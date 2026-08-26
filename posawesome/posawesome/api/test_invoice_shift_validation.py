"""Stub-based unit tests for validate_shift in posawesome.posawesome.api.invoice.

Every import invoice.py performs is satisfied explicitly (frappe, mapper,
utils, erpnext, all invoice_processing siblings, and the shift_guard), so
the suite runs hermetically under plain python3. The shift_guard stub
replicates the real guard's rejection semantics (activity, freshness,
ownership, membership) against a fixed clock so the delegation wiring in
validate_shift is exercised end-to-end.
"""

import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timedelta

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]

FIXED_NOW = datetime(2026, 8, 26, 10, 0, 0)
SESSION_USER = "cashier@example.com"
GUARD_LOG_TITLE = "POS Awesome Shift Guard"

STATE = {"shifts": {}, "has_role": False, "members": True, "logs": [], "conf": {}}


def _make_lazy_module(name):
    """Module whose missing attributes resolve to no-op functions."""
    module = types.ModuleType(name)

    def _fallback(attr):
        return lambda *args, **kwargs: None

    module.__getattr__ = _fallback  # PEP 562
    sys.modules[name] = module
    return module


def _install_stubs():
    for existing in list(sys.modules):
        if existing == "frappe" or existing.startswith(
            ("frappe.", "erpnext", "posawesome.")
        ):
            del sys.modules[existing]

    frappe_module = types.ModuleType("frappe")
    frappe_module._ = lambda text: text
    frappe_module.throw = lambda message: (_ for _ in ()).throw(Exception(str(message)))
    frappe_module.log_error = lambda msg="", title=None: STATE["logs"].append(
        (str(msg), title)
    )
    frappe_module.session = types.SimpleNamespace(user=SESSION_USER)
    frappe_module.conf = types.SimpleNamespace(get=lambda key: STATE["conf"].get(key))
    frappe_module.has_role = lambda roles=None: STATE["has_role"]
    frappe_module.db = types.SimpleNamespace(
        exists=lambda doctype, filters=None: (
            STATE["members"] and (filters or {}).get("user") == frappe_module.session.user
        )
    )
    sys.modules["frappe"] = frappe_module

    mapper = types.ModuleType("frappe.model.mapper")
    mapper.get_mapped_doc = lambda *args, **kwargs: None
    sys.modules["frappe.model.mapper"] = mapper

    frappe_utils = types.ModuleType("frappe.utils")
    frappe_utils.add_days = lambda value, days: value
    frappe_utils.flt = float
    frappe_utils.cint = lambda value: int(value) if value not in (None, "") else 0
    frappe_utils.now_datetime = lambda: FIXED_NOW
    sys.modules["frappe.utils"] = frappe_utils

    # Heavy imports invoice.py pulls at module load — lazily no-op'd.
    _make_lazy_module("erpnext")
    _make_lazy_module("erpnext.selling")
    _make_lazy_module("erpnext.selling.doctype")
    _make_lazy_module("erpnext.selling.doctype.sales_order")
    _make_lazy_module("erpnext.selling.doctype.sales_order.sales_order")

    # shift_guard stub with REAL guard semantics (fixed clock)
    guard = types.ModuleType("posawesome.posawesome.api.shift_guard")
    GUARD_MESSAGES = {
        "required": "A valid POS Opening Shift reference is required.",
        "stale": (
            "POS Opening Shift {name} is stale: it was opened more than "
            "{hours} hours ago (config key: posa_shift_max_age_hours)."
        ),
        "inactive": "POS Opening Shift {name} is not active.",
        "foreign": "POS Opening Shift {name} does not belong to the current user.",
        "membership": "You are not currently assigned to POS Profile {profile}.",
    }

    def _stub_hours():
        return int(STATE["conf"].get("posa_shift_max_age_hours") or 0) or 24

    def _stub_enforce(ref=None, allow_manager=True):
        shift = STATE["shifts"].get(ref) if isinstance(ref, str) else ref
        if shift is None:
            raise Exception(GUARD_MESSAGES["required"])
        label = getattr(shift, "name", str(shift))
        if getattr(shift, "status", "") != "Open" or getattr(
            shift, "pos_closing_shift", None
        ):
            raise Exception(GUARD_MESSAGES["inactive"].format(name=label))
        hours = _stub_hours()
        started = getattr(shift, "period_start_date", None)
        cutoff = FIXED_NOW - timedelta(hours=hours)
        if started is not None and started < cutoff:
            raise Exception(GUARD_MESSAGES["stale"].format(name=label, hours=hours))
        bypass = bool(allow_manager and STATE["has_role"])
        if not bypass and getattr(shift, "user", None) != SESSION_USER:
            raise Exception(GUARD_MESSAGES["foreign"].format(name=label))
        profile = getattr(shift, "pos_profile", None)
        if not bypass and profile and not STATE["members"]:
            raise Exception(GUARD_MESSAGES["membership"].format(profile=profile))
        return shift

    guard.enforce_own_active_shift = _stub_enforce
    guard.is_manager = lambda: STATE["has_role"]
    guard.get_active_own_shift_filters = lambda user=None: {}
    sys.modules["posawesome.posawesome.api.shift_guard"] = guard

    # Sibling app modules invoice.py imports at top level.
    for name in (
        "posawesome.posawesome.api.utilities",
        "posawesome.posawesome.api.payments",
        "posawesome.posawesome.api.utils",
        "posawesome.posawesome.api.invoice_processing",
        "posawesome.posawesome.api.invoice_processing.utils",
        "posawesome.posawesome.api.invoice_processing.stock",
        "posawesome.posawesome.api.invoice_processing.creation",
        "posawesome.posawesome.api.invoice_processing.returns",
        "posawesome.posawesome.api.invoice_processing.payment",
        "posawesome.posawesome.api.invoice_processing.data",
        "posawesome.posawesome.doctype.delivery_charges.delivery_charges",
        "posawesome.posawesome.doctype.pos_coupon.pos_coupon",
    ):
        _make_lazy_module(name)


