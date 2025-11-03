# tests/test_common_utils.py
# Tests for common/utils.py - utility functions

import io
import os
import pytest
from PIL import Image
from common.utils import (
    fsize,
    compress_imgfile,
    split_string_by_utf8_length,
    get_path_suffix,
    remove_markdown_symbol,
)


class TestFsize:
    """Test file size calculation for different input types."""

    def test_fsize_bytesio(self):
        """Test size calculation for BytesIO objects."""
        data = b"Hello World"
        file = io.BytesIO(data)
        assert fsize(file) == len(data)

    def test_fsize_string_path(self, temp_dir):
        """Test size calculation for file paths."""
        test_file = os.path.join(temp_dir, "test.txt")
        content = "Test content"
        with open(test_file, "w") as f:
            f.write(content)
        assert fsize(test_file) == len(content.encode())

    def test_fsize_file_object(self, temp_dir):
        """Test size calculation for file objects."""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "wb") as f:
            f.write(b"Test data")
        with open(test_file, "rb") as f:
            assert fsize(f) == 9

    def test_fsize_unsupported_type(self):
        """Test that unsupported types raise TypeError."""
        with pytest.raises(TypeError, match="Unsupported type"):
            fsize(12345)


class TestCompressImgfile:
    """Test image compression functionality."""

    def test_compress_imgfile_no_compression_needed(self):
        """Test that small images are not compressed."""
        # Create a small test image
        img = Image.new("RGB", (10, 10), color="red")
        buf = io.BytesIO()
        img.save(buf, "JPEG")
        buf.seek(0)
        
        original_size = fsize(buf)
        result = compress_imgfile(buf, max_size=original_size + 1000)
        
        # Should return the same buffer if already small enough
        assert result == buf

class TestSplitStringByUtf8Length:
    """Test UTF-8 aware string splitting."""

    def test_split_ascii_string(self):
        """Test splitting simple ASCII strings."""
        text = "Hello World"
        result = split_string_by_utf8_length(text, max_length=5)
        assert result == ["Hello", " Worl", "d"]

    def test_split_utf8_string(self):
        """Test splitting strings with multi-byte UTF-8 characters."""
        text = "你好世界"  # Chinese characters (3 bytes each in UTF-8)
        result = split_string_by_utf8_length(text, max_length=6)
        # Each Chinese character is 3 bytes, so max_length=6 fits 2 characters
        assert result == ["你好", "世界"]

    def test_split_with_max_split(self):
        """Test max_split parameter limits number of chunks."""
        text = "abcdefghijklmnop"
        result = split_string_by_utf8_length(text, max_length=3, max_split=2)
        assert len(result) == 3
        assert result == ["abc", "def", "ghijklmnop"]

    def test_split_empty_string(self):
        """Test splitting empty string."""
        result = split_string_by_utf8_length("", max_length=10)
        assert result == []


class TestGetPathSuffix:
    """Test file extension extraction."""

    def test_get_path_suffix_simple(self):
        """Test extracting suffix from simple paths."""
        assert get_path_suffix("/path/to/file.txt") == "txt"
        assert get_path_suffix("image.png") == "png"

    def test_get_path_suffix_url(self):
        """Test extracting suffix from URLs."""
        url = "https://example.com/path/to/image.jpg?param=value"
        assert get_path_suffix(url) == "jpg"

    def test_get_path_suffix_no_extension(self):
        """Test paths without extensions."""
        assert get_path_suffix("/path/to/file") == ""


class TestRemoveMarkdownSymbol:
    """Test markdown symbol removal."""

    def test_remove_bold_markdown(self):
        """Test removing ** bold markers."""
        text = "This is **bold** text"
        result = remove_markdown_symbol(text)
        assert result == "This is bold text"

    def test_remove_multiple_bold(self):
        """Test removing multiple bold markers."""
        text = "**First** and **second** bold"
        result = remove_markdown_symbol(text)
        assert result == "First and second bold"

    def test_remove_markdown_none_input(self):
        """Test handling None input."""
        result = remove_markdown_symbol(None)
        assert result is None

    def test_remove_markdown_empty_string(self):
        """Test handling empty string."""
        result = remove_markdown_symbol("")
        assert result == ""