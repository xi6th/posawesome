import { describe, expect, it } from "vitest";

import {
	_getStockCacheKey,
	_getCachedStockQty,
	_storeStockQty,
} from "../src/posapp/components/pos/invoice_utils/cache";

describe("invoice stock cache", () => {
	it("includes batch number in the stock cache key when present", () => {
		const context: any = {
			pos_profile: {
				warehouse: "Main Warehouse",
			},
		};

		expect(
			_getStockCacheKey(context, {
				item_code: "ITEM-001",
				warehouse: "Main Warehouse",
			}),
		).toBe("ITEM-001::Main Warehouse");

		expect(
			_getStockCacheKey(context, {
				item_code: "ITEM-001",
				warehouse: "Main Warehouse",
				batch_no: "BATCH-001",
			}),
		).toBe("ITEM-001::Main Warehouse::BATCH-001");
	});

	it("stores batch-specific quantities independently", () => {
		const context: any = {};

		_storeStockQty(context, "ITEM-001::Main Warehouse", 7);
		_storeStockQty(context, "ITEM-001::Main Warehouse::BATCH-001", 3);

		expect(
			_getCachedStockQty(context, "ITEM-001::Main Warehouse"),
		).toBe(7);
		expect(
			_getCachedStockQty(context, "ITEM-001::Main Warehouse::BATCH-001"),
		).toBe(3);
	});
});
