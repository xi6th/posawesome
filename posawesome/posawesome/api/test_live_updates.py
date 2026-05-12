import importlib.util
import pathlib
import sys
import types
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _install_stubs():
    frappe_module = types.ModuleType("frappe")
    frappe_module.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe_module.ValidationError = Exception
    frappe_module.throw = lambda message: (_ for _ in ()).throw(Exception(message))
    frappe_module.get_doc = lambda *args, **kwargs: None
    frappe_module.get_cached_doc = lambda *args, **kwargs: None
    frappe_module.get_cached_value = lambda *args, **kwargs: None
    frappe_module.session = types.SimpleNamespace(user="test@example.com")
    frappe_module.db = types.SimpleNamespace()
    sys.modules["frappe"] = frappe_module

    frappe_utils = types.ModuleType("frappe.utils")
    frappe_utils.cstr = str
    sys.modules["frappe.utils"] = frappe_utils

    items_module = types.ModuleType("posawesome.posawesome.api.items")
    items_module.get_delta_items = lambda *args, **kwargs: []
    sys.modules["posawesome.posawesome.api.items"] = items_module

    utils_module = types.ModuleType("posawesome.posawesome.api.utils")
    utils_module._ensure_pos_profile = lambda pos_profile: (pos_profile, pos_profile)
    utils_module.get_active_pos_profile = lambda: {"name": "Main POS"}
    sys.modules["posawesome.posawesome.api.utils"] = utils_module


def _load_module():
    module_name = "posawesome.posawesome.api.live_updates"
    file_path = REPO_ROOT / "posawesome" / "posawesome" / "api" / "live_updates.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestLiveUpdates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _install_stubs()
        cls.module = _load_module()

    def test_build_stock_payload_normalizes_rows(self):
        payload = self.module.build_stock_payload(
            [
                {"item_code": "ITEM-001", "warehouse": "Stores - TC", "actual_qty": 4, "company": "TC"},
                {"item_code": "ITEM-001", "warehouse": "Stores - TC", "actual_qty": 5, "company": "TC"},
                {"item_code": "", "warehouse": "Ignored", "actual_qty": 1},
            ]
        )

        self.assertEqual(payload["item_codes"], ["ITEM-001"])
        self.assertEqual(payload["warehouses"], ["Stores - TC"])
        self.assertEqual(payload["companies"], ["TC"])
        self.assertEqual(payload["items"][0]["actual_qty"], 4)

    def test_format_sse_event_serializes_payload(self):
        event = self.module._format_sse_event("posa_stock_changed", {"ok": True})

        self.assertIn("event: posa_stock_changed", event)
        self.assertIn('"ok": true', event.lower())


if __name__ == "__main__":
    unittest.main()
