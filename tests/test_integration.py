"""Integration tests for ai-rename components."""

import json
from unittest.mock import Mock, patch

import pytest

from src.core.llm import LLMClient, RenameSuggestion
from src.core.taxonomy import TaxonomyParser
from src.rename import rename_files
from src.ui.interface import UserInterface


class TestLLMTaxonomyIntegration:
    """Integration tests for LLM and taxonomy system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_patcher = patch('src.core.llm.genai.Client')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = Mock()
        self.mock_client_class.return_value = self.mock_client

    def teardown_method(self):
        """Clean up test fixtures."""
        self.client_patcher.stop()

    def test_llm_with_taxonomy_rules(self, sample_txt_file, sample_taxonomy_parser):
        """Test LLM integration with taxonomy rules."""
        # Mock successful LLM response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Person/ACME_Corp/Financial/2024-01-15_invoice.txt",
            "filename": "2024-01-15_invoice.txt",
            "reasoning": "Invoice from ACME Corp, categorized under Financial per taxonomy rules"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        # Create LLM client
        llm_client = LLMClient(api_key="test-key")

        # Test suggestion generation with taxonomy
        suggestion = llm_client.generate_rename_suggestion(
            content="Invoice from ACME Corp\nDate: 2024-01-15\nAmount: $1,250.00",
            file_path=sample_txt_file,
            taxonomy_rules=sample_taxonomy_parser.content
        )

        assert isinstance(suggestion, RenameSuggestion)
        assert "Financial" in suggestion.suggested_path
        assert "2024-01-15" in suggestion.filename
        assert "taxonomy" in suggestion.reasoning.lower()

    def test_prompt_includes_taxonomy_content(self, sample_txt_file, sample_taxonomy_parser):
        """Test that LLM prompt includes taxonomy content."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "test/path.txt",
            "filename": "test.txt",
            "reasoning": "test"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        llm_client = LLMClient(api_key="test-key")

        llm_client.generate_rename_suggestion(
            content="Test content",
            file_path=sample_txt_file,
            taxonomy_rules=sample_taxonomy_parser.content
        )

        # Verify that taxonomy content was included in the prompt
        call_args = self.mock_client.models.generate_content.call_args
        prompt = call_args[1]['contents']
        assert "Medical" in str(prompt)
        assert "Financial" in str(prompt)
        assert sample_taxonomy_parser.content in str(prompt)

    def test_override_instructions_integration(self, sample_txt_file):
        """Test LLM integration with override instructions."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Custom/Override/2024-01-15_custom.txt",
            "filename": "2024-01-15_custom.txt",
            "reasoning": "Applied custom override instructions"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        llm_client = LLMClient(api_key="test-key")

        suggestion = llm_client.generate_rename_suggestion(
            content="Test content",
            file_path=sample_txt_file,
            taxonomy_rules="Test taxonomy",
            override_instructions="Place in Custom/Override directory"
        )

        assert "Custom/Override" in suggestion.suggested_path
        assert "override" in suggestion.reasoning.lower()

    def test_pdf_processing_integration(self, sample_pdf_file):
        """Test PDF file processing integration."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Documents/2024-01-15_scanned_document.pdf",
            "filename": "2024-01-15_scanned_document.pdf",
            "reasoning": "Processed PDF document content"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        llm_client = LLMClient(api_key="test-key")

        suggestion = llm_client.generate_rename_suggestion(
            content="<PDF file will be processed directly by Gemini>",
            file_path=sample_pdf_file
        )

        assert suggestion.filename.endswith(".pdf")
        assert "2024-01-15" in suggestion.filename


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client_patcher = patch('src.core.llm.genai.Client')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = Mock()
        self.mock_client_class.return_value = self.mock_client

    def teardown_method(self):
        """Clean up test fixtures."""
        self.client_patcher.stop()

    def test_complete_rename_workflow(self, sample_txt_file, sample_config, sample_taxonomy_file):
        """Test complete rename workflow from start to finish."""
        # Mock LLM response
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Person/ACME/Financial/2024-01-15_invoice.txt",
            "filename": "2024-01-15_invoice.txt",
            "reasoning": "Invoice from ACME Corp per taxonomy rules"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        # Create LLM client
        llm_client = LLMClient(api_key="test-key")

        # Mock UI to auto-accept
        with patch('src.rename.UserInterface') as mock_ui_class:
            mock_ui = Mock()
            mock_ui.handle_rename.return_value = True
            mock_ui_class.return_value = mock_ui

            # Test complete workflow
            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=llm_client,
                taxonomy_file=sample_taxonomy_file
            )

            # Verify workflow executed
            mock_ui.handle_rename.assert_called_once()
            proposal = mock_ui.handle_rename.call_args[0][0]
            assert "ACME" in proposal.new_path.name
            assert "Financial" in str(proposal.new_path)

    def test_batch_processing_workflow(self, temp_dir, sample_config):
        """Test batch processing multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            file_path = temp_dir / f"test_{i}.txt"
            file_path.write_text(f"Test content {i}")
            files.append(file_path)

        # Mock LLM responses
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "Batch/2024-01-15_test.txt",
            "filename": "2024-01-15_test.txt",
            "reasoning": "Batch processed file"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        llm_client = LLMClient(api_key="test-key")

        with patch('src.rename.UserInterface') as mock_ui_class:
            mock_ui = Mock()
            mock_ui.handle_rename.return_value = True
            mock_ui.total_files = 3
            mock_ui_class.return_value = mock_ui

            rename_files(
                paths=files,
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=llm_client
            )

            # Should process all files
            assert mock_ui.handle_rename.call_count == 3

    def test_error_handling_workflow(self, sample_txt_file, sample_config):
        """Test error handling in complete workflow."""
        # Mock LLM failure
        self.mock_client.models.generate_content.side_effect = Exception("API Error")

        llm_client = LLMClient(api_key="test-key")

        with patch('src.rename.logger') as mock_logger:
            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=llm_client
            )

            # Should log error
            mock_logger.error.assert_called()

    def test_dry_run_workflow(self, sample_txt_file, sample_config):
        """Test dry run workflow."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "suggested_path": "DryRun/2024-01-15_test.txt",
            "filename": "2024-01-15_test.txt",
            "reasoning": "Dry run test"
        })
        self.mock_client.models.generate_content.return_value = mock_response

        llm_client = LLMClient(api_key="test-key")

        with patch('src.rename.logger') as mock_logger:
            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=True,
                config_path=sample_config,
                llm_client=llm_client
            )

            # Should log what would be done
            mock_logger.info.assert_called()


