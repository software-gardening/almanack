"""
Testing metrics/blobs functionality
"""

import pytest
import pygit2
from charset_normalizer import from_bytes
from almanack.metrics.blobs import detect_encoding, find_and_read_file

@pytest.mark.parametrize(
    "byte_data, expected_encoding, should_raise",
    [
        (b'\xef\xbb\xbf\xf0\x9f\xa9\xb3', 'utf_8', False), # Test detection of UTF-8 encoding
    (b'', None, True), # Test detection on empty byte sequence
        # Add more test cases here if needed
    ]
)
def test_detect_encoding(byte_data, expected_encoding, should_raise):
    """Test detection of encoding based on various byte inputs."""
    if should_raise:
        with pytest.raises(ValueError):
            detect_encoding(byte_data)
    else:
        detected_encoding = detect_encoding(byte_data)
        assert detected_encoding == expected_encoding


@pytest.mark.parametrize(
    "filename, expected_content",
    [
        ("README.md", "## Citation"),  # Exact match for file1.txt
        ("readme", None),         # Partial match, should return content of file1.txt
        ("nonexistent.txt", None),               # Non-existent file
    ]
)
def test_find_and_read_file(repo_with_citation_in_readme, filename, expected_content):
    """Test finding and reading files in the repository with various filename patterns."""

    # Call the function under test
    result = find_and_read_file(repo_with_citation_in_readme, filename)

    # Assert the result based on the expected content
    if expected_content is None:
        assert result is None  # Expecting None for non-existent files
    else:
        assert result == expected_content  # Expecting the actual content for found files
