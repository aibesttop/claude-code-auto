"""
Test script for validation fix

Tests the improved content_check validation logic.
"""

import re
import tempfile
from pathlib import Path


def test_content_check_logic():
    """Test the 3-method content checking approach"""

    # Test cases: variations of markdown headers
    test_cases = [
        # (file_content, required_section, should_pass, test_name)
        ("## Target Users\nContent here", "## Target Users", True, "Exact match"),
        ("##  Target Users\nContent", "## Target Users", True, "Extra space after ##"),
        ("##Target Users\nContent", "## Target Users", True, "No space after ##"),
        ("##   Target   Users\nContent", "## Target Users", True, "Multiple spaces"),
        ("## target users\nContent", "## Target Users", False, "Case sensitive fail"),
        ("### Target Users\nContent", "## Target Users", True, "Substring match (acceptable)"),
        ("Content without header", "## Target Users", False, "Missing header"),
        (
            """# Main Title

## Executive Summary
This is a summary.

## Target Users
- User segment 1
- User segment 2

## Competitor Analysis
Analysis here.

## Market Size
$4.1B by 2029

## User Pain Points
- Pain 1
- Pain 2

## Opportunities
- Opportunity 1
""",
            "## Target Users",
            True,
            "Real markdown document"
        ),
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("🧪 Testing Improved Content Check Logic")
    print("=" * 70)

    for content, required, should_pass, test_name in test_cases:
        # Simulate the 3-method approach from role_executor.py
        found = False

        # Method 1: Try exact match first (fastest)
        if required in content:
            found = True
            method = "Method 1: Exact match"

        # Method 2: Try flexible whitespace pattern
        if not found:
            pattern = re.escape(required)
            pattern = pattern.replace(r'\ ', r'\s*')  # Allow 0 or more spaces

            if re.search(pattern, content, re.MULTILINE):
                found = True
                method = "Method 2: Flexible pattern"

        # Method 3: Try normalized comparison
        if not found:
            normalized_required = ' '.join(required.split())
            normalized_content = ' '.join(content.split())

            if normalized_required in normalized_content:
                found = True
                method = "Method 3: Normalized"

        # Check result
        test_passed = (found == should_pass)

        if test_passed:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"

        print(f"\n{status} | {test_name}")
        print(f"  Required: '{required}'")
        content_preview = content[:50].replace('\n', '\\n')
        print(f"  Content preview: {content_preview}...")
        expected_str = 'found' if should_pass else 'not found'
        got_str = 'found' if found else 'not found'
        print(f"  Expected: {expected_str}, Got: {got_str}")
        if found:
            print(f"  Matched by: {method}")

    print("\n" + "=" * 70)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


def test_infinite_loop_protection():
    """Test infinite loop detection logic"""

    print("\n" + "=" * 70)
    print("🔁 Testing Infinite Loop Protection")
    print("=" * 70)

    # Simulate validation error history
    error_history = [
        ["error1", "error2"],
        ["error1", "error2"],  # Same errors - count = 1
        ["error1", "error2"],  # Same errors - count = 2 -> should break
        ["error3"],            # Different - would reset
    ]

    previous_errors = []
    same_error_count = 0
    MAX_SAME_ERROR_RETRIES = 2

    for iteration, current_errors in enumerate(error_history, 1):
        current_errors_sorted = sorted(current_errors)

        if previous_errors and current_errors_sorted == previous_errors:
            same_error_count += 1
            print(f"  Iteration {iteration}: Same errors detected ({same_error_count} times)")

            if same_error_count >= MAX_SAME_ERROR_RETRIES:
                print(f"  ❌ Breaking loop after {same_error_count} identical errors!")
                print(f"  ✅ PASS: Loop protection activated at iteration {iteration}")
                return True
        else:
            if previous_errors:
                print(f"  Iteration {iteration}: Different errors, reset counter")
            same_error_count = 0

        previous_errors = current_errors_sorted

    print("  ❌ FAIL: Loop protection did not activate")
    return False


def test_header_extraction():
    """Test markdown header extraction for debugging"""

    print("\n" + "=" * 70)
    print("📝 Testing Header Extraction")
    print("=" * 70)

    content = """
# Main Title

## Executive Summary
This is the summary.

## Target Users
- User 1
- User 2

###  Subsection
Details here

## Competitor Analysis
Analysis content.
"""

    headers = re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE)

    print(f"\nExtracted {len(headers)} headers:")
    for h in headers:
        print(f"  - {h}")

    expected_count = 5  # Main Title, Executive Summary, Target Users, Subsection, Competitor Analysis
    if len(headers) == expected_count:
        print(f"\n✅ PASS: Found {len(headers)} headers as expected")
        return True
    else:
        print(f"\n❌ FAIL: Expected {expected_count} headers, found {len(headers)}")
        return False


if __name__ == "__main__":
    print("\n🚀 Running Validation Fix Tests\n")

    test1 = test_content_check_logic()
    test2 = test_infinite_loop_protection()
    test3 = test_header_extraction()

    print("\n" + "=" * 70)
    print("📋 FINAL RESULTS")
    print("=" * 70)
    print(f"Content Check Logic:      {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Infinite Loop Protection: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Header Extraction:        {'✅ PASS' if test3 else '❌ FAIL'}")

    all_passed = test1 and test2 and test3

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Review output above")
    print("=" * 70)

    exit(0 if all_passed else 1)
