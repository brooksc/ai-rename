"""LLM client for generating rename suggestions."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

import google.generativeai as genai
from loguru import logger

from src.core.exceptions import LLMError, RateLimitError


@dataclass
class RenameSuggestion:
    """Rename suggestion from LLM."""
    suggested_path: str
    filename: str
    reasoning: str

class LLMClient:
    """Client for LLM API."""

    def __init__(self,
                 model: str = "gemini-2.0-flash",
                 timeout: int = 120,
                 temperature: float = 1.0,

                 api_key: str | None = None,
                 capture_dir: Path | None = None,
                 retry_attempts: int = 3,
                 retry_delay: float = 1.0):
        """Initialize LLM client.

        Args:
            model: Gemini model name (default: gemini-2.0-flash)
            timeout: Request timeout in seconds
            temperature: Sampling temperature (0.0-1.0)
            api_key: Gemini API key (required)
            capture_dir: Optional directory to capture prompts/responses
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds

        Raises:
            ValueError: If invalid configuration
        """
        if not (0.0 <= temperature <= 1.0):
            raise ValueError("Temperature must be between 0.0 and 1.0")
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        if retry_attempts < 0:
            raise ValueError("Retry attempts must be non-negative")
        if retry_delay < 0:
            raise ValueError("Retry delay must be non-negative")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature

        self.api_key = api_key
        self.capture_dir = capture_dir
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Set up Gemini client
        logger.debug("Setting up Gemini client")
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.api_key = api_key

    def test_connection(self) -> bool:
        """Test the connection to the Gemini API."""
        try:
            logger.debug(f"Testing Gemini connection with model {self.model}")
            # Use a simple test prompt
            test_prompt = "Hello, can you help me rename some files?"

            logger.debug("Sending test prompt to Gemini")
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(test_prompt)

            if response.text:
                logger.debug("Successfully received response from Gemini")
                return True
            else:
                logger.error("Empty response from Gemini")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Gemini: {e}")
            raise LLMError("Failed to connect to Gemini. Please ensure:\n1. Your API key is valid\n2. The model is available\n3. You have access to the model") from e

    def _make_request(self, prompt: str, file_path: Path | None = None) -> str:
        """Make request to LLM API.

        Args:
            prompt: Prompt to send

        Returns:
            Response from LLM

        Raises:
            LLMError: If request fails
            RateLimitError: If rate limit exceeded
        """
        try:
            # Save prompt if capture enabled
            if self.capture_dir:
                prompt_file = self.capture_dir / "request.prompt"
                with open(prompt_file, "w") as f:
                    f.write(prompt)

            # Add explicit JSON instruction with format reminder
            prompt_with_json = f"""{prompt}

IMPORTANT: Your response must be a valid JSON object with EXACTLY these fields:
{{{{
    "suggested_path": "full/path/to/file/YYYY-MM-DD_descriptive_name{file_path.suffix}",
    "filename": "YYYY-MM-DD_descriptive_name{file_path.suffix}",
    "reasoning": "Explanation of why this path and name were chosen"
}}}}

