import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.json_utils import extract_json

class TestJsonExtraction(unittest.TestCase):
    def test_clean_json(self):
        text = '{"key": "value"}'
        self.assertEqual(extract_json(text), {"key": "value"})

    def test_markdown_json(self):
        text = 'Here is the json:\n```json\n{"key": "value"}\n```'
        self.assertEqual(extract_json(text), {"key": "value"})

    def test_markdown_no_lang(self):
        text = '```\n{"key": "value"}\n```'
        self.assertEqual(extract_json(text), {"key": "value"})

    def test_surrounding_text(self):
        text = 'Some text before {"key": "value"} and after.'
        self.assertEqual(extract_json(text), {"key": "value"})

    def test_nested_structures(self):
        text = '{"key": {"nested": [1, 2, 3]}}'
        self.assertEqual(extract_json(text), {"key": {"nested": [1, 2, 3]}})

    def test_malformed_json(self):
        text = 'Not json'
        self.assertIsNone(extract_json(text))

    def test_xml_tags(self):
        text = '{"key": "value"}</arg_value>'
        self.assertEqual(extract_json(text), {"key": "value"})

if __name__ == '__main__':
    unittest.main()
