"""Tests for UI components."""

from unittest.mock import Mock, patch

from src.ui.interface import FileRenameProposal, UserInterface


class TestFileRenameProposal:
    """Tests for FileRenameProposal dataclass."""

    def test_file_rename_proposal_creation(self, temp_dir):
        """Test creating a FileRenameProposal instance."""
        current_path = temp_dir / "old.txt"
        new_path = temp_dir / "new.txt"
        current_path.write_text("test content")

        proposal = FileRenameProposal(
            current_path=current_path,
            new_path=new_path,
            content_preview="test content preview",
            reasoning="test reasoning"
        )

        assert proposal.current_path == current_path
        assert proposal.new_path == new_path
        assert proposal.content_preview == "test content preview"
        assert proposal.reasoning == "test reasoning"
        assert proposal.taxonomy_rule is None
        assert proposal.override_instructions is None

    def test_file_rename_proposal_with_optional_fields(self, temp_dir):
        """Test FileRenameProposal with optional fields."""
        current_path = temp_dir / "old.txt"
        new_path = temp_dir / "new.txt"
        current_path.write_text("test content")

        mock_rule = Mock()
        proposal = FileRenameProposal(
            current_path=current_path,
            new_path=new_path,
            content_preview="test content",
            reasoning="test reasoning",
            taxonomy_rule=mock_rule,
            override_instructions="custom override"
        )

        assert proposal.taxonomy_rule == mock_rule
        assert proposal.override_instructions == "custom override"


class TestUserInterface:
    """Tests for UserInterface class."""

    def test_user_interface_creation(self):
        """Test creating a UserInterface instance."""
        ui = UserInterface(autoaccept=False)

        assert ui.autoaccept is False
        assert ui.console is not None
        assert ui.total_files == 0
        assert ui.processed_files == 0

    def test_user_interface_autoaccept_mode(self):
        """Test UserInterface in autoaccept mode."""
        ui = UserInterface(autoaccept=True)

        assert ui.autoaccept is True

    def test_display_progress(self):
        """Test progress display functionality."""
        ui = UserInterface()
        ui.total_files = 10

        with patch.object(ui.console, 'print') as mock_print:
            ui.display_progress(5, 10)

            # Should display progress information
            mock_print.assert_called()

    def test_display_summary(self):
        """Test summary display functionality."""
        ui = UserInterface()

        with patch.object(ui.console, 'print') as mock_print:
            ui.display_summary(
                processed=10,
                renamed=8,
                skipped=1,
                failed=1
            )

            # Should display summary information
            mock_print.assert_called()

    def test_handle_rename_autoaccept(self, temp_dir):
        """Test handle_rename in autoaccept mode."""
        ui = UserInterface(autoaccept=True)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="auto accept test"
        )

        rename_func = Mock()

        result = ui.handle_rename(proposal, None, rename_func)

        assert result is True
        rename_func.assert_called_once_with(proposal.current_path, proposal.new_path)

    def test_handle_rename_user_accepts(self, temp_dir):
        """Test handle_rename when user accepts."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="user accept test"
        )

        rename_func = Mock()

        with patch.object(ui, '_get_user_input', return_value='y'):
            result = ui.handle_rename(proposal, None, rename_func)

            assert result is True
            rename_func.assert_called_once()

    def test_handle_rename_user_rejects(self, temp_dir):
        """Test handle_rename when user rejects."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="user reject test"
        )

        rename_func = Mock()

        with patch.object(ui, '_get_user_input', return_value='n'):
            result = ui.handle_rename(proposal, None, rename_func)

            assert result is True  # Continue processing
            rename_func.assert_not_called()

    def test_handle_rename_user_quits(self, temp_dir):
        """Test handle_rename when user quits."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="user quit test"
        )

        rename_func = Mock()

        with patch.object(ui, '_get_user_input', return_value='q'):
            result = ui.handle_rename(proposal, None, rename_func)

            assert result is False  # Stop processing
            rename_func.assert_not_called()

    def test_handle_rename_view_content(self, temp_dir):
        """Test handle_rename view content option."""
        ui = UserInterface(autoaccept=False)

        current_path = temp_dir / "test.txt"
        current_path.write_text("This is test file content for viewing")

        proposal = FileRenameProposal(
            current_path=current_path,
            new_path=temp_dir / "new.txt",
            content_preview="preview",
            reasoning="view test"
        )

        rename_func = Mock()

        # Mock user inputs: first 'v' to view, then 'y' to accept
        with patch.object(ui, '_get_user_input', side_effect=['v', 'y']):
            with patch.object(ui, '_display_file_content') as mock_display:
                result = ui.handle_rename(proposal, None, rename_func)

                assert result is True
                mock_display.assert_called_once()
                rename_func.assert_called_once()

    def test_handle_rename_edit_suggestion(self, temp_dir):
        """Test handle_rename edit suggestion option."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="edit test"
        )

        rename_func = Mock()

        # Mock user inputs: first 'e' to edit, then return edited path, then 'y' to accept
        with patch.object(ui, '_get_user_input', side_effect=['e', 'y']):
            with patch.object(ui, '_edit_suggestion', return_value=temp_dir / "edited.txt"):
                result = ui.handle_rename(proposal, None, rename_func)

                assert result is True
                # Should call rename_func with edited path
                rename_func.assert_called_once()
                call_args = rename_func.call_args[0]
                assert call_args[1] == temp_dir / "edited.txt"

    def test_handle_rename_move_to_trash(self, temp_dir):
        """Test handle_rename move to trash option."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="trash test"
        )

        rename_func = Mock()

        with patch.object(ui, '_get_user_input', return_value='t'):
            with patch.object(ui, '_move_to_trash') as mock_trash:
                result = ui.handle_rename(proposal, None, rename_func)

                assert result is True
                mock_trash.assert_called_once_with(proposal.current_path)
                rename_func.assert_not_called()

    def test_handle_rename_override_instructions(self, temp_dir):
        """Test handle_rename with override instructions."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="override test"
        )

        rename_func = Mock()

        # Mock user inputs: first '!' for override, then 'y' to accept
        with patch.object(ui, '_get_user_input', side_effect=['!', 'y']):
            with patch.object(ui, '_get_override_instructions', return_value="custom override"):
                with patch.object(ui, '_regenerate_with_override') as mock_regen:
                    mock_regen.return_value = FileRenameProposal(
                        current_path=temp_dir / "old.txt",
                        new_path=temp_dir / "override.txt",
                        content_preview="test content",
                        reasoning="override applied",
                        override_instructions="custom override"
                    )

                    result = ui.handle_rename(proposal, None, rename_func)

                    assert result is True
                    mock_regen.assert_called_once()

    def test_handle_rename_invalid_input(self, temp_dir):
        """Test handle_rename with invalid user input."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="invalid input test"
        )

        rename_func = Mock()

        # Mock invalid input followed by valid input
        with patch.object(ui, '_get_user_input', side_effect=['x', 'y']):
            with patch.object(ui.console, 'print') as mock_print:
                result = ui.handle_rename(proposal, None, rename_func)

                assert result is True
                # Should show error message for invalid input
                error_calls = [call for call in mock_print.call_args_list
                              if 'Invalid' in str(call) or 'invalid' in str(call)]
                assert len(error_calls) > 0

    def test_handle_rename_with_taxonomy(self, temp_dir, sample_taxonomy_parser):
        """Test handle_rename with taxonomy information."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="taxonomy test"
        )

        rename_func = Mock()

        with patch.object(ui, '_get_user_input', return_value='y'):
            result = ui.handle_rename(proposal, sample_taxonomy_parser, rename_func)

            assert result is True
            rename_func.assert_called_once()

    def test_handle_rename_error_during_rename(self, temp_dir):
        """Test handle_rename when rename operation fails."""
        ui = UserInterface(autoaccept=False)

        proposal = FileRenameProposal(
            current_path=temp_dir / "old.txt",
            new_path=temp_dir / "new.txt",
            content_preview="test content",
            reasoning="error test"
        )

        rename_func = Mock(side_effect=Exception("Rename failed"))

        with patch.object(ui, '_get_user_input', return_value='y'):
            with patch.object(ui.console, 'print') as mock_print:
                result = ui.handle_rename(proposal, None, rename_func)

                assert result is True  # Continue processing despite error
                # Should show error message
                error_calls = [call for call in mock_print.call_args_list
                              if 'Error' in str(call) or 'failed' in str(call)]
                assert len(error_calls) > 0