class TestUIIntegration:
    """Integration tests for UI components."""

    def test_ui_file_rename_proposal(self, sample_txt_file, temp_dir):
        """Test UI integration with file rename proposals."""
        from src.ui.interface import FileRenameProposal

        # Create a rename proposal
        proposal = FileRenameProposal(
            current_path=sample_txt_file,
            new_path=temp_dir / "renamed.txt",
            content_preview="Test content preview",
            reasoning="Test reasoning for rename"
        )

        # Mock UI interactions
        ui = UserInterface(autoaccept=False)

        with patch.object(ui, '_get_user_input', return_value='y'):
            with patch('shutil.move') as mock_move:
                def mock_rename_func(src, dst):
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    mock_move(src, dst)

                result = ui.handle_rename(proposal, None, mock_rename_func)

                assert result is True
                mock_move.assert_called_once()

    def test_ui_autoaccept_mode(self, sample_txt_file, temp_dir):
        """Test UI in autoaccept mode."""
        from src.ui.interface import FileRenameProposal

        proposal = FileRenameProposal(
            current_path=sample_txt_file,
            new_path=temp_dir / "autoaccept.txt",
            content_preview="Auto accept test",
            reasoning="Auto accept reasoning"
        )

        ui = UserInterface(autoaccept=True)

        with patch('shutil.move') as mock_move:
            def mock_rename_func(src, dst):
                dst.parent.mkdir(parents=True, exist_ok=True)
                mock_move(src, dst)

            result = ui.handle_rename(proposal, None, mock_rename_func)

            assert result is True
            mock_move.assert_called_once()

    def test_ui_user_rejection(self, sample_txt_file, temp_dir):
        """Test UI handling user rejection."""
        from src.ui.interface import FileRenameProposal

        proposal = FileRenameProposal(
            current_path=sample_txt_file,
            new_path=temp_dir / "rejected.txt",
            content_preview="Rejection test",
            reasoning="Test rejection"
        )

        ui = UserInterface(autoaccept=False)

        with patch.object(ui, '_get_user_input', return_value='n'):
            with patch('shutil.move') as mock_move:
                def mock_rename_func(src, dst):
                    mock_move(src, dst)

                result = ui.handle_rename(proposal, None, mock_rename_func)

                assert result is True  # Continue processing
                mock_move.assert_not_called()


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_config_with_llm_client(self, temp_dir):
        """Test configuration integration with LLM client."""
        # Create config file
        config_file = temp_dir / "config.yaml"
        config_data = """
gemini:
  api_key: integration-test-key
  model: gemini-2.0-flash
  temperature: 0.8
  timeout: 60
"""
        config_file.write_text(config_data)

        from src.config import load_config
        config = load_config(config_file)

        with patch('src.core.llm.genai.Client'):
            llm_client = LLMClient(
                model=config.gemini.model,
                temperature=config.gemini.temperature,
                timeout=config.gemini.timeout,
                api_key=config.gemini.api_key
            )

            assert llm_client.model == "gemini-2.0-flash"
            assert llm_client.temperature == 0.8
            assert llm_client.timeout == 60
            assert llm_client.api_key == "integration-test-key"

    def test_taxonomy_file_integration(self, temp_dir):
        """Test taxonomy file integration with processing."""
        # Create custom taxonomy
        taxonomy_content = """# Custom Taxonomy

## Categories

### Invoices
- **Path:** `Business/{Company}/Invoices/{date}_{description}.pdf`
- **Rules:** Business invoices and receipts

### Contracts
- **Path:** `Legal/{Party}/Contracts/{date}_{description}.pdf`
- **Rules:** Legal contracts and agreements
"""
        taxonomy_file = temp_dir / "custom_taxonomy.md"
        taxonomy_file.write_text(taxonomy_content)

        # Test taxonomy parsing
        parser = TaxonomyParser(taxonomy_file)

        assert "Business/{Company}/Invoices" in parser.content
        assert "Legal/{Party}/Contracts" in parser.content
        assert "Business invoices and receipts" in parser.content


