from ingest_smart import process_easy_case, ai_stage1_classify, ai_stage2_extract
import unittest
from unittest.mock import MagicMock, patch

class TestSideLogic(unittest.TestCase):
    def test_regex_side_rebel(self):
        text = "مظاهرة للجيش الحر في حمص"
        result = process_easy_case(text)
        self.assertEqual(result['side'], 'REBEL')
        print(f"✅ Regex Rebel Test Passed: {result['side']}")

    def test_regex_side_gov(self):
        text = "قوات الجيش النظامي تقصف المدينة"
        result = process_easy_case(text)
        self.assertEqual(result['side'], 'GOV')
        print(f"✅ Regex Gov Test Passed: {result['side']}")

    def test_regex_side_neutral(self):
        text = "اشتباكات في دمشق"
        result = process_easy_case(text)
        self.assertEqual(result['side'], 'NEUTRAL')
        print(f"✅ Regex Neutral Test Passed: {result['side']}")

if __name__ == '__main__':
    unittest.main()
