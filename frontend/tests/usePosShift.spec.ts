import { describe, expect, it, vi } from "vitest";

import { buildSkippedClosingInvoicesPrompt } from "../src/posapp/composables/pos/shared/usePosShift";

describe("usePosShift closing warnings", () => {
	it("includes invoice and cancelled return reference details in the warning prompt", () => {
		vi.stubGlobal("window", {
			__: (value: string) => value,
		});

		const message = buildSkippedClosingInvoicesPrompt([
			{
				invoice: "SINV-RET-0001",
				doctype: "Sales Invoice",
				return_against: "ACC-SINV-2026-00222",
			},
		]);

		expect(message).toContain(
			"1 printed return invoice references a cancelled invoice and will be excluded from closing.",
		);
		expect(message).toContain("SINV-RET-0001");
		expect(message).toContain("ACC-SINV-2026-00222");
		expect(message).toContain("The skipped invoice will remain a draft.");
		expect(message).toContain("Do you want to proceed?");
	});
});
