import unittest

from workspace_persistence import (
    ensure_mandate_id,
    is_enabled,
)


class WorkspacePersistenceTests(unittest.TestCase):
    def test_disabled_without_credentials(self):
        self.assertFalse(is_enabled({"url": "", "key": ""}))

    def test_enabled_with_url_and_key(self):
        self.assertTrue(
            is_enabled(
                {
                    "url": "https://example.supabase.co",
                    "key": "test-key",
                }
            )
        )

    def test_existing_mandate_id_is_preserved(self):
        self.assertEqual(
            ensure_mandate_id({"mandate_id": "mandate_existing"}),
            "mandate_existing",
        )

    def test_missing_mandate_id_is_generated(self):
        value = ensure_mandate_id({})
        self.assertTrue(value.startswith("mandate_"))
        self.assertGreater(len(value), len("mandate_"))


if __name__ == "__main__":
    unittest.main()
