"""Stub-based unit tests for posawesome.posawesome.api.shift_guard.

Mirrors the convention of test_invoice_shift_validation.py: a fake
``frappe`` module is injected into sys.modules so the target loads with
zero Frappe runtime. Behaviour state lives in ``STATE``; tests mutate it
(or the stub's ``session.user`` / ``has_role``) to simulate scenarios.
"""

import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
TARGET_PATH = REPO_ROOT / "posawesome" / "posawesome" / "api" / "shift_guard.py"

FIXED_NOW = datetime(2026, 8, 26, 10, 0, 0)
SESSION_USER = "cashier@example.com"
OTHER_USER = "someoneelse@example.com"
GUARD_LOG_TITLE = "POS Awesome Shift Guard"


def _fake_cint(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _install_stubs():
    if "frappe" in sys.modules:
        del sys.modules["frappe"]

    frappe = types.ModuleType("frappe")
    utils_mod = types.ModuleType("frappe.utils")

    utils_mod.cint = _fake_cint
    utils_mod.now_datetime = lambda: FIXED_NOW

    frappe._ = lambda s: s
    frappe.throw = lambda msg=None, **kwargs: (_ for _ in ()).throw(Exception(str(msg)))
    frappe.log_error = lambda msg="", title=None: STATE["logs"].append((str(msg), title))
    frappe.session = SimpleNamespace(user=SESSION_USER)
    frappe.conf = SimpleNamespace(get=lambda key: STATE["conf"].get(key))
    frappe.has_role = lambda roles=None: STATE["has_role"]
    frappe.get_roles = lambda: ("System Manager",) if STATE["has_role"] else ()
    frappe.db = SimpleNamespace(
        exists=lambda doctype, filters=None: (
            STATE["members"] and (filters or {}).get("user") == frappe.session.user
        )
    )
    frappe.get_cached_doc = lambda doctype, name=None: STATE["shifts"].get(name)

    frappe.utils = utils_mod
    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = utils_mod
    return frappe


def _load_module():
    spec = importlib.util.spec_from_file_location("shift_guard_under_test", TARGET_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATE = {}


def reset_state():
    STATE.clear()
    STATE.update(
        {
            "conf": {},
            "has_role": False,
            "members": True,
            "logs": [],
            "shifts": {},
        }
    )


def make_shift(**overrides):
    data = {
        "name": "POSA-T-0001",
        "status": "Open",
        "user": SESSION_USER,
        "pos_profile": "Till One",
        "pos_closing_shift": None,
        "period_start_date": FIXED_NOW - timedelta(hours=1),
    }
    data.update(overrides)
    doc = SimpleNamespace(**data)
    STATE["shifts"][data["name"]] = doc
    return doc


class TestShiftGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frappe_stub = _install_stubs()
        cls.guard = _load_module()

    def setUp(self):
        reset_state()

    # --- condition 1: reference resolution ---------------------------

    def test_happy_path_returns_same_document(self):
        shift = make_shift()
        result = self.guard.enforce_own_active_shift(shift.name)
        self.assertIs(result, shift)

    def test_missing_reference_is_rejected(self):
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift(None)
        self.assertIn("reference is required", str(ctx.exception))

    def test_unknown_reference_is_rejected_and_security_logged(self):
        with self.assertRaises(Exception):
            self.guard.enforce_own_active_shift("POSA-DOES-NOT-EXIST")
        titles = [title for _, title in STATE["logs"]]
        self.assertIn(GUARD_LOG_TITLE, titles)

    # --- condition 2: activity status ---------------------------------

    def test_closed_shift_is_rejected(self):
        make_shift(status="Closed")
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001")
        self.assertIn("is not active", str(ctx.exception))

    def test_shift_already_linked_to_closing_is_rejected(self):
        make_shift(pos_closing_shift="POSA-CS-0009")
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001")
        self.assertIn("is not active", str(ctx.exception))

    # --- freshness -----------------------------------------------------

    def test_default_freshness_window_is_24_hours(self):
        self.assertEqual(self.guard.get_shift_freshness_hours(), 24)

    def test_freshness_window_reads_site_config(self):
        STATE["conf"]["posa_shift_max_age_hours"] = "2"
        self.assertEqual(self.guard.get_shift_freshness_hours(), 2)

    def test_shift_within_short_custom_window_passes(self):
        STATE["conf"]["posa_shift_max_age_hours"] = "2"
        make_shift(period_start_date=FIXED_NOW - timedelta(hours=1))
        self.assertIsNotNone(self.guard.enforce_own_active_shift("POSA-T-0001"))

    def test_stale_shift_is_rejected_with_config_hint(self):
        make_shift(period_start_date=FIXED_NOW - timedelta(hours=48))
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001")
        message = str(ctx.exception)
        self.assertIn("stale", message)
        self.assertIn("24 hours", message)
        self.assertIn("posa_shift_max_age_hours", message)

    # --- ownership ------------------------------------------------------

    def test_foreign_owned_shift_rejected_for_plain_user(self):
        make_shift(user=OTHER_USER)
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001")
        self.assertIn("does not belong to the current user", str(ctx.exception))

    def test_manager_bypass_accepts_foreign_owned_shift(self):
        STATE["has_role"] = True
        STATE["members"] = False  # bypass covers membership too
        make_shift(user=OTHER_USER)
        self.assertIsNotNone(self.guard.enforce_own_active_shift("POSA-T-0001"))

    def test_strict_mode_blocks_even_manager_on_foreign_shift(self):
        STATE["has_role"] = True
        make_shift(user=OTHER_USER)
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001", allow_manager=False)
        self.assertIn("does not belong to the current user", str(ctx.exception))

    def test_manager_bypass_does_not_rescue_stale_shift(self):
        STATE["has_role"] = True
        make_shift(period_start_date=FIXED_NOW - timedelta(hours=72))
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001")
        self.assertIn("stale", str(ctx.exception))

    # --- till membership --------------------------------------------------

    def test_user_no_longer_assigned_to_till_is_rejected(self):
        STATE["members"] = False
        make_shift()
        with self.assertRaises(Exception) as ctx:
            self.guard.enforce_own_active_shift("POSA-T-0001")
        self.assertIn("not currently assigned", str(ctx.exception))

    # --- companion list-filter helper ---------------------------------------

    def test_active_own_shift_filters_embed_guard_conditions(self):
        filters = self.guard.get_active_own_shift_filters()
        cutoff = self.guard.get_shift_cutoff_datetime()
        self.assertEqual(filters["user"], SESSION_USER)
        self.assertEqual(filters["status"], "Open")
        self.assertEqual(filters["docstatus"], 1)
        self.assertEqual(filters["pos_closing_shift"], ["is", "not set"])
        self.assertEqual(filters["period_start_date"], [">=", cutoff])

    def test_filters_respect_explicit_user_and_window(self):
        STATE["conf"]["posa_shift_max_age_hours"] = 5
        filters = self.guard.get_active_own_shift_filters(user="other-user@example.com")
        self.assertEqual(filters["user"], "other-user@example.com")
        expected_cutoff = FIXED_NOW - timedelta(hours=5)
        self.assertEqual(filters["period_start_date"], [">=", expected_cutoff])


if __name__ == "__main__":
    unittest.main()