IMPORTANT: You MUST keep the original file extension {file_path.suffix} in both the suggested_path and filename.
Do not include any other fields or text outside this JSON object."""

            # Log Gemini configuration parameters
            logger.debug("Making Gemini request with configuration:")
            logger.debug(f"  Model: {self.model}")
            logger.debug(f"  Temperature: {self.temperature}")
            logger.debug(f"  Timeout: {self.timeout}")
            logger.debug(f"  API Key Set: {bool(self.api_key)}")
            logger.debug(f"  Prompt Length: {len(prompt_with_json)} characters")

            # Print full prompt in debug mode
            logger.debug("Full prompt:")
            logger.debug("=" * 80)
            logger.debug(prompt_with_json)
            logger.debug("=" * 80)

            try:
                logger.debug("Sending request to LLM...")
                if file_path and file_path.suffix.lower() == '.pdf':
                    logger.debug("Processing PDF file directly with Gemini")
                    try:
                        # Upload PDF file and create content
                        model = genai.GenerativeModel(self.model)
                        pdf_file = genai.upload_file(file_path, mime_type='application/pdf')
                        response = model.generate_content([pdf_file, prompt_with_json])
                    except Exception as e:
                        logger.error(f"Failed to process PDF file: {e}")
                        raise LLMError(f"Failed to process PDF file: {e}") from e
                else:
                    # Regular text processing
                    model = genai.GenerativeModel(self.model)
                    response = model.generate_content(prompt_with_json)
                logger.debug("Successfully received response from Gemini")
                # Gemini sometimes includes newlines in the JSON, remove them
                content = response.text.strip().replace('\n', '')

                # Print full response in debug mode
                logger.debug("Full response:")
                logger.debug("=" * 80)
                logger.debug(content)
                logger.debug("=" * 80)

            except Exception as e:
                error_msg = str(e).lower()
                # Handle Gemini-specific errors
                if "api key" in error_msg:
                    logger.error("Missing or invalid Google API key")
                    logger.error("Please set the GOOGLE_API_KEY environment variable")
                    raise LLMError("Missing or invalid Google API key. Please set GOOGLE_API_KEY environment variable.") from e
                elif "model not found" in error_msg:
                    logger.error(f"Model '{self.model}' not found or not available")
                    logger.error("Please check the model name and your API access")
                    raise LLMError(f"Model '{self.model}' not found or not available") from e
                elif "rate limit" in error_msg:
                    logger.error("Gemini API rate limit exceeded")
                    raise RateLimitError("Gemini API rate limit exceeded") from e
                elif "unauthorized" in error_msg:
                    logger.error("Authentication failed - please check your API key")
                    raise LLMError("Authentication failed - please check your API key") from e
                else:
                    logger.error(f"Unexpected Gemini API error: {error_msg}")
                    raise LLMError(f"Gemini API request failed: {error_msg}") from e

            # Try to find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise LLMError("No JSON object found in response")

            # Extract just the JSON part
            json_str = content[json_start:json_end]

            # Validate it's parseable
            try:
                parsed_json = json.loads(json_str)
                # Try to fix common issues with the response
                if 'suggested_path' not in parsed_json and 'file_name' in parsed_json:
                    # LLM used wrong field name
                    logger.warning("LLM used 'file_name' instead of 'suggested_path', attempting to fix")
                    parsed_json['suggested_path'] = parsed_json['file_name']
                    parsed_json['filename'] = parsed_json['file_name']
                    if 'reasoning' not in parsed_json:
                        parsed_json['reasoning'] = "Generated from file analysis"
                    json_str = json.dumps(parsed_json)
            except json.JSONDecodeError as e:
                raise LLMError(f"Invalid JSON in response: {json_str}") from e

            # Save raw response if capture enabled
            if self.capture_dir:
                response_file = self.capture_dir / "response.json"
                with open(response_file, "w") as f:
                    # Save only the parsed JSON response
                    json.dump(parsed_json, f, indent=2)

            return json_str

        except Exception as e:
            # Handle rate limit errors
            if "rate limit" in str(e).lower():
                raise RateLimitError(f"Rate limit exceeded: {e}") from e
            if isinstance(e, LLMError):
                raise
            raise LLMError(f"LLM request failed: {e}") from e

    def _validate_response(self, response: dict, original_path: Path) -> dict:
        """Validate the LLM response format."""
        try:
            if not isinstance(response, dict):
                raise ValueError("Response must be a dictionary")

            required_fields = ['suggested_path', 'filename', 'reasoning']
            for field in required_fields:
                if field not in response:
                    raise ValueError(f"Missing required field: {field}")

            if not isinstance(response['suggested_path'], str):
                raise ValueError("suggested_path must be a string")
            if not isinstance(response['filename'], str):
                raise ValueError("filename must be a string")
            if not isinstance(response['reasoning'], str):
                raise ValueError("reasoning must be a string")

            # Additional validation
            if not response['filename'].endswith(original_path.suffix):
                raise ValueError(f"Filename must keep original extension: {original_path.suffix}")

            return response
        except Exception as e:
            raise LLMError(f"Invalid response format: {e}") from e

    def generate_rename_suggestion(self,
                             content: str,
                             file_path: Path,
                             taxonomy_rules: str | None = None,
                             capture_dir: Path | None = None,
                             override_instructions: str | None = None) -> RenameSuggestion:
        """Generate rename suggestion for file.

        Args:
            content: File content
            file_path: Path to file
            taxonomy_rules: Optional taxonomy rules
            capture_dir: Optional directory to capture prompts/responses for this request

        Returns:
            RenameSuggestion with new path and reasoning

        Raises:
            LLMError: If request fails
            RateLimitError: If rate limit exceeded
        """
        # Save current capture dir
        original_capture_dir = self.capture_dir
        try:
            # Set capture dir for this request if specified
            if capture_dir:
                self.capture_dir = capture_dir
            logger.debug("Building prompt for rename suggestion")
            prompt = self._build_prompt(file_path, content, taxonomy_rules, override_instructions)
            logger.debug("Making request to LLM")
            response = self._make_request(prompt, file_path)
            logger.debug(f"Got raw response: {response}")
            try:
                response_json = json.loads(response)
                logger.debug(f"Parsed response JSON: {response_json}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                raise LLMError(f"Invalid JSON response: {e}") from e

            try:
                validated = self._validate_response(response_json, file_path)
                logger.debug(f"Validated response: {validated}")
            except Exception as e:
                logger.error(f"Response validation failed: {e}")
                logger.error(f"Response JSON: {response_json}")
                raise LLMError(f"Invalid response format: {e}") from e
            return RenameSuggestion(
                suggested_path=validated["suggested_path"],
                filename=validated["filename"],
                reasoning=validated["reasoning"]
            )
        except Exception as e:
            logger.error(f"Failed to generate rename suggestion: {e}")
            if isinstance(e, LLMError | RateLimitError):
                raise
            raise LLMError(f"Failed to generate rename suggestion: {e}") from e
        finally:
            # Restore original capture dir
            self.capture_dir = original_capture_dir

    def _build_prompt(self,
                     file_path: Path,
                     file_content: str,
                     taxonomy_rules: str | None = None,
                     override_instructions: str | None = None) -> str:
        """Build prompt for rename suggestion.

        Args:
            file_path: Path to file
            file_content: File content
            taxonomy_rules: Optional taxonomy rules

        Returns:
            str: Prompt text
        """
        # Log input details
        logger.debug("Building LLM prompt:")
        logger.debug(f"  File: {file_path}")
        logger.debug(f"  Content Length: {len(file_content)} characters")
        if taxonomy_rules:
            logger.debug(f"  Taxonomy Rules Length: {len(str(taxonomy_rules))} characters")

        prompt = f"""
