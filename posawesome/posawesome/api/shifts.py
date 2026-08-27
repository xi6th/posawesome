# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe.utils import cint, nowdate
from frappe import _
from .utilities import get_version
from .shift_guard import enforce_own_active_shift, get_active_own_shift_filters


@frappe.whitelist()
def get_opening_dialog_data():
    data = {}

    # Get only POS Profiles where current user is defined in POS Profile User table
    pos_profiles_data = frappe.db.sql(
        """
        SELECT DISTINCT p.name, p.company, p.currency 
        FROM `tabPOS Profile` p
        INNER JOIN `tabPOS Profile User` u ON u.parent = p.name
        WHERE p.disabled = 0 AND u.user = %s
        ORDER BY p.name
    """,
        frappe.session.user,
        as_dict=1,
    )

    data["pos_profiles_data"] = pos_profiles_data

    # Derive companies from accessible POS Profiles
    company_names = []
    for profile in pos_profiles_data:
        if profile.company and profile.company not in company_names:
            company_names.append(profile.company)
    data["companies"] = [{"name": c} for c in company_names]

    pos_profiles_list = []
    for i in data["pos_profiles_data"]:
        pos_profiles_list.append(i.name)

    payment_method_table = "POS Payment Method" if get_version() == 13 else "Sales Invoice Payment"
    data["payments_method"] = frappe.get_list(
        payment_method_table,
        filters={"parent": ["in", pos_profiles_list]},
        fields=["*"],
        limit_page_length=0,
        order_by="parent",
        ignore_permissions=True,
    )
    # set currency from pos profile
    for mode in data["payments_method"]:
        mode["currency"] = frappe.get_cached_value("POS Profile", mode["parent"], "currency")

    return data


@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
    balance_details = json.loads(balance_details)

    _validate_opening_eligibility(pos_profile)

    new_pos_opening = frappe.get_doc(
        {
            "doctype": "POS Opening Shift",
            "period_start_date": frappe.utils.get_datetime(),
            "posting_date": frappe.utils.getdate(),
            "user": frappe.session.user,
            "pos_profile": pos_profile,
            "company": company,
            "docstatus": 1,
        }
    )
    new_pos_opening.set("balance_details", balance_details)
    new_pos_opening.insert(ignore_permissions=True)

    data = {}
    data["pos_opening_shift"] = new_pos_opening.as_dict()
    update_opening_shift_data(data, new_pos_opening.pos_profile)
    return data


@frappe.whitelist()
def check_opening_shift(user=None, pos_profile=None, enforce=False):
    """Check if the current user has an open POS shift.

    Args:
        user: Optional user to check for (defaults to session user)
        pos_profile: Optional POS profile to filter by
        enforce: If True, throws an error when no shift is open

    Returns:
        If enforce=False: Returns dict with shift data or empty dict if none
        If enforce=True: Returns shift data dict or throws error
    """
    session_user = frappe.session.user
    if user and user != session_user:
        frappe.log_error(
            f"Rejected opening shift lookup for user '{user}' from session '{session_user}'",
            "POS Awesome Shift Lookup Security",
        )

    filters = get_active_own_shift_filters(user=session_user)

    if pos_profile:
        filters["pos_profile"] = pos_profile

    open_vouchers = frappe.db.get_all(
        "POS Opening Shift",
        filters=filters,
        fields=["name", "pos_profile"],
        order_by="period_start_date desc",
    )

    if len(open_vouchers) > 0:
        data = {}
        data["pos_opening_shift"] = frappe.get_doc("POS Opening Shift", open_vouchers[0]["name"])
        update_opening_shift_data(data, open_vouchers[0]["pos_profile"])
        return data

    # No open shift found
    if enforce:
        # Check if user can create a shift
        can_create = frappe.has_permission("POS Opening Shift", "create", user=session_user)
        frappe.throw(
            _(
                "You don't have an open POS shift. Please create an opening shift before using the POS."
            ),
            title=_("No Open Shift") if can_create else _("Contact Administrator"),
        )
    return {}


def update_opening_shift_data(data, pos_profile):
    data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile).as_dict()
    if data["pos_profile"].get("posa_language"):
        frappe.local.lang = data["pos_profile"].posa_language
    data["company"] = frappe.get_doc("Company", data["pos_profile"].company).as_dict()
    allow_negative_stock = cint(frappe.db.get_single_value("Stock Settings", "allow_negative_stock") or 0)
    data["stock_settings"] = {}
    data["stock_settings"].update({"allow_negative_stock": bool(allow_negative_stock)})


@frappe.whitelist()
def validate_pos_access(pos_profile=None):
    """Validate that the user has an open shift before accessing POS.

    This function should be called when the POS page loads to ensure
    the user has an open shift. If not, it throws an error prompting
    the user to create an opening shift.

    Args:
        pos_profile: Optional POS profile to check against

    Returns:
        Dict with shift information if user has open shift

    Raises:
        frappe.ValidationError: If no open shift exists
    """
    return check_opening_shift(user=None, pos_profile=pos_profile, enforce=True)


def _validate_opening_eligibility(pos_profile):
    """A user must be assigned to the till and hold no other open shift."""
    session_user = frappe.session.user

    if not frappe.db.exists(
        "POS Profile User",
        {"parent": pos_profile, "parenttype": "POS Profile", "user": session_user},
    ):
        frappe.throw(_("You are not assigned to POS Profile {0}.").format(pos_profile))

    existing = frappe.db.get_all(
        "POS Opening Shift",
        filters=get_active_own_shift_filters(user=session_user),
        limit=1,
    )
    if existing:
        frappe.throw(
            _("You already have an open POS shift. Close it before opening another.")
        )
