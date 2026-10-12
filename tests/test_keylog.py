import json
import platform
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from keylog import SessionWriter, new_session_path, normalize_key


class NormalizeKeyTests(unittest.TestCase):
    def test_character_preserves_unicode_and_quotes(self):
        self.assertEqual(normalize_key(SimpleNamespace(char="é'")), {"kind": "character", "value": "é'"})

    def test_special_key_is_named(self):
        self.assertEqual(normalize_key(SimpleNamespace(name="backspace")), {"kind": "special", "value": "backspace"})

    def test_virtual_key_fallback(self):
        self.assertEqual(normalize_key(SimpleNamespace(vk=123)), {"kind": "virtual_key", "value": "123"})

    def test_unknown_key_does_not_leak_repr(self):
        class Unknown:
            def __repr__(self):
                return "sensitive display text"

        self.assertEqual(normalize_key(Unknown()), {"kind": "unknown", "value": "Unknown"})


class SessionWriterTests(unittest.TestCase):
    def test_session_is_json_lines_with_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = new_session_path(Path(directory))
            writer = SessionWriter(path)
            writer.write_key("2026-01-01T00:00:00+00:00", {"kind": "character", "value": "é'"})
            writer.write_key("2026-01-01T00:00:01+00:00", {"kind": "special", "value": "backspace"})
            writer.close("user_stopped")
            writer.close("user_stopped")

            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([r["event"] for r in records], ["start", "key", "key", "stop"])
            self.assertEqual(records[0]["schema_version"], 1)
            self.assertEqual(records[0]["os"], platform.system())
            self.assertEqual(records[1]["value"], "é'")
            self.assertEqual(records[2]["value"], "backspace")
            self.assertEqual(records[3]["reason"], "user_stopped")

    def test_existing_session_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.jsonl"
            path.write_text("original", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                SessionWriter(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "original")


if __name__ == "__main__":
    unittest.main()
