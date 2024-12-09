import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import litellm
from ..utils.logging import LLMError
from ..core.database import Database

class LLMProvider:
    def __init__(self, config: Dict[str, Any], db: Database):
        """Initialize LLM provider with configuration and database connection."""
        self.config = config
        self.db = db
        self.setup_provider()

    def setup_provider(self) -> None:
        """Configure litellm with API keys and settings."""
        try:
            litellm.api_key = self.config['litellm_config']['api_key']
            if org_id := self.config['litellm_config'].get('organization'):
                litellm.organization = org_id

            # Set up anthropic key if available
            if anthropic_key := self.config['litellm_config'].get('anthropic_api_key'):
                litellm.anthropic_api_key = anthropic_key

        except KeyError as e:
            raise LLMError(f"Missing required LLM configuration: {e}")

    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate a unique cache key for the request."""
        data = f"{prompt}:{model}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Retrieve cached response if available and not expired."""
        if not self.config['cache']['enabled']:
            return None

        try:
            cur = self.db.conn.execute("""
                SELECT response, created_at
                FROM llm_cache
                WHERE request_hash = ?
            """, (cache_key,))
            result = cur.fetchone()

            if not result:
                return None

            # Check if cache is expired
            cache_age = datetime.utcnow() - datetime.fromisoformat(result['created_at'])
            if cache_age.total_seconds() > self.config['cache']['max_age']:
                return None

            return result['response']
        except Exception as e:
            logging.warning(f"Failed to retrieve from cache: {e}")
            return None

    def _cache_response(self, cache_key: str, response: str, tokens_used: int, model: str) -> None:
        """Cache the LLM response."""
        if not self.config['cache']['enabled']:
            return

        try:
            with self.db.conn:
                self.db.conn.execute("""
                    INSERT INTO llm_cache (request_hash, response, tokens_used, model_used, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (cache_key, response, tokens_used, model, datetime.utcnow()))
        except Exception as e:
            logging.warning(f"Failed to cache response: {e}")

    def _make_llm_call(self, prompt: str, model: str, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Make the actual API call to the LLM provider."""
        try:
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or self.config['max_chunk_size']
            )
            
            return {
                'content': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': model
            }
        except Exception as e:
            if self.config.get('fallback_provider') and self.config.get('fallback_model'):
                logging.warning(f"Primary LLM call failed, trying fallback: {e}")
                return self._make_llm_call(
                    prompt,
                    f"{self.config['fallback_provider']}/{self.config['fallback_model']}",
                    max_tokens
                )
            raise LLMError(f"LLM API call failed: {e}")

    def process_text(self, text: str, operation: str, doc_id: Optional[int] = None,
                    max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Process text with LLM, using cache if available."""
        model = f"{self.config['provider']}/{self.config['model']}"
        prompt = self._build_prompt(text, operation)
        cache_key = self._get_cache_key(prompt, model)

        # Try to get from cache
        if cached := self._get_cached_response(cache_key):
            return {'content': cached, 'cached': True}

        # Make LLM call
        result = self._make_llm_call(prompt, model, max_tokens)
        
        # Cache the response
        self._cache_response(cache_key, result['content'], result['tokens_used'], result['model'])

        # Record processing if document ID is provided
        if doc_id:
            try:
                with self.db.conn:
                    self.db.conn.execute("""
                        INSERT INTO llm_processing (
                            document_id, operation, model_used, result,
                            tokens_used, processed_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (doc_id, operation, result['model'], result['content'],
                         result['tokens_used'], datetime.utcnow()))
            except Exception as e:
                logging.error(f"Failed to record LLM processing: {e}")

        return result

    def _build_prompt(self, text: str, operation: str) -> str:
        """Build appropriate prompt based on operation type."""
        prompts = {
            'summarize': f"Please provide a concise summary of the following text in {self.config['summary_length']} words or less:\n\n{text}",
            'categorize': f"Please suggest up to 5 relevant categories for the following text, separated by commas:\n\n{text}",
            'tag': f"Please suggest up to 5 relevant tags for the following text, separated by commas:\n\n{text}",
            'extract_metadata': f"Please extract key metadata from the following text, including title, author, date, and any other relevant information. Format as JSON:\n\n{text}"
        }
        
        if operation not in prompts:
            raise LLMError(f"Unknown operation: {operation}")
            
        return prompts[operation]

    def get_token_usage(self, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict[str, int]:
        """Get token usage statistics for the specified time period."""
        try:
            query = """
                SELECT model_used, SUM(tokens_used) as total_tokens
                FROM llm_processing
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND processed_at >= ?"
                params.append(start_date)
            if end_date:
                query += " AND processed_at <= ?"
                params.append(end_date)

            query += " GROUP BY model_used"

            cur = self.db.conn.execute(query, params)
            return {row['model_used']: row['total_tokens'] for row in cur}
        except Exception as e:
            logging.error(f"Failed to get token usage stats: {e}")
            return {}