class TestErrorRecovery:
    """Integration tests for error recovery scenarios."""

    def test_partial_failure_recovery(self, temp_dir, sample_config):
        """Test recovery from partial processing failures."""
        # Create multiple files, some will fail
        good_file = temp_dir / "good.txt"
        bad_file = temp_dir / "bad.txt"
        good_file.write_text("Good content")
        bad_file.write_text("Bad content")

        files = [good_file, bad_file]

        def mock_process_file(path, **kwargs):
            if path.name == "bad.txt":
                raise Exception("Processing failed")
            return True

        with patch('src.rename._process_file', side_effect=mock_process_file):
            with patch('src.rename.logger') as mock_logger:
                rename_files(
                    paths=files,
                    recursive=False,
                    dry_run=False,
                    config_path=sample_config,
                    llm_client=Mock()
                )

                # Should log error but continue processing
                mock_logger.error.assert_called()

    def test_taxonomy_error_handling(self, temp_dir, sample_txt_file, sample_config):
        """Test handling taxonomy parsing errors."""
        # Create invalid taxonomy file
        bad_taxonomy = temp_dir / "bad_taxonomy.md"
        bad_taxonomy.write_text("")  # Empty file

        with pytest.raises(Exception):  # Should raise TaxonomyError
            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=Mock(),
                taxonomy_file=bad_taxonomy
            )
