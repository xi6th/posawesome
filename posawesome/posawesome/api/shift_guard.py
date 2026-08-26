# Copyright (c) 2026, BIPC / POS Awesome contributors
# For license information, please see license.txt

"""Central security guard for POS Opening Shift references.

Every consumer of a ``POS Opening Shift`` reference must route through
``enforce_own_active_shift`` so the four trust conditions are enforced
uniformly instead of being re-implemented per endpoint:

1. Reference resolves to an existing, Open shift not linked to a closing.
2. Ownership: the shift belongs to the current session user.
3. Till-membership: the session user is still assigned to the shift's POS Profile.
4. Freshness: the shift started within the configured window
   (site_config key ``posa_shift_max_age_hours``, default 24).

Manager bypass policy: when *allow_manager* is true (default) System
Manager/Administrator sessions skip ONLY conditions 2 and 3 above
(ownership/membership) — never activity-status or freshness — so even
administrators cannot act on dead sessions through guarded endpoints.
"""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

DEFAULT_FRESHNESS_HOURS = 24

SECURITY_LOG_TITLE = "POS Awesome Shift Guard"


def get_shift_freshness_hours():
    """Freshness window in hours, tunable via site_config.json without redeploy."""
    conf = getattr(frappe, "conf", None)
    hours = cint(conf.get("posa_shift_max_age_hours")) if conf else 0
    return hours or DEFAULT_FRESHNESS_HOURS


def get_shift_cutoff_datetime():
    """Shifts with period_start_date earlier than this are considered stale."""
    return now_datetime() - timedelta(hours=get_shift_freshness_hours())


def is_manager():
    # frappe.get_roles() is the supported roles API in this Frappe version;
    # (module-level frappe.has_role does not exist — the copy in
    # cash_movement/permissions.py carries the same latent bug)
    roles = frappe.get_roles()
    return bool(roles and ("System Manager" in roles or "Administrator" in roles))


def _reject(message, detail=""):
    detail_suffix = f" | {detail}" if detail else ""
    try:
        frappe.log_error(
            f"{message} | user={getattr(frappe.session, 'user', None)}{detail_suffix}",
            SECURITY_LOG_TITLE,
        )
    except Exception:
        # A broken error-log sink must never mask the rejection itself
        pass
    frappe.throw(_(message))


def _resolve_shift(ref):
    """Accept a shift name (string) or an already-loaded document object."""
    if hasattr(ref, "name") and not isinstance(ref, str):
        return ref
    name = ref.get("name") if isinstance(ref, dict) else ref
    if not name:
        return None
    try:
        return frappe.get_cached_doc("POS Opening Shift", name)
    except Exception:
        return None


def enforce_own_active_shift(pos_opening_shift=None, allow_manager=True):
    """Validate a shift reference against all four trust conditions.

    Args:
        pos_opening_shift: shift name, loaded document/dict, or None (rejects).
        allow_manager: let System Manager/Administrator waive ownership and
            till-membership checks. Activity and freshness still apply.

    Returns:
        The validated POS Opening Shift document on success.

    Raises:
        frappe.ValidationError / frappe.PermissionError on every failed
        condition; each rejection is written to the security error-log.
    """
    shift = _resolve_shift(pos_opening_shift)
    if shift is None:
        _reject(
            "A valid POS Opening Shift reference is required.",
            f"requested={pos_opening_shift!r}",
        )

    label = getattr(shift, "name", str(shift))

    if getattr(shift, "status", "") != "Open" or getattr(shift, "pos_closing_shift", None):
        _reject(
            f"POS Opening Shift {label} is not active.",
            f"status={getattr(shift, 'status', None)}, "
            f"closing={getattr(shift, 'pos_closing_shift', None)}",
        )

    hours = get_shift_freshness_hours()
    started = getattr(shift, "period_start_date", None)
    if started is not None and started < get_shift_cutoff_datetime():
        _reject(
            f"POS Opening Shift {label} is stale: it was opened more than "
            f"{hours} hours ago (config key: posa_shift_max_age_hours).",
            f"period_start_date={started}",
        )

    bypass = bool(allow_manager and is_manager())

    if not bypass and getattr(shift, "user", None) != frappe.session.user:
        _reject(
            f"POS Opening Shift {label} does not belong to the current user.",
            f"shift_user={getattr(shift, 'user', None)}",
        )

    profile = getattr(shift, "pos_profile", None)
    if not bypass and profile:
        assigned = frappe.db.exists(
            "POS Profile User",
            {"parent": profile, "parenttype": "POS Profile", "user": frappe.session.user},
        )
        if not assigned:
            _reject(
                f"You are not currently assigned to POS Profile {profile}.",
                f"shift={label}",
            )

    return shift


def get_active_own_shift_filters(user=None):
    """List-filter equivalent of the guard for resume/list queries.

    Applying these filters embeds ownership + open-status + not-closed +
    freshness directly into the query, mirroring enforce_own_active_shift.
    """
    return {
        "user": user or frappe.session.user,
        "status": "Open",
        "docstatus": 1,
        "pos_closing_shift": ["is", "not set"],
        "period_start_date": [">=", get_shift_cutoff_datetime()],
    }
