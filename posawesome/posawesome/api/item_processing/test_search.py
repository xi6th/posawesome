import importlib.util
import pathlib
import sys
import types
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


class AttrDict(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def _install_stubs():
	frappe_module = types.ModuleType("frappe")
	frappe_module._ = lambda text: text
	frappe_module.as_json = lambda value: value
	frappe_module.throw = lambda message: (_ for _ in ()).throw(Exception(message))
	frappe_module.whitelist = lambda *args, **kwargs: (lambda fn: fn)
	frappe_module.validate_and_sanitize_search_inputs = lambda fn: fn
	frappe_module.get_all = lambda *args, **kwargs: []
	frappe_module.get_cached_doc = lambda *args, **kwargs: AttrDict({})
	frappe_module.get_cached_value = lambda *args, **kwargs: None
	frappe_module.get_value = lambda *args, **kwargs: None
	frappe_module.qb = types.SimpleNamespace(from_=lambda *args, **kwargs: None)
	frappe_module.db = types.SimpleNamespace(get_value=lambda *args, **kwargs: None)
	sys.modules["frappe"] = frappe_module

	frappe_utils = types.ModuleType("frappe.utils")
	frappe_utils.cint = int
	frappe_utils.cstr = str
	frappe_utils.get_datetime = lambda value: value
	sys.modules["frappe.utils"] = frappe_utils

	frappe_cache = types.ModuleType("frappe.utils.caching")
	frappe_cache.redis_cache = lambda ttl=None: (lambda fn: fn)
	sys.modules["frappe.utils.caching"] = frappe_cache

	item_fetchers_module = types.ModuleType("posawesome.posawesome.api.item_fetchers")
	item_fetchers_module.ItemDetailAggregator = object
	sys.modules["posawesome.posawesome.api.item_fetchers"] = item_fetchers_module

	utils_module = types.ModuleType("posawesome.posawesome.api.utils")
	utils_module.HAS_VARIANTS_EXCLUSION = {"has_variants": 0}
	utils_module.expand_item_groups = lambda groups: list(groups or [])
	utils_module.get_active_pos_profile = lambda user=None: None
	utils_module.get_item_groups = lambda pos_profile: []
	utils_module._ensure_pos_profile = lambda pos_profile: (pos_profile, "{}")
	utils_module.log_perf_event = lambda *args, **kwargs: None
	sys.modules["posawesome.posawesome.api.utils"] = utils_module

	barcode_module = types.ModuleType("posawesome.posawesome.api.item_processing.barcode")
	barcode_module.search_serial_or_batch_or_barcode_number = lambda *args, **kwargs: {}
	sys.modules["posawesome.posawesome.api.item_processing.barcode"] = barcode_module

	details_module = types.ModuleType("posawesome.posawesome.api.item_processing.details")
	details_module.get_items_details = lambda *args, **kwargs: []
	sys.modules["posawesome.posawesome.api.item_processing.details"] = details_module

	package_paths = {
		"posawesome": REPO_ROOT / "posawesome",
		"posawesome.posawesome": REPO_ROOT / "posawesome" / "posawesome",
		"posawesome.posawesome.api": REPO_ROOT / "posawesome" / "posawesome" / "api",
		"posawesome.posawesome.api.item_processing": REPO_ROOT / "posawesome" / "posawesome" / "api" / "item_processing",
	}
	for name, path in package_paths.items():
		module = types.ModuleType(name)
		module.__path__ = [str(path)]
		sys.modules[name] = module


def _load_module():
	module_name = "posawesome.posawesome.api.item_processing.search"
	file_path = REPO_ROOT / "posawesome" / "posawesome" / "api" / "item_processing" / "search.py"
	spec = importlib.util.spec_from_file_location(module_name, file_path)
	module = importlib.util.module_from_spec(spec)
	sys.modules[module_name] = module
	spec.loader.exec_module(module)
	return module


class TestItemVisibilityToggle(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		_install_stubs()
		cls.module = _load_module()

	def _make_plan(self, hide_unavailable_items):
		return self.module.SearchPlan(
			filters={},
			or_filters=[],
			fields=[],
			limit_page_length=None,
			limit_start=None,
			order_by="item_name asc",
			page_size=100,
			initial_page_start=0,
			item_code_for_search=None,
			search_words=[],
			normalized_search_value="",
			word_filter_active=False,
			include_description=False,
			include_image=False,
			posa_display_items_in_stock=hide_unavailable_items,
			posa_show_template_items=False,
		)

	def test_keeps_zero_stock_items_when_toggle_is_disabled(self):
		row = self.module._shape_item_row(
			{"item_code": "ITEM-001", "is_stock_item": 1, "has_variants": 0},
			{"actual_qty": 0},
			self._make_plan(False),
		)

		self.assertIsNotNone(row)
		self.assertEqual(row["item_code"], "ITEM-001")

	def test_hides_zero_stock_stock_items_when_toggle_is_enabled(self):
		row = self.module._shape_item_row(
			{"item_code": "ITEM-002", "is_stock_item": 1, "has_variants": 0},
			{"actual_qty": 0},
			self._make_plan(True),
		)

		self.assertIsNone(row)

	def test_keeps_non_stock_items_visible_when_toggle_is_enabled(self):
		row = self.module._shape_item_row(
			{"item_code": "ITEM-003", "is_stock_item": 0, "has_variants": 0},
			{"actual_qty": 0},
			self._make_plan(True),
		)

		self.assertIsNotNone(row)
		self.assertEqual(row["item_code"], "ITEM-003")


if __name__ == "__main__":
	unittest.main()
