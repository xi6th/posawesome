import { describe, expect, it } from "vitest";

import { buildVersionPayload, getEntryFileName } from "../build-manifest.js";

describe("build manifest helpers", () => {
	it("keeps primary shell entries stable while hashing auxiliary entries", () => {
		expect(getEntryFileName({ name: "posawesome" })).toBe("[name].js");
		expect(getEntryFileName({ name: "loader" })).toBe("[name].js");
		expect(getEntryFileName({ name: "offline/index" })).toBe(
			"[name]-[hash].js",
		);
	});

	it("publishes the hashed offline entry path in version metadata", () => {
		const payload = buildVersionPayload("build-2000", {
			"offline/index-AbCd1234.js": {
				type: "chunk",
				name: "offline/index",
				fileName: "offline/index-AbCd1234.js",
			},
		});

		expect(payload).toEqual({
			version: "build-2000",
			assets: {
				loader: "/assets/posawesome/dist/js/loader.js",
				posawesome: "/assets/posawesome/dist/js/posawesome.js",
				css: "/assets/posawesome/dist/js/posawesome.css",
				offlineIndex:
					"/assets/posawesome/dist/js/offline/index-AbCd1234.js",
			},
		});
	});
});
