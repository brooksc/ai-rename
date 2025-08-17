"""Tests for LLM client functionality."""

import json
from unittest.mock import Mock, patch

import pytest

from src.core.exceptions import LLMError, RateLimitError
from src.core.llm import LLMClient, RenameSuggestion


class TestRenameSuggestion:
    """Tests for RenameSuggestion dataclass."""

    def test_rename_suggestion_creation(self):
        """Test creating a RenameSuggestion instance."""
        suggestion = RenameSuggestion(
            suggested_path="Person/John_Doe/Medical/2024-01-15_checkup.pdf",
            filename="2024-01-15_checkup.pdf",
            reasoning="Medical checkup document for John Doe"
        )

        assert suggestion.suggested_path == "Person/John_Doe/Medical/2024-01-15_checkup.pdf"
        assert suggestion.filename == "2024-01-15_checkup.pdf"
        assert suggestion.reasoning == "Medical checkup document for John Doe"


class TestLLMClientInitialization:
    """Tests for LLMClient initialization."""

    def test_llm_client_creation_with_defaults(self):
        """Test creating LLMClient with default parameters."""
        with patch('src.core.llm.genai.Client') as mock_client:
            client = LLMClient(api_key="test-key")

            assert client.model == "gemini-2.0-flash"
            assert client.timeout == 120
            assert client.temperature == 1.0
            assert client.api_key == "test-key"
            mock_client.assert_called_once_with(api_key="test-key")

    def test_llm_client_creation_with_custom_params(self):
        """Test creating LLMClient with custom parameters."""
        with patch('src.core.llm.genai.Client'):
            client = LLMClient(
                model="gemini-1.5-pro",
                timeout=60,
                temperature=0.5,
                api_key="custom-key",
                retry_attempts=5,
                retry_delay=2.0
            )

            assert client.model == "gemini-1.5-pro"
            assert client.timeout == 60
            assert client.temperature == 0.5
            assert client.api_key == "custom-key"
            assert client.retry_attempts == 5
            assert client.retry_delay == 2.0

    def test_llm_client_invalid_temperature(self):
        """Test LLMClient with invalid temperature."""
        with pytest.raises(ValueError, match="Temperature must be between 0.0 and 1.0"):
            LLMClient(temperature=1.5, api_key="test-key")

    def test_llm_client_invalid_timeout(self):
        """Test LLMClient with invalid timeout."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            LLMClient(timeout=-1, api_key="test-key")

    def test_llm_client_invalid_retry_attempts(self):
        """Test LLMClient with invalid retry attempts."""
        with pytest.raises(ValueError, match="Retry attempts must be non-negative"):
            LLMClient(retry_attempts=-1, api_key="test-key")

    def test_llm_client_missing_api_key(self):
        """Test LLMClient without API key in env or params."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY not found"):
                LLMClient()

    def test_llm_client_api_key_from_env(self):
        """Test LLMClient getting API key from environment."""
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'env-key'}):
            with patch('src.core.llm.genai.Client') as mock_client:
                client = LLMClient()

                assert client.api_key == "env-key"
                mock_client.assert_called_once_with(api_key="env-key")


class TestLLMClientConnection:
    """Tests for LLM client connection testing."""

    @patch('src.core.llm.genai.GenerativeModel')
    def test_test_connection_success(self, mock_model_class):
        """Test successful connection test."""
        # Mock the model and response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Hello! I can help you rename files."
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        with patch('src.core.llm.genai.Client'):
            client = LLMClient(api_key="test-key")
            result = client.test_connection()

            assert result is True
            mock_model.generate_content.assert_called_once()

    @patch('src.core.llm.genai.GenerativeModel')
    def test_test_connection_empty_response(self, mock_model_class):
        """Test connection test with empty response."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = ""
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        with patch('src.core.llm.genai.Client'):
            client = LLMClient(api_key="test-key")
            result = client.test_connection()

            assert result is False

    @patch('src.core.llm.genai.GenerativeModel')
    def test_test_connection_api_error(self, mock_model_class):
        """Test connection test with API error."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model

        with patch('src.core.llm.genai.Client'):
            client = LLMClient(api_key="test-key")

            with pytest.raises(LLMError, match="Failed to connect to Gemini"):
                client.test_connection()


class TestLLMClientRequestHandling:
    """Tests for LLM request handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_patcher = patch('src.core.llm.genai.Client')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = Mock()
        self.mock_client_class.return_value = self.mock_client

    def teardown_method(self):
        """Clean up test fixtures."""
        self.client_patcher.stop()

    def test_make_request_success(self, sample_txt_file):
        """Test successful LLM request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = '{"suggested_path": "test/path.pdf", "filename": "test.pdf", "reasoning": "test"}'
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")
        result = client._make_request("test prompt", sample_txt_file)

        assert json.loads(result) == {
            "suggested_path": "test/path.pdf",
            "filename": "test.pdf",
            "reasoning": "test"
        }

    def test_make_request_pdf_file(self, sample_pdf_file):
        """Test LLM request with PDF file."""
        mock_response = Mock()
        mock_response.text = '{"suggested_path": "test/path.pdf", "filename": "test.pdf", "reasoning": "test"}'
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")
        result = client._make_request("test prompt", sample_pdf_file)

        # Should call with PDF part
        self.mock_client.models.generate_content.assert_called_once()
        args = self.mock_client.models.generate_content.call_args
        assert args[1]['contents'][0] is not None  # PDF part
        assert "test prompt" in args[1]['contents'][1]  # Prompt

    def test_make_request_api_key_error(self, sample_txt_file):
        """Test LLM request with API key error."""
        self.mock_client.models.generate_content.side_effect = Exception("api key error")

        client = LLMClient(api_key="test-key")

        with pytest.raises(LLMError, match="Missing or invalid Google API key"):
            client._make_request("test prompt", sample_txt_file)

    def test_make_request_rate_limit_error(self, sample_txt_file):
        """Test LLM request with rate limit error."""
        self.mock_client.models.generate_content.side_effect = Exception("rate limit exceeded")

        client = LLMClient(api_key="test-key")

        with pytest.raises(RateLimitError, match="rate limit exceeded"):
            client._make_request("test prompt", sample_txt_file)

    def test_make_request_invalid_json_response(self, sample_txt_file):
        """Test LLM request with invalid JSON response."""
        mock_response = Mock()
        mock_response.text = "invalid json response"
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")

        with pytest.raises(LLMError, match="No JSON object found in response"):
            client._make_request("test prompt", sample_txt_file)

    def test_make_request_with_capture_dir(self, sample_txt_file, temp_dir):
        """Test LLM request with capture directory."""
        mock_response = Mock()
        mock_response.text = '{"suggested_path": "test/path.pdf", "filename": "test.pdf", "reasoning": "test"}'
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key", capture_dir=temp_dir)
        client._make_request("test prompt", sample_txt_file)

        # Check that prompt and response files were created
        prompt_file = temp_dir / "request.prompt"
        response_file = temp_dir / "response.json"

        assert prompt_file.exists()
        assert response_file.exists()
        assert "test prompt" in prompt_file.read_text()


