import importlib.util
import pathlib
import sys
import types
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def _install_stubs():
    frappe_module = types.ModuleType("frappe")
    frappe_module._ = lambda text: text
    frappe_module.throw = lambda message: (_ for _ in ()).throw(Exception(message))
    frappe_module.get_cached_doc = lambda *args, **kwargs: None
    frappe_module.get_doc = lambda *args, **kwargs: None
    frappe_module.get_value = lambda *args, **kwargs: None
    frappe_module.get_all = lambda *args, **kwargs: []
    frappe_module.session = types.SimpleNamespace(user="cashier@example.com")
    sys.modules["frappe"] = frappe_module

    frappe_mapper = types.ModuleType("frappe.model.mapper")
    frappe_mapper.get_mapped_doc = lambda *args, **kwargs: None
    sys.modules["frappe.model.mapper"] = frappe_mapper

    frappe_utils = types.ModuleType("frappe.utils")
    frappe_utils.add_days = lambda value, days: value
    frappe_utils.flt = float
    sys.modules["frappe.utils"] = frappe_utils

    utilities_module = types.ModuleType("posawesome.posawesome.api.utilities")
    utilities_module.get_company_domain = lambda *args, **kwargs: None
    sys.modules["posawesome.posawesome.api.utilities"] = utilities_module

    payments_module = types.ModuleType("posawesome.posawesome.api.payments")
    payments_module.get_posawesome_credit_redeem_remark = lambda *args, **kwargs: ""
    sys.modules["posawesome.posawesome.api.payments"] = payments_module

    delivery_charges_module = types.ModuleType(
        "posawesome.posawesome.doctype.delivery_charges.delivery_charges"
    )
    delivery_charges_module.get_applicable_delivery_charges = lambda *args, **kwargs: None
    sys.modules[
        "posawesome.posawesome.doctype.delivery_charges.delivery_charges"
    ] = delivery_charges_module

    coupon_module = types.ModuleType("posawesome.posawesome.doctype.pos_coupon.pos_coupon")
    coupon_module.update_coupon_code_count = lambda *args, **kwargs: None
    sys.modules["posawesome.posawesome.doctype.pos_coupon.pos_coupon"] = coupon_module


def _load_module():
    module_name = "posawesome.posawesome.api.invoice"
    file_path = REPO_ROOT / "posawesome" / "posawesome" / "api" / "invoice.py"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class TestInvoiceShiftValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _install_stubs()
        cls.invoice = _load_module()

    def test_validate_shift_allows_current_user_shift(self):
        shift = types.SimpleNamespace(
            name="POS-OPEN-1",
            status="Open",
            user="cashier@example.com",
            pos_profile="Main POS",
            company="Test Company",
        )
        self.invoice.frappe.get_cached_doc = lambda *args, **kwargs: shift

        doc = types.SimpleNamespace(
            posa_pos_opening_shift="POS-OPEN-1",
            pos_profile="Main POS",
            company="Test Company",
            is_pos=True,
        )

        self.invoice.validate_shift(doc)

    def test_validate_shift_rejects_other_users_shift(self):
        shift = types.SimpleNamespace(
            name="POS-OPEN-2",
            status="Open",
            user="other@example.com",
            pos_profile="Main POS",
            company="Test Company",
        )
        self.invoice.frappe.get_cached_doc = lambda *args, **kwargs: shift

        doc = types.SimpleNamespace(
            posa_pos_opening_shift="POS-OPEN-2",
            pos_profile="Main POS",
            company="Test Company",
            is_pos=True,
        )

        with self.assertRaises(Exception) as ctx:
            self.invoice.validate_shift(doc)

        self.assertIn("does not belong to the current user", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
