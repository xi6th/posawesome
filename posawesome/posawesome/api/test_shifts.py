import importlib.util
import pathlib
import sys
import types
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _install_stubs():
    frappe_module = types.ModuleType("frappe")
    frappe_module._ = lambda text: text
    frappe_module.whitelist = lambda *args, **kwargs: (lambda fn: fn)
    frappe_module.log_error = lambda *args, **kwargs: None
    frappe_module.get_doc = lambda *args, **kwargs: None
    frappe_module.get_cached_value = lambda *args, **kwargs: None
    frappe_module.session = types.SimpleNamespace(user="cashier@example.com")
    frappe_module.local = types.SimpleNamespace(lang=None)
    frappe_module.db = types.SimpleNamespace(
        get_all=lambda *args, **kwargs: [],
        get_single_value=lambda *args, **kwargs: 0,
    )
    sys.modules["frappe"] = frappe_module

    frappe_utils = types.ModuleType("frappe.utils")
    frappe_utils.cint = int
    frappe_utils.nowdate = lambda: "2026-05-12"
    sys.modules["frappe.utils"] = frappe_utils

    utilities_module = types.ModuleType("posawesome.posawesome.api.utilities")
    utilities_module.get_version = lambda: 13
    sys.modules["posawesome.posawesome.api.utilities"] = utilities_module

    shift_guard_module = types.ModuleType("posawesome.posawesome.api.shift_guard")

    def _stub_filters(user=None):
        return {
            "user": user or sys.modules["frappe"].session.user,
            "status": "Open",
            "docstatus": 1,
            "pos_closing_shift": ["is", "not set"],
            "period_start_date": [">=", "STUB_CUTOFF"],
        }

    shift_guard_module.get_active_own_shift_filters = _stub_filters
    shift_guard_module.enforce_own_active_shift = lambda ref=None, **kwargs: None
    sys.modules["posawesome.posawesome.api.shift_guard"] = shift_guard_module


def _load_module():
    module_name = "posawesome.posawesome.api.shifts"
    file_path = REPO_ROOT / "posawesome" / "posawesome" / "api" / "shifts.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestOpeningShiftLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _install_stubs()
        cls.shifts = _load_module()

    def test_check_opening_shift_uses_session_user(self):
        captured = {}

        def fake_get_all(doctype, **kwargs):
            captured["doctype"] = doctype
            captured["kwargs"] = kwargs
            return []

        self.shifts.frappe.db.get_all = fake_get_all
        self.shifts.check_opening_shift("other@example.com")

        self.assertEqual(captured["doctype"], "POS Opening Shift")
        self.assertEqual(captured["kwargs"]["filters"]["user"], "cashier@example.com")

    def test_check_opening_shift_does_not_trust_spoofed_user(self):
        captured = {}

        def fake_get_all(doctype, **kwargs):
            captured["kwargs"] = kwargs
            return []

        self.shifts.frappe.db.get_all = fake_get_all
        self.shifts.check_opening_shift("manager@example.com")

        self.assertEqual(captured["kwargs"]["filters"]["user"], "cashier@example.com")

    def test_check_opening_shift_filters_embed_activity_and_freshness(self):
        captured = {}

        def fake_get_all(doctype, **kwargs):
            captured["kwargs"] = kwargs
            return []

        self.shifts.frappe.db.get_all = fake_get_all
        self.shifts.check_opening_shift()

        filters = captured["kwargs"]["filters"]
        self.assertEqual(filters["user"], "cashier@example.com")
        self.assertEqual(filters["status"], "Open")
        self.assertEqual(filters["docstatus"], 1)
        self.assertEqual(filters["pos_closing_shift"], ["is", "not set"])
        self.assertEqual(filters["period_start_date"], [">=", "STUB_CUTOFF"])


if __name__ == "__main__":
    unittest.main()