class TestUIHelperMethods:
    """Tests for UI helper methods."""

    def test_display_file_content(self, temp_dir):
        """Test file content display."""
        ui = UserInterface()

        test_file = temp_dir / "content.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        with patch.object(ui.console, 'print') as mock_print:
            ui._display_file_content(test_file)

            # Should display file content
            mock_print.assert_called()

    def test_move_to_trash(self, temp_dir):
        """Test move to trash functionality."""
        ui = UserInterface()

        test_file = temp_dir / "trash_me.txt"
        test_file.write_text("content to trash")

        with patch('shutil.move') as mock_move:
            with patch('pathlib.Path.mkdir') as mock_mkdir:
                ui._move_to_trash(test_file)

                # Should create trash directory and move file
                mock_mkdir.assert_called()
                mock_move.assert_called()

    def test_edit_suggestion(self, temp_dir):
        """Test edit suggestion functionality."""
        ui = UserInterface()

        original_path = temp_dir / "original.txt"

        with patch('builtins.input', return_value=str(temp_dir / "edited.txt")):
            result = ui._edit_suggestion(original_path)

            assert result == temp_dir / "edited.txt"

    def test_get_override_instructions(self):
        """Test getting override instructions from user."""
        ui = UserInterface()

        with patch('builtins.input', return_value="Place in custom directory"):
            result = ui._get_override_instructions()

            assert result == "Place in custom directory"

    def test_get_user_input(self):
        """Test getting user input."""
        ui = UserInterface()

        with patch('builtins.input', return_value="y"):
            result = ui._get_user_input()

            assert result == "y"