You are an AI document organization assistant. Your task is to analyze the content of a document and suggest a file path and filename based on a user-provided taxonomy and any override instructions.

You will receive these inputs:

1. **Original Filename:** The current name of the file. This may contain relevant information about the document's content or purpose, but it might also be generic or misleading.
2. **Taxonomy:** A set of rules and examples defining how to categorize and name files. This will be provided within `<taxonomy>` tags.
3. **Document Content:** The text content of the document to be analyzed. This will be provided within `<document>` tags.
4. **Override Instructions:** (Optional) User-provided instructions that take precedence over taxonomy rules. These will be provided within `<override>` tags.

Analyze the Document Content and determine the best file path and filename. If override instructions are provided, they take precedence over the taxonomy rules, though you should still use the taxonomy as a secondary guide.

IMPORTANT: Your response must be a valid JSON object with EXACTLY these fields:
{{{{
    "suggested_path": "full/path/to/file/YYYY-MM-DD_descriptive_name.ext",
    "filename": "YYYY-MM-DD_descriptive_name.ext",
    "reasoning": "Explanation of why this path and name were chosen"
}}}}

Constraints:

*   Response MUST be a valid JSON object. No other text.
*   Use *only* the information in the taxonomy. Do not invent rules.
*   If the document doesn't fit, use `Other/{{date}}_{{name}}`.
*   Prioritize dates *within* the document (invoice, service). If no date is found, use the creation date.
    *   If there are multiple dates, use the earliest date.
    *   If there are multiple dates, and one is explicitly a service end date, then use that date instead.
*   Filenames: descriptive, use underscores, avoid non-standard abbreviations.

Example (Illustrative):

<taxonomy>
## Example
### Medical
Person/{{Name}}/Medical/{{date}}_{{description}}.pdf
</taxonomy>

<example>
Patient: John Doe
Date: 2024-03-15
</example>

Example Output:
{{
    "suggested_path": "Person/John Doe/Medical/2024-03-15_patient_record.pdf",
    "filename": "2024-03-15_patient_record.pdf",
    "reasoning": "Medical category. Date from document."
}}

Now, here is the original filename, taxonomy, document content, and any override instructions:

<original_filename>
{file_path.name}
</original_filename>

<taxonomy>
{taxonomy_rules}
</taxonomy>

<document>
{file_content[:2000]}
</document>

{f'<override>\n{override_instructions}\n</override>' if override_instructions else ''}

Remember: Your response must be ONLY a JSON object with exactly the fields shown in the example above.
"""

        return prompt
