import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
	setRegisterData: vi.fn(),
	openDialog: vi.fn(),
	clearOpeningStorage: vi.fn(),
	getOpeningStorage: vi.fn(),
	getValidCachedOpeningForCurrentUser: vi.fn(),
	frappeCall: vi.fn(),
	realtimeEmit: vi.fn(),
}));

vi.mock("vue", async () => {
	const actual = await vi.importActual<any>("vue");
	return {
		...actual,
		getCurrentInstance: () => ({ proxy: { eventBus: null } }),
		inject: () => null,
	};
});

vi.mock("../src/posapp/stores/toastStore.js", () => ({
	useToastStore: () => ({ show: vi.fn() }),
}));

vi.mock("../src/posapp/stores/uiStore.js", () => ({
	useUIStore: () => ({
		setRegisterData: mocks.setRegisterData,
	}),
}));

vi.mock("../src/offline/index", () => ({
	initPromise: Promise.resolve(),
	checkDbHealth: vi.fn().mockResolvedValue(undefined),
	getOpeningStorage: mocks.getOpeningStorage,
	setOpeningStorage: vi.fn(),
	clearOpeningStorage: mocks.clearOpeningStorage,
	setTaxTemplate: vi.fn(),
	isOffline: vi.fn(() => false),
	getBootstrapSnapshot: vi.fn(() => ({})),
	setBootstrapSnapshot: vi.fn(),
}));

vi.mock("../src/posapp/utils/openingCache", () => ({
	getValidCachedOpeningForCurrentUser:
		mocks.getValidCachedOpeningForCurrentUser,
}));

vi.mock("../src/offline/bootstrapSnapshot", () => ({
	createBootstrapSnapshotFromRegisterData: vi.fn(() => ({})),
}));

describe("usePosShift opening gate", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		vi.stubGlobal("frappe", {
			session: { user: "cashier@example.com" },
			call: vi.fn(),
			realtime: { emit: mocks.realtimeEmit },
		});
		mocks.getOpeningStorage.mockReturnValue({
			pos_profile: { name: "Main POS" },
			pos_opening_shift: { name: "SHIFT-1", user: "cashier@example.com" },
		});
		mocks.getValidCachedOpeningForCurrentUser.mockReturnValue({
			pos_profile: { name: "Main POS" },
			pos_opening_shift: { name: "SHIFT-1", user: "cashier@example.com" },
		});
	});

	it("does not grant POS access from cached opening data when the server has no open shift", async () => {
		const { usePosShift } = await import(
			"../src/posapp/composables/pos/shared/usePosShift"
		);
		mocks.frappeCall.mockResolvedValue({ message: null });
		globalThis.frappe.call = mocks.frappeCall;

		const shift = usePosShift(mocks.openDialog);
		await shift.check_opening_entry();

		expect(mocks.setRegisterData).not.toHaveBeenCalled();
		expect(mocks.openDialog).toHaveBeenCalledTimes(1);
		expect(mocks.clearOpeningStorage).toHaveBeenCalledTimes(1);
		expect(mocks.frappeCall).toHaveBeenCalledWith(
			"posawesome.posawesome.api.shifts.check_opening_shift",
			{ user: "cashier@example.com" },
		);
	});

	it("still applies the server-confirmed open shift", async () => {
		const { usePosShift } = await import(
			"../src/posapp/composables/pos/shared/usePosShift"
		);
		const registerData = {
			pos_profile: { name: "Main POS" },
			pos_opening_shift: { name: "SHIFT-2", user: "cashier@example.com" },
		};
		mocks.frappeCall.mockResolvedValue({ message: registerData });
		globalThis.frappe.call = mocks.frappeCall;

		const shift = usePosShift(mocks.openDialog);
		await shift.check_opening_entry();

		expect(mocks.setRegisterData).toHaveBeenCalledWith(registerData);
		expect(mocks.openDialog).not.toHaveBeenCalled();
	});
});