def _load_module():
    module_name = "posawesome.posawesome.api.invoice"
    file_path = REPO_ROOT / "posawesome" / "posawesome" / "api" / "invoice.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def make_shift(**overrides):
    data = {
        "name": "POS-OPEN-1",
        "status": "Open",
        "user": SESSION_USER,
        "pos_profile": "Main POS",
        "company": "Test Company",
        "pos_closing_shift": None,
        "period_start_date": FIXED_NOW - timedelta(hours=1),
    }
    data.update(overrides)
    shift = types.SimpleNamespace(**data)
    STATE["shifts"][data["name"]] = shift
    return shift


def make_invoice_doc(**overrides):
    data = {
        "is_pos": True,
        "posa_pos_opening_shift": "POS-OPEN-1",
        "pos_profile": "Main POS",
        "company": "Test Company",
    }
    data.update(overrides)
    return types.SimpleNamespace(**data)


class TestInvoiceShiftValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frappe_stub = None  # installed per-test via reset_state + reinstall
        _install_stubs()
        cls.invoice = _load_module()

    def setUp(self):
        STATE["shifts"] = {}
        STATE["has_role"] = False
        STATE["members"] = True
        STATE["logs"] = []
        STATE["conf"] = {}

    def test_validate_shift_allows_current_user_shift(self):
        make_shift()
        self.invoice.validate_shift(make_invoice_doc())

    def test_validate_shift_rejects_other_users_shift(self):
        make_shift(user="other@example.com")
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(make_invoice_doc())
        self.assertIn("does not belong to the current user", str(ctx.exception))

    def test_blank_shift_reference_is_now_rejected(self):
        doc = make_invoice_doc(posa_pos_opening_shift=None)
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(doc)
        self.assertIn("reference is required", str(ctx.exception))

    def test_missing_shift_attribute_is_rejected(self):
        doc = types.SimpleNamespace(is_pos=True, pos_profile="Main POS", company="TC")
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(doc)
        self.assertIn("reference is required", str(ctx.exception))

    def test_stale_shift_rejected_with_config_hint(self):
        make_shift(period_start_date=FIXED_NOW - timedelta(hours=48))
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(make_invoice_doc())
        message = str(ctx.exception)
        self.assertIn("stale", message)
        self.assertIn("posa_shift_max_age_hours", message)

    def test_closed_shift_rejected(self):
        make_shift(status="Closed")
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(make_invoice_doc())
        self.assertIn("is not active", str(ctx.exception))

    def test_profile_mismatch_still_rejected(self):
        make_shift()
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(make_invoice_doc(pos_profile="Other Till"))
        self.assertIn("not for the same POS Profile", str(ctx.exception))

    def test_company_mismatch_still_rejected(self):
        make_shift()
        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(make_invoice_doc(company="Other Co"))
        self.assertIn("not for the same company", str(ctx.exception))

    def test_non_pos_document_skips_validation_entirely(self):
        self.invoice.validate_shift(types.SimpleNamespace(is_pos=0))


if __name__ == "__main__":
    unittest.main()
