import os
import pytest
from unittest.mock import Mock, patch
from python_modules.google_drive_support import upload_file  # Replace 'your_module' with the actual module name where upload_file is defined

# Define a fixture for a mock Google Drive service
@pytest.fixture
def mock_drive_service():
    return Mock()

def test_upload_file_without_overwrite(mock_drive_service):
    # Mock get_google_drive_file_id to return None
    with patch('python_modules.google_drive_support.get_google_drive_file_id', return_value=None):
        # Mock create method to return a file ID
        mock_drive_service.files().create.return_value.execute.return_value = {'id': 'new_file_id'}
        file_id = upload_file(mock_drive_service, 'README.md', 'folder_id', overwrite=False)

    assert file_id == 'new_file_id'

    # Check that delete_google_drive_item was not called
    mock_drive_service.files().create.assert_called_once()
    assert not mock_drive_service.delete_google_drive_item.called

