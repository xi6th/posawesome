"""Shared helpers for bulk item data retrieval used by POS Awesome APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import frappe
from erpnext.setup.utils import get_exchange_rate
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum
from frappe.utils import cint, cstr, flt, nowdate
from frappe.utils.caching import redis_cache


def _resolve_cache_ttl(ttl: Optional[int]) -> int:
    """Return a numeric TTL value while falling back to the default window."""

    return int(ttl) if ttl else 300


def _cache_wrapper(store: Dict[int, Callable[..., Any]], ttl: Optional[int], fn: Callable[..., Any]):
    """Memoize the redis cache decorator for a given TTL to avoid re-wrapping."""

    resolved_ttl = _resolve_cache_ttl(ttl)
    cached = store.get(resolved_ttl)
    if cached is None:
        cached = redis_cache(ttl=resolved_ttl)(fn)
        store[resolved_ttl] = cached
    return cached


def _normalize_codes(codes: Iterable[str]) -> Tuple[str, ...]:
    """Return a sorted tuple of unique item codes while dropping falsy values."""

    return tuple(sorted({code for code in codes if code}))


_price_cache: Dict[int, Callable[..., Any]] = {}
_bin_cache: Dict[int, Callable[..., Any]] = {}
_warehouse_bin_cache: Dict[int, Callable[..., Any]] = {}
_meta_cache: Dict[int, Callable[..., Any]] = {}
_barcode_cache: Dict[int, Callable[..., Any]] = {}
_uom_cache: Dict[int, Callable[..., Any]] = {}
_batch_cache: Dict[int, Callable[..., Any]] = {}
_serial_cache: Dict[int, Callable[..., Any]] = {}
_bom_cache: Dict[int, Callable[..., Any]] = {}


def _fetch_item_prices(
    price_list: str,
    currency: str,
    item_codes: Tuple[str, ...],
    customer: str,
    today: str,
):
    """Return raw Item Price rows honoring date, currency and customer filters."""

    if not item_codes:
        return []

    params = {
        "price_list": price_list,
        "currency": currency,
        "item_codes": item_codes,
        "today": today,
        "customer": customer or "",
    }
    query = """
        SELECT
            item_code,
            price_list_rate,
            currency,
            uom,
            customer
        FROM (
            SELECT
                item_code,
                price_list_rate,
                currency,
                uom,
                customer,
                valid_from,
                valid_upto
            FROM `tabItem Price`
            WHERE
                price_list = %(price_list)s
                AND item_code IN %(item_codes)s
                AND currency = %(currency)s
                AND (valid_from IS NULL OR valid_from <= %(today)s)
                AND IFNULL(customer, '') IN ('', %(customer)s)
                AND (valid_upto IS NULL OR valid_upto = '' OR valid_upto >= %(today)s)
        ) ip
        ORDER BY IFNULL(customer, '') ASC, valid_from ASC, valid_upto DESC
    """

    return frappe.db.sql(query, params, as_dict=True)


def get_item_prices(
    price_list: str,
    currency: str,
    item_codes: Sequence[str],
    customer: Optional[str],
    today: Optional[str] = None,
    ttl: Optional[int] = None,
):
    """Fetch Item Price data with optional redis caching based on TTL."""

    cached = _cache_wrapper(_price_cache, ttl, _fetch_item_prices)
    return cached(price_list, currency, tuple(item_codes), customer or "", today or nowdate())


def _fetch_bin_qty(warehouse: str, item_codes: Tuple[str, ...]):
    """Return stock quantities for each item, expanding warehouse groups."""

    if not item_codes or not warehouse:
        return []

    if frappe.db.get_value("Warehouse", warehouse, "is_group"):
        warehouses = frappe.db.get_descendants("Warehouse", warehouse) or []
        if not warehouses:
            return []
        bin_doctype = DocType("Bin")
        return (
            frappe.qb.from_(bin_doctype)
            .select(bin_doctype.item_code, Sum(bin_doctype.projected_qty).as_("projected_qty"))
            .where(bin_doctype.warehouse.isin(warehouses))
            .where(bin_doctype.item_code.isin(item_codes))
            .groupby(bin_doctype.item_code)
            .run(as_dict=True)
        )

    return frappe.get_all(
        "Bin",
        fields=["item_code", "actual_qty"],
        filters={"warehouse": warehouse, "item_code": ["in", item_codes]},
    )


def get_bin_qty(warehouse: Optional[str], item_codes: Sequence[str], ttl: Optional[int] = None):
    """Return cached Bin quantities when a warehouse and codes are provided."""

    cached = _cache_wrapper(_bin_cache, ttl, _fetch_bin_qty)
    return cached(warehouse, tuple(item_codes))


def _fetch_warehouse_bin_qty(company: Optional[str], item_codes: Tuple[str, ...]):
    """Return per-warehouse Bin quantities for the supplied item codes."""

    if not item_codes:
        return []

    filters = {
        "item_code": ["in", item_codes],
    }
    params: Dict[str, Any] = {"item_codes": item_codes}
    company_clause = ""
    if company:
        company_clause = "AND w.company = %(company)s"
        params["company"] = company

    query = f"""
        SELECT
            b.item_code,
            b.warehouse,
            SUM(b.actual_qty) AS actual_qty
        FROM `tabBin` b
        INNER JOIN `tabWarehouse` w ON w.name = b.warehouse
        WHERE b.item_code IN %(item_codes)s
        {company_clause}
        GROUP BY b.item_code, b.warehouse
    """
    return frappe.db.sql(query, params, as_dict=True)


def get_warehouse_bin_qty(
    company: Optional[str],
    item_codes: Sequence[str],
    ttl: Optional[int] = None,
):
    """Return cached per-warehouse Bin quantities for the supplied item codes."""

    cached = _cache_wrapper(_warehouse_bin_cache, ttl, _fetch_warehouse_bin_qty)
    return cached(company, tuple(item_codes))


def _fetch_item_meta(item_codes: Tuple[str, ...]):
    """Return Item metadata required for batch/serial checks."""

    if not item_codes:
        return []
    fields = [
        "name",
        "item_name",
        "has_batch_no",
        "has_serial_no",
        "stock_uom",
        "allow_negative_stock",
        "purchase_uom",
        "standard_rate",
    ]
    if frappe.db.has_column("Item", "default_bom"):
        fields.append("default_bom")
    if frappe.db.has_column("Item", "valuation_rate"):
        fields.append("valuation_rate")
    return frappe.get_all(
        "Item",
        fields=fields,
        filters={"name": ["in", item_codes]},
    )


def get_item_meta(item_codes: Sequence[str], ttl: Optional[int] = None):
    """Fetch Item metadata with caching support."""

    cached = _cache_wrapper(_meta_cache, ttl, _fetch_item_meta)
    return cached(tuple(item_codes))


def _fetch_barcodes(item_codes: Tuple[str, ...]):
    """Return barcode rows mapped to the parent item."""

    if not item_codes:
        return []
    return frappe.get_all(
        "Item Barcode",
        fields=["parent", "barcode", "posa_uom"],
        filters={"parent": ["in", item_codes]},
    )


def get_barcodes(item_codes: Sequence[str], ttl: Optional[int] = None):
    """Fetch Item Barcode entries while respecting the configured TTL."""

    cached = _cache_wrapper(_barcode_cache, ttl, _fetch_barcodes)
    return cached(tuple(item_codes))


def _fetch_uoms(item_codes: Tuple[str, ...]):
    """Return UOM conversion rows for the supplied item codes."""

    if not item_codes:
        return []
    return frappe.get_all(
        "UOM Conversion Detail",
        fields=["parent", "uom", "conversion_factor"],
        filters={"parent": ["in", item_codes]},
    )


def get_uoms(item_codes: Sequence[str], ttl: Optional[int] = None):
    """Fetch UOM Conversion Detail rows with redis caching support."""

    cached = _cache_wrapper(_uom_cache, ttl, _fetch_uoms)
    return cached(tuple(item_codes))


def _normalize_warehouses(warehouse: Optional[str]) -> Tuple[str, ...]:
    """Return a tuple of concrete warehouses for the provided warehouse or group."""

    if not warehouse:
        return tuple()

    if frappe.db.get_value("Warehouse", warehouse, "is_group"):
        descendants = frappe.db.get_descendants("Warehouse", warehouse) or []
        if not descendants:
            return tuple()
        return tuple(sorted({w for w in descendants if w}))

    return (warehouse,)


def _fetch_batches(warehouse: str, item_codes: Tuple[str, ...]):
    """Collect batch information (including expired entries) for the given warehouse."""

    if not item_codes or not warehouse:
        return []

    warehouses = _normalize_warehouses(warehouse)
    if not warehouses:
        return []

    batch_docs = frappe.get_all(
        "Batch",
        filters={"item": ["in", item_codes], "disabled": 0},
        fields=[
            "name as batch_no",
            "item as item_code",
            "expiry_date",
            "manufacturing_date",
            "posa_batch_price",
        ],
        order_by="expiry_date asc, creation asc",
    )
    if not batch_docs:
        return []

    qty_map: Dict[Tuple[str, str], float] = {}

    # Primary source of batch quantities: Serial and Batch Entry records linked to SLEs.
    bundle_rows = frappe.db.sql(
        """
        SELECT
            sbb.item_code,
            sbe.batch_no,
            SUM(sbe.qty) AS qty
        FROM `tabSerial and Batch Entry` sbe
        INNER JOIN `tabSerial and Batch Bundle` sbb
            ON sbb.name = sbe.parent
        INNER JOIN `tabStock Ledger Entry` sle
            ON sle.serial_and_batch_bundle = sbb.name
        WHERE
            sbe.batch_no IS NOT NULL
            AND sbb.item_code IN %(item_codes)s
            AND sbb.warehouse IN %(warehouses)s
            AND sle.is_cancelled = 0
        GROUP BY sbb.item_code, sbe.batch_no
        """,
        {"item_codes": item_codes, "warehouses": warehouses},
        as_dict=True,
    )

    for row in bundle_rows:
        if not row.batch_no:
            continue
        key = (row.item_code, row.batch_no)
        qty_map[key] = qty_map.get(key, 0) + flt(row.qty)

    # Backward compatibility for ledgers created before Serial and Batch Bundle existed.
    legacy_rows = frappe.db.sql(
        """
        SELECT
            item_code,
            batch_no,
            SUM(actual_qty) AS qty
        FROM `tabStock Ledger Entry`
        WHERE
            serial_and_batch_bundle IS NULL
            AND warehouse IN %(warehouses)s
            AND item_code IN %(item_codes)s
            AND batch_no IS NOT NULL
            AND is_cancelled = 0
        GROUP BY item_code, batch_no
        """,
        {"item_codes": item_codes, "warehouses": warehouses},
        as_dict=True,
    )

    for row in legacy_rows:
        if not row.batch_no:
            continue
        key = (row.item_code, row.batch_no)
        qty_map[key] = qty_map.get(key, 0) + flt(row.qty)

    rows = []
    for doc in batch_docs:
        qty = qty_map.get((doc.item_code, doc.batch_no), 0)
        rows.append(
            frappe._dict(
                {
                    "item_code": doc.item_code,
                    "batch_no": doc.batch_no,
                    "batch_qty": qty,
                    "expiry_date": doc.expiry_date,
                    "batch_price": doc.posa_batch_price,
                    "manufacturing_date": doc.manufacturing_date,
                }
            )
        )

    return rows


def get_batches(warehouse: Optional[str], item_codes: Sequence[str], ttl: Optional[int] = None):
    """Fetch batch availability constrained to the provided warehouse."""

    cached = _cache_wrapper(_batch_cache, ttl, _fetch_batches)
    return cached(warehouse, tuple(item_codes))


def _fetch_serials(warehouse: str, item_codes: Tuple[str, ...]):
    """Return active serial numbers scoped to a warehouse."""

    if not item_codes or not warehouse:
        return []
    return frappe.get_all(
        "Serial No",
        fields=["name as serial_no", "item_code", "batch_no"],
        filters={
            "item_code": ["in", item_codes],
            "warehouse": warehouse,
            "status": "Active",
        },
    )


def get_serials(warehouse: Optional[str], item_codes: Sequence[str], ttl: Optional[int] = None):
    """Fetch serial number data while honouring the redis cache TTL."""

    cached = _cache_wrapper(_serial_cache, ttl, _fetch_serials)
    return cached(warehouse, tuple(item_codes))


def _resolve_bom_cost_fields() -> List[str]:
    fields = ["name", "item", "is_active", "is_default", "docstatus", "modified", "quantity"]
    for fieldname in ("base_total_cost", "total_cost", "raw_material_cost", "operating_cost"):
        if frappe.db.has_column("BOM", fieldname):
            fields.append(fieldname)
    return fields


def _extract_bom_unit_cost(row: frappe._dict) -> Optional[float]:
    quantity = flt(row.get("quantity")) or 1
    for fieldname in ("base_total_cost", "total_cost"):
        value = row.get(fieldname)
        if value is not None:
            return flt(value) / quantity

    raw_material_cost = row.get("raw_material_cost")
    operating_cost = row.get("operating_cost")
    if raw_material_cost is not None or operating_cost is not None:
        return (flt(raw_material_cost) + flt(operating_cost)) / quantity
    return None


def _fetch_bom_costs(meta_rows: Tuple[Tuple[str, Optional[str]], ...]):
    if not meta_rows:
        return {}

    resolved: Dict[str, Dict[str, Any]] = {}
    bom_fields = _resolve_bom_cost_fields()
    default_boms = tuple(sorted({default_bom for _, default_bom in meta_rows if default_bom}))

    if default_boms:
        default_rows = frappe.get_all(
            "BOM",
            filters={"name": ["in", default_boms]},
            fields=bom_fields,
        )
        for row in default_rows:
            item_code = row.get("item")
            if not item_code or not cint(row.get("is_active")) or cint(row.get("docstatus")) != 1:
                continue
            unit_cost = _extract_bom_unit_cost(row)
            if unit_cost is None:
                continue
            resolved[item_code] = {
                "rate": unit_cost,
                "bom": row.get("name"),
                "source": "bom",
            }

    unresolved_items = tuple(
        sorted(
            {
                item_code
                for item_code, _default_bom in meta_rows
                if item_code and item_code not in resolved
            }
        )
    )
    if unresolved_items:
        fallback_rows = frappe.get_all(
            "BOM",
            filters={"item": ["in", unresolved_items], "is_active": 1, "docstatus": 1},
            fields=bom_fields,
            order_by="item asc, is_default desc, modified desc",
        )
        for row in fallback_rows:
            item_code = row.get("item")
            if not item_code or item_code in resolved:
                continue
            unit_cost = _extract_bom_unit_cost(row)
            if unit_cost is None:
                continue
            resolved[item_code] = {
                "rate": unit_cost,
                "bom": row.get("name"),
                "source": "bom",
            }

    return resolved


def get_bom_costs(meta_rows: Sequence[frappe._dict], ttl: Optional[int] = None):
    normalized_rows = tuple(
        (str(row.get("name") or ""), row.get("default_bom"))
        for row in (meta_rows or [])
        if row.get("name")
    )
    cached = _cache_wrapper(_bom_cache, ttl, _fetch_bom_costs)
    return cached(normalized_rows)


@dataclass(frozen=True)
class ItemLookupData:
    price_map: Dict[str, Dict[str, frappe._dict]]
    stock_map: Dict[str, float]
    warehouse_map: Dict[str, str]
    warehouse_qty_map: Dict[str, Dict[str, float]]
    meta_map: Dict[str, frappe._dict]
    uom_map: Dict[str, List[Dict[str, Any]]]
    barcode_map: Dict[str, List[Dict[str, Any]]]
    batch_map: Dict[str, Dict[str, List[Dict[str, Any]]]]
    serial_map: Dict[str, Dict[str, List[Dict[str, Any]]]]
    bom_map: Dict[str, Dict[str, Any]]


def _select_stock_warehouse(
    preferred_warehouse: Optional[str],
    warehouse_qty_map: Dict[str, float],
) -> Tuple[str, float]:
    """Pick the best warehouse for an item based on available qty."""

    normalized_preferred = cstr(preferred_warehouse or "").strip()
    if normalized_preferred and normalized_preferred in warehouse_qty_map:
        preferred_qty = flt(warehouse_qty_map.get(normalized_preferred))
        if preferred_qty > 0:
            return normalized_preferred, preferred_qty

    positive_warehouses = [
        (warehouse, flt(qty))
        for warehouse, qty in warehouse_qty_map.items()
        if flt(qty) > 0
    ]
    if positive_warehouses:
        positive_warehouses.sort(key=lambda row: (-row[1], row[0]))
        return positive_warehouses[0]

    if normalized_preferred and normalized_preferred in warehouse_qty_map:
        return normalized_preferred, flt(warehouse_qty_map.get(normalized_preferred))

    if warehouse_qty_map:
        warehouse, qty = max(warehouse_qty_map.items(), key=lambda row: flt(row[1]))
        return warehouse, flt(qty)

    return normalized_preferred, 0.0


def _select_price(
    price_rows: Dict[str, frappe._dict],
    requested_uom: Optional[str],
    stock_uom: Optional[str],
) -> frappe._dict:
    """Select the most appropriate price row for the requested item context."""

    if not price_rows:
        return frappe._dict()

    if requested_uom and requested_uom in price_rows:
        return price_rows[requested_uom]

    if stock_uom and stock_uom in price_rows:
        return price_rows[stock_uom]

    if "None" in price_rows:
        return price_rows["None"]

    # fall back to first available rate
    return next(iter(price_rows.values()), frappe._dict())


def _ensure_stock_uom(uoms: List[Dict[str, Any]], stock_uom: Optional[str]) -> List[Dict[str, Any]]:
    """Make sure the stock UOM is always present in the UOM listing."""

    uoms = list(uoms or [])
    if stock_uom and not any(u.get("uom") == stock_uom for u in uoms):
        uoms.append({"uom": stock_uom, "conversion_factor": 1.0})
    return uoms


def merge_item_row(
    item: Dict[str, Any],
    lookup_data: ItemLookupData,
    price_list_currency: Optional[str],
    exchange_rate: float,
) -> Dict[str, Any]:
    """Merge lookup data into a POS item row for downstream consumption."""

    item_code = item.get("item_code")
    if not item_code:
        return dict(item)

    meta = lookup_data.meta_map.get(item_code, frappe._dict())
    uoms = _ensure_stock_uom(lookup_data.uom_map.get(item_code, []), meta.get("stock_uom"))
    price_row = _select_price(
        lookup_data.price_map.get(item_code, {}), item.get("uom"), meta.get("stock_uom")
    )
    price_currency = price_row.get("currency") if price_row else None

    warehouse_qty_map = lookup_data.warehouse_qty_map.get(item_code, {})
    requested_warehouse = cstr(item.get("warehouse") or "").strip()
    chosen_warehouse = requested_warehouse
    requested_qty = flt(warehouse_qty_map.get(requested_warehouse, 0)) if requested_warehouse else 0
    if not requested_warehouse or requested_qty <= 0:
        chosen_warehouse = lookup_data.warehouse_map.get(item_code) or requested_warehouse

    batch_rows = (
        lookup_data.batch_map.get(item_code, {}).get(chosen_warehouse, [])
        if chosen_warehouse
        else []
    )
    actual_qty = flt(warehouse_qty_map.get(chosen_warehouse, 0)) if chosen_warehouse else 0
    if meta.get("has_batch_no") and batch_rows:
        actual_qty = sum(
            flt(batch.get("batch_qty"))
            for batch in batch_rows
            if not batch.get("is_expired")
        )

    row = dict(item)
    row.update(
        {
            "warehouse": chosen_warehouse or item.get("warehouse"),
            "item_uoms": uoms,
            "item_barcode": lookup_data.barcode_map.get(item_code, []),
            "actual_qty": actual_qty,
            "has_batch_no": meta.get("has_batch_no"),
            "has_serial_no": meta.get("has_serial_no"),
            "allow_negative_stock": meta.get("allow_negative_stock"),
            "purchase_uom": meta.get("purchase_uom"),
            "standard_rate": meta.get("standard_rate"),
            "valuation_rate": meta.get("valuation_rate"),
            "default_bom": meta.get("default_bom"),
            "batch_no_data": batch_rows,
            "serial_no_data": lookup_data.serial_map.get(item_code, {}).get(chosen_warehouse, [])
            if chosen_warehouse
            else [],
            "rate": price_row.get("price_list_rate") if price_row else 0,
            "price_list_rate": price_row.get("price_list_rate") if price_row else 0,
            "currency": price_currency or price_list_currency,
            "price_list_currency": price_list_currency,
            "plc_conversion_rate": exchange_rate,
            "conversion_rate": exchange_rate,
        }
    )
    bom_cost = lookup_data.bom_map.get(item_code)
    if bom_cost:
        row["manufacturing_cost"] = bom_cost.get("rate")
        row["manufacturing_cost_source"] = bom_cost.get("source")
        row["manufacturing_bom"] = bom_cost.get("bom")
    if not row.get("item_name") and meta.get("item_name"):
        row["item_name"] = meta.get("item_name")
    return row


class ItemDetailAggregator:
    """Aggregate item lookup data and build detail rows."""

    def __init__(
        self,
        pos_profile: Dict[str, Any],
        price_list: Optional[str] = None,
        customer: Optional[str] = None,
    ) -> None:
        self.pos_profile = pos_profile
        self.customer = customer
        self.price_list = price_list or pos_profile.get("selling_price_list")
        self.cache_ttl = self._resolve_ttl()
        self.today = nowdate()
        self.warehouse = pos_profile.get("warehouse")
        self.price_list_currency = self._determine_price_list_currency()
        self.exchange_rate = self._compute_exchange_rate()

    def _resolve_ttl(self) -> Optional[int]:
        """Convert the POS profile cache duration to seconds."""

        ttl = self.pos_profile.get("posa_server_cache_duration")
        if not ttl:
            return None
        try:
            return int(ttl) * 60
        except Exception:
            return None

    def _determine_price_list_currency(self) -> Optional[str]:
        """Resolve the currency backing the active selling price list."""

        if not self.price_list:
            return self.pos_profile.get("currency")
        return frappe.db.get_value("Price List", self.price_list, "currency") or self.pos_profile.get(
            "currency"
        )

    def _compute_exchange_rate(self) -> float:
        """Compute the price list to company currency exchange rate."""

        company = self.pos_profile.get("company")
        allow_multi_currency = self.pos_profile.get("posa_allow_multi_currency") or 0
        company_currency = frappe.db.get_value("Company", company, "default_currency") if company else None
        price_list_currency = self.price_list_currency or self.pos_profile.get("currency")

        if (
            company_currency
            and price_list_currency
            and price_list_currency != company_currency
            and allow_multi_currency
        ):
            try:
                return get_exchange_rate(price_list_currency, company_currency, self.today)
            except Exception:
                frappe.log_error(
                    f"Missing exchange rate from {price_list_currency} to {company_currency}",
                    "POS Awesome",
                )
        return 1

    def _prepare_lookup(self, item_codes: Iterable[str]) -> ItemLookupData:
        """Collect and organise lookup rows for the provided item codes."""

        item_codes_tuple = _normalize_codes(item_codes)
        if not item_codes_tuple:
            return ItemLookupData({}, {}, {}, {}, {}, {}, {}, {}, {}, {})

        use_cache = bool(self.pos_profile.get("posa_use_server_cache"))

        price_rows = []
        if self.price_list:
            if use_cache:
                price_rows = get_item_prices(
                    self.price_list,
                    self.price_list_currency or self.pos_profile.get("currency"),
                    item_codes_tuple,
                    self.customer,
                    today=self.today,
                    ttl=self.cache_ttl,
                )
            else:
                price_rows = _fetch_item_prices(
                    self.price_list,
                    self.price_list_currency or self.pos_profile.get("currency"),
                    item_codes_tuple,
                    self.customer or "",
                    self.today,
                )

        # Stock, metadata, UOM and barcode data are reused both for batches and the
        # final merged item rows, so collect them up front.
        warehouse_qty_rows = (
            get_warehouse_bin_qty(self.pos_profile.get("company"), item_codes_tuple, ttl=self.cache_ttl)
            if use_cache
            else _fetch_warehouse_bin_qty(self.pos_profile.get("company"), item_codes_tuple)
        )
        if use_cache:
            meta_rows = get_item_meta(item_codes_tuple, ttl=self.cache_ttl)
            uom_rows = get_uoms(item_codes_tuple, ttl=self.cache_ttl)
            barcode_rows = get_barcodes(item_codes_tuple, ttl=self.cache_ttl)
            bom_map = get_bom_costs(meta_rows, ttl=self.cache_ttl)
        else:
            meta_rows = _fetch_item_meta(item_codes_tuple)
            uom_rows = _fetch_uoms(item_codes_tuple)
            barcode_rows = _fetch_barcodes(item_codes_tuple)
            bom_map = _fetch_bom_costs(
                tuple((str(row.get("name") or ""), row.get("default_bom")) for row in meta_rows if row.get("name"))
            )

        price_map: Dict[str, Dict[str, frappe._dict]] = {}
        for row in price_rows:
            price_map.setdefault(row.item_code, {})[row.get("uom") or "None"] = row

        meta_map = {row.name: row for row in meta_rows}
        warehouse_qty_map: Dict[str, Dict[str, float]] = {}
        resolved_warehouse_map: Dict[str, str] = {}
        stock_map: Dict[str, float] = {}
        for row in warehouse_qty_rows:
            item_code = row.get("item_code")
            warehouse = row.get("warehouse")
            if not item_code or not warehouse:
                continue
            qty_map = warehouse_qty_map.setdefault(item_code, {})
            qty_map[warehouse] = flt(row.get("actual_qty"))

        for item_code in item_codes_tuple:
            preferred_warehouse = self.warehouse
            chosen_warehouse, chosen_qty = _select_stock_warehouse(
                preferred_warehouse,
                warehouse_qty_map.get(item_code, {}),
            )
            resolved_warehouse_map[item_code] = chosen_warehouse
            stock_map[item_code] = chosen_qty

        batch_items_by_warehouse: Dict[str, List[str]] = {}
        serial_items_by_warehouse: Dict[str, List[str]] = {}
        for item_code, meta in meta_map.items():
            resolved_warehouse = resolved_warehouse_map.get(item_code)
            if not resolved_warehouse:
                continue
            if meta.get("has_batch_no"):
                batch_items_by_warehouse.setdefault(resolved_warehouse, []).append(item_code)
            if meta.get("has_serial_no"):
                serial_items_by_warehouse.setdefault(resolved_warehouse, []).append(item_code)

        batch_map: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
        serial_map: Dict[str, Dict[str, List[Dict[str, object]]]] = {}

        for warehouse, codes in batch_items_by_warehouse.items():
            codes_tuple = _normalize_codes(codes)
            if not codes_tuple:
                continue
            rows = (
                get_batches(warehouse, codes_tuple, ttl=self.cache_ttl)
                if use_cache
                else _fetch_batches(warehouse, codes_tuple)
            )
            for row in rows:
                is_expired = bool(row.expiry_date and str(row.expiry_date) <= str(self.today))
                if is_expired:
                    continue
                batch_map.setdefault(row.item_code, {}).setdefault(warehouse, []).append(
                    {
                        "batch_no": row.batch_no,
                        "batch_qty": row.batch_qty,
                        "expiry_date": row.expiry_date,
                        "batch_price": row.batch_price,
                        "manufacturing_date": row.manufacturing_date,
                        "is_expired": is_expired,
                    }
                )

        for warehouse, codes in serial_items_by_warehouse.items():
            codes_tuple = _normalize_codes(codes)
            if not codes_tuple:
                continue
            rows = (
                get_serials(warehouse, codes_tuple, ttl=self.cache_ttl)
                if use_cache
                else _fetch_serials(warehouse, codes_tuple)
            )
            for row in rows:
                serial_map.setdefault(row.item_code, {}).setdefault(warehouse, []).append(
                    {"serial_no": row.serial_no, "batch_no": row.batch_no}
                )

        uom_map: Dict[str, List[Dict[str, object]]] = {}
        for row in uom_rows:
            uom_map.setdefault(row.parent, []).append(
                {"uom": row.uom, "conversion_factor": row.conversion_factor}
            )

        barcode_map: Dict[str, List[Dict[str, object]]] = {}
        for row in barcode_rows:
            barcode_map.setdefault(row.parent, []).append(
                {"barcode": row.barcode, "posa_uom": row.posa_uom}
            )

        return ItemLookupData(
            price_map=price_map,
            stock_map=stock_map,
            warehouse_map=resolved_warehouse_map,
            warehouse_qty_map=warehouse_qty_map,
            meta_map=meta_map,
            uom_map=uom_map,
            barcode_map=barcode_map,
            batch_map=batch_map,
            serial_map=serial_map,
            bom_map=bom_map,
        )

    def build_details(self, items_data: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
        """Produce enriched item detail rows for all non-template items."""

        item_codes = [
            item.get("item_code")
            for item in items_data
            if item.get("item_code") and not item.get("has_variants")
        ]
        lookup_data = self._prepare_lookup(item_codes)

        result = []
        for item in items_data:
            if not item.get("item_code") or item.get("has_variants"):
                continue
            result.append(
                merge_item_row(
                    item,
                    lookup_data,
                    self.price_list_currency or self.pos_profile.get("currency"),
                    self.exchange_rate,
                )
            )
        return result


__all__ = [
    "ItemDetailAggregator",
    "ItemLookupData",
    "get_item_prices",
    "get_bin_qty",
    "get_item_meta",
    "get_barcodes",
    "get_uoms",
    "get_batches",
    "get_serials",
    "get_bom_costs",
    "merge_item_row",
]
