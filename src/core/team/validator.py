"""
Optimized Validation System with Caching
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from functools import lru_cache
import logging
from src.utils.monitor import measure

logger = logging.getLogger(__name__)


class OptimizedValidator:
    """
    File content validator with intelligent caching.

    Features:
    - File content caching based on modification time
    - Compiled regex pattern caching
    - Single-pass normalization
    - Batch validation to avoid repeated file reads
    """

    def __init__(self):
        # Cache: (file_path, mtime) -> content
        self._file_cache: Dict[Tuple[Path, float], str] = {}
        # Pattern cache for compiled regex
        self._pattern_cache: Dict[str, re.Pattern] = {}

    @measure("validator.file_read")
    def _get_file_content(self, file_path: Path) -> str:
        """
        Retrieve file content with caching based on modification time.

        Args:
            file_path: Path to the file

        Returns:
            File content as string
        """
        try:
            stat_info = file_path.stat()
            cache_key = (file_path, stat_info.st_mtime)

            # Check cache first
            if cache_key in self._file_cache:
                logger.debug(f"Cache hit for {file_path}")
                return self._file_cache[cache_key]

            # Read and cache
            logger.debug(f"Cache miss for {file_path}, reading from disk")
            content = file_path.read_text(encoding='utf-8')

            # Limit cache size (keep only 50 most recent files)
            if len(self._file_cache) >= 50:
                # Remove oldest entry (first item)
                oldest_key = next(iter(self._file_cache))
                del self._file_cache[oldest_key]

            self._file_cache[cache_key] = content
            return content

        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    def _compile_pattern(self, required: str) -> re.Pattern:
        """
        Compile and cache regex pattern for content matching.

        Args:
            required: The required string pattern

        Returns:
            Compiled regex pattern
        """
        if required not in self._pattern_cache:
            # Escape special characters and allow flexible whitespace
            pattern_str = re.escape(required).replace(r'\ ', r'\s*')
            self._pattern_cache[required] = re.compile(pattern_str, re.MULTILINE)

        return self._pattern_cache[required]

    @measure("validator.validate_content")
    def validate_content(
        self,
        file_path: Path,
        requirements: List[str]
    ) -> List[str]:
        """
        Validate file content against multiple requirements efficiently.

        Args:
            file_path: Path to the file to validate
            requirements: List of required strings/patterns

        Returns:
            List of error messages (empty if all requirements met)
        """
        if not file_path.exists():
            return [f"File not found: {file_path}"]

        # Single file read for all requirements
        content = self._get_file_content(file_path)

        # Single normalization pass (lazy evaluation)
        normalized_content = None

        errors = []
        for required in requirements:
            # Strategy 1: Exact match (fastest)
            if required in content:
                continue

            # Strategy 2: Regex match with flexible whitespace
            pattern = self._compile_pattern(required)
            if pattern.search(content):
                continue

            # Strategy 3: Normalized match (only if needed)
            if normalized_content is None:
                normalized_content = ' '.join(content.split())

            normalized_required = ' '.join(required.split())
            if normalized_required in normalized_content:
                continue

            # All strategies failed
            errors.append(f"Failed to find '{required}' in {file_path.name}")

        return errors

    def validate_file_exists(self, file_path: Path) -> Optional[str]:
        """
        Check if file exists.

        Args:
            file_path: Path to check

        Returns:
            Error message if file doesn't exist, None otherwise
        """
        if not file_path.exists():
            return f"Missing required file: {file_path}"
        return None

    def validate_min_length(
        self,
        file_path: Path,
        min_chars: int
    ) -> Optional[str]:
        """
        Validate file has minimum character count.

        Args:
            file_path: Path to the file
            min_chars: Minimum required characters

        Returns:
            Error message if validation fails, None otherwise
        """
        if not file_path.exists():
            return f"File not found: {file_path}"

        content = self._get_file_content(file_path)
        actual_length = len(content)

        if actual_length < min_chars:
            return f"{file_path.name} has {actual_length} chars, minimum is {min_chars}"

        return None

    def validate_no_placeholders(
        self,
        file_path: Path,
        forbidden_patterns: List[str]
    ) -> List[str]:
        """
        Check that file doesn't contain placeholder patterns.

        Args:
            file_path: Path to the file
            forbidden_patterns: List of forbidden regex patterns

        Returns:
            List of error messages for found placeholders
        """
        if not file_path.exists():
            return [f"File not found: {file_path}"]

        content = self._get_file_content(file_path)
        errors = []

        for pattern_str in forbidden_patterns:
            try:
                pattern = re.compile(pattern_str)
                matches = pattern.findall(content)
                if matches:
                    errors.append(
                        f"Found {len(matches)} placeholder(s) matching '{pattern_str}' "
                        f"in {file_path.name}"
                    )
            except re.error as e:
                logger.error(f"Invalid regex pattern '{pattern_str}': {e}")
                errors.append(f"Invalid pattern '{pattern_str}'")

        return errors

    def clear_cache(self):
        """Clear all caches (useful for testing or memory management)."""
        self._file_cache.clear()
        self._pattern_cache.clear()
        logger.info("Validation cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring."""
        return {
            "file_cache_size": len(self._file_cache),
            "pattern_cache_size": len(self._pattern_cache)
        }
