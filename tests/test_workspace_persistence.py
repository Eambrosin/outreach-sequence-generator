import unittest

from workspace_persistence import (
    _query_mandate_id,
    ensure_mandate_id,
    is_enabled,
)


class FakeStreamlit:
    def __init__(self, query_params):
        self.query_params = query_params


class WorkspacePersistenceTests(unittest.TestCase):
    def test_disabled_without_credentials(self):
        self.assertFalse(
            is_enabled(
                {
                    "url": "",
                    "key": "",
                    "access_token": "",
                }
            )
        )

    def test_disabled_without_private_access_token(self):
        self.assertFalse(
            is_enabled(
                {
                    "url": "https://example.supabase.co",
                    "key": "test-key",
                    "access_token": "",
                }
            )
        )

    def test_enabled_with_backend_and_private_access(self):
        self.assertTrue(
            is_enabled(
                {
                    "url": "https://example.supabase.co",
                    "key": "test-key",
                    "access_token": "workspace-secret",
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

    def test_query_mandate_id_is_resolved(self):
        st = FakeStreamlit(
            {"mandate_id": "mandate_auto_123"}
        )
        self.assertEqual(
            _query_mandate_id(st),
            "mandate_auto_123",
        )

    def test_query_mandate_id_handles_list_value(self):
        st = FakeStreamlit(
            {"mandate_id": ["mandate_auto_456"]}
        )
        self.assertEqual(
            _query_mandate_id(st),
            "mandate_auto_456",
        )


if __name__ == "__main__":
    unittest.main()
