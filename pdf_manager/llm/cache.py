import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from ..core.database import Database
from ..utils.logging import LLMError

class LLMCache:
    def __init__(self, db: Database, config: Dict[str, Any]):
        """Initialize LLM cache with database connection and configuration."""
        self.db = db
        self.config = config
        self.enabled = config['cache']['enabled']
        self.max_age = config['cache']['max_age']

    def get(self, request_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response if available and not expired.
        
        Args:
            request_hash: The hash of the request to look up
            
        Returns:
            Optional[Dict]: The cached response or None if not found/expired
        """
        if not self.enabled:
            return None

        try:
            with self.db.conn:
                cur = self.db.conn.execute("""
                    SELECT response, tokens_used, model_used, created_at
                    FROM llm_cache
                    WHERE request_hash = ?
                """, (request_hash,))
                result = cur.fetchone()

                if not result:
                    return None

                # Check if cache is expired
                created_at = datetime.fromisoformat(result['created_at'])
                if (datetime.utcnow() - created_at).total_seconds() > self.max_age:
                    self._remove_expired()
                    return None

                return {
                    'response': result['response'],
                    'tokens_used': result['tokens_used'],
                    'model_used': result['model_used'],
                    'cached': True
                }

        except Exception as e:
            logging.warning(f"Failed to retrieve from cache: {e}")
            return None

    def set(self, request_hash: str, response: str, tokens_used: int,
            model_used: str) -> None:
        """
        Cache an LLM response.
        
        Args:
            request_hash: Hash of the request
            response: The LLM response to cache
            tokens_used: Number of tokens used
            model_used: Name of the model used
        """
        if not self.enabled:
            return

        try:
            with self.db.conn:
                self.db.conn.execute("""
                    INSERT OR REPLACE INTO llm_cache (
                        request_hash, response, tokens_used,
                        model_used, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (request_hash, response, tokens_used,
                     model_used, datetime.utcnow()))

        except Exception as e:
            logging.warning(f"Failed to cache response: {e}")

    def _remove_expired(self) -> None:
        """Remove expired cache entries."""
        try:
            expiry = datetime.utcnow() - timedelta(seconds=self.max_age)
            with self.db.conn:
                self.db.conn.execute("""
                    DELETE FROM llm_cache
                    WHERE created_at < ?
                """, (expiry,))
        except Exception as e:
            logging.warning(f"Failed to remove expired cache entries: {e}")

    def clear(self) -> None:
        """Clear all cached responses."""
        try:
            with self.db.conn:
                self.db.conn.execute("DELETE FROM llm_cache")
        except Exception as e:
            logging.error(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            with self.db.conn:
                # Get total entries and size
                cur = self.db.conn.execute("""
                    SELECT COUNT(*) as count,
                           SUM(LENGTH(response)) as total_size,
                           SUM(tokens_used) as total_tokens
                    FROM llm_cache
                """)
                stats = dict(cur.fetchone())

                # Get model distribution
                cur = self.db.conn.execute("""
                    SELECT model_used, COUNT(*) as count
                    FROM llm_cache
                    GROUP BY model_used
                """)
                stats['models'] = {row['model_used']: row['count']
                                 for row in cur.fetchall()}

                # Calculate age distribution
                cur = self.db.conn.execute("""
                    SELECT
                        COUNT(*) as count,
                        CASE
                            WHEN (julianday('now') - julianday(created_at)) * 86400 < 3600 THEN '< 1 hour'
                            WHEN (julianday('now') - julianday(created_at)) * 86400 < 86400 THEN '< 1 day'
                            ELSE '> 1 day'
                        END as age_group
                    FROM llm_cache
                    GROUP BY age_group
                """)
                stats['age_distribution'] = {row['age_group']: row['count']
                                           for row in cur.fetchall()}

                return stats

        except Exception as e:
            logging.error(f"Failed to get cache stats: {e}")
            return {}
