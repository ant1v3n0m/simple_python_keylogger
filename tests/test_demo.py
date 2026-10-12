import unittest

from demo import run_sample_upload_demo


class SampleUploadDemoTests(unittest.TestCase):
    def test_fixed_sample_is_acknowledged_offline(self):
        result = run_sample_upload_demo()

        self.assertTrue(result["request"]["demo"])
        self.assertEqual(result["request"]["source"], "synthetic_sample")
        self.assertEqual(
            result["request"]["events"],
            [
                {"kind": "character", "value": "h"},
                {"kind": "character", "value": "i"},
                {"kind": "special", "value": "enter"},
            ],
        )
        self.assertEqual(result["receipt"]["received_events"], 3)
        self.assertFalse(result["receipt"]["network_sent"])


if __name__ == "__main__":
    unittest.main()