class TestLLMClientResponseValidation:
    """Tests for LLM response validation."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.core.llm.genai.Client'):
            self.client = LLMClient(api_key="test-key")

    def test_validate_response_success(self, sample_txt_file):
        """Test successful response validation."""
        response = {
            "suggested_path": "Person/John/Medical/2024-01-15_report.txt",
            "filename": "2024-01-15_report.txt",
            "reasoning": "This is a medical report"
        }

        validated = self.client._validate_response(response, sample_txt_file)

        assert validated == response

    def test_validate_response_missing_field(self, sample_txt_file):
        """Test response validation with missing field."""
        response = {
            "suggested_path": "test/path.txt",
            "reasoning": "test reasoning"
            # Missing "filename"
        }

        with pytest.raises(LLMError, match="Missing required field: filename"):
            self.client._validate_response(response, sample_txt_file)

    def test_validate_response_wrong_extension(self, sample_txt_file):
        """Test response validation with wrong file extension."""
        response = {
            "suggested_path": "test/path.pdf",  # Wrong extension
            "filename": "test.pdf",  # Wrong extension
            "reasoning": "test reasoning"
        }

        with pytest.raises(LLMError, match="Filename must keep original extension"):
            self.client._validate_response(response, sample_txt_file)

    def test_validate_response_invalid_types(self, sample_txt_file):
        """Test response validation with invalid data types."""
        response = {
            "suggested_path": 123,  # Should be string
            "filename": "test.txt",
            "reasoning": "test reasoning"
        }

        with pytest.raises(LLMError, match="suggested_path must be a string"):
            self.client._validate_response(response, sample_txt_file)

    def test_validate_response_not_dict(self, sample_txt_file):
        """Test response validation with non-dictionary input."""
        response = "not a dictionary"

        with pytest.raises(LLMError, match="Response must be a dictionary"):
            self.client._validate_response(response, sample_txt_file)


class TestLLMClientSuggestionGeneration:
    """Tests for rename suggestion generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_patcher = patch('src.core.llm.genai.Client')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = Mock()
        self.mock_client_class.return_value = self.mock_client

    def teardown_method(self):
        """Clean up test fixtures."""
        self.client_patcher.stop()

    def test_generate_rename_suggestion_success(self, sample_txt_file):
        """Test successful rename suggestion generation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Person/ACME/Financial/2024-01-15_invoice.txt",
            "filename": "2024-01-15_invoice.txt",
            "reasoning": "This is an invoice from ACME Corp"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")
        suggestion = client.generate_rename_suggestion(
            content="Invoice from ACME Corp",
            file_path=sample_txt_file,
            taxonomy_rules="Test taxonomy"
        )

        assert isinstance(suggestion, RenameSuggestion)
        assert suggestion.suggested_path == "Person/ACME/Financial/2024-01-15_invoice.txt"
        assert suggestion.filename == "2024-01-15_invoice.txt"
        assert "ACME Corp" in suggestion.reasoning

    def test_generate_rename_suggestion_with_override(self, sample_txt_file):
        """Test rename suggestion generation with override instructions."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Custom/Path/2024-01-15_custom.txt",
            "filename": "2024-01-15_custom.txt",
            "reasoning": "Custom override applied"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")
        suggestion = client.generate_rename_suggestion(
            content="Test content",
            file_path=sample_txt_file,
            taxonomy_rules="Test taxonomy",
            override_instructions="Use custom path"
        )

        assert "Custom/Path" in suggestion.suggested_path

    def test_generate_rename_suggestion_invalid_json(self, sample_txt_file):
        """Test rename suggestion with invalid JSON response."""
        mock_response = Mock()
        mock_response.text = "invalid json"
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")

        with pytest.raises(LLMError, match="Invalid JSON response"):
            client.generate_rename_suggestion(
                content="Test content",
                file_path=sample_txt_file
            )

    def test_generate_rename_suggestion_validation_failure(self, sample_txt_file):
        """Test rename suggestion with validation failure."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "test/path.txt",
            "filename": "test.pdf",  # Wrong extension
            "reasoning": "test"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        client = LLMClient(api_key="test-key")

        with pytest.raises(LLMError, match="Invalid response format"):
            client.generate_rename_suggestion(
                content="Test content",
                file_path=sample_txt_file
            )
