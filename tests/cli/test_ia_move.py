import responses
from urllib.parse import urlparse, unquote

from tests.conftest import IaRequestsMock, ia_call, PROTOCOL


def test_ia_move_subdirectory(capsys, tmpdir_ch):
    """Test that the ia move command correctly handles subdirectories.
    
    This test verifies that when moving a file from a subdirectory, the delete operation
    correctly includes the subdirectory path in the URL (/identifier/sub_dir/file).
    """
    # Create minimal mock metadata
    source_metadata = '{"metadata":{"identifier":"identifier"},"files":[{"name":"sub_dir/file"}]}'
    dest_metadata = '{"metadata":{"identifier":"some_other_identifier"}}'
    
    # Flag to verify the DELETE request path
    delete_path_verified = False
    
    with IaRequestsMock(assert_all_requests_are_fired=False) as rsps:
        # Mock metadata
        rsps.add_metadata_mock('identifier', body=source_metadata)
        rsps.add_metadata_mock('some_other_identifier', body=dest_metadata)
        
        # Mock the COPY (PUT) operation - we don't need to verify this
        rsps.add(
            responses.PUT,
            f'{PROTOCOL}//s3.us.archive.org/some_other_identifier/sub_dir/file',
            body='',
            status=200
        )
        
        # Mock and verify the DELETE request path
        def verify_delete_path(request):
            nonlocal delete_path_verified
            
            # Extract and verify the path
            url_path = unquote(urlparse(request.url).path)
            
            # This is what we're testing - the path should include the subdirectory
            assert '/identifier/sub_dir/file' == url_path
            delete_path_verified = True
            
            return (204, {}, '')

        # Add the DELETE callback
        rsps.add_callback(
            responses.DELETE,
            f'{PROTOCOL}//s3.us.archive.org/identifier/sub_dir/file',
            callback=verify_delete_path
        )
        
        # Run the move command
        ia_call(['ia', 'move', 'identifier/sub_dir/file', 'some_other_identifier/sub_dir/file'])
        
        # Verify our delete path check was called
        assert delete_path_verified, "DELETE request path verification was not triggered"
    
    # Check for success message
    out, err = capsys.readouterr()
    assert "success: moved 'identifier/sub_dir/file' to 'some_other_identifier/sub_dir/file'" in err 