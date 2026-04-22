// @vitest-environment jsdom

import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { defineComponent, h } from "vue";
import { mount } from "@vue/test-utils";

vi.mock("../src/posapp/services/dashboardService", () => ({
	fetchDashboardData: vi.fn(async () => ({
		enabled: false,
		disabled_reason: "profile_disabled",
		sales_overview: {},
	})),
}));

import Reports from "../src/posapp/components/reports/Reports.vue";
import { fetchDashboardData } from "../src/posapp/services/dashboardService";
import { useEmployeeStore } from "../src/posapp/stores/employeeStore";
import { useUIStore } from "../src/posapp/stores/uiStore";

const BoxStub = defineComponent({
	setup(_, { slots }) {
		return () => h("div", {}, slots.default?.());
	},
});

const flushPromises = async () => {
	await Promise.resolve();
	await Promise.resolve();
};

describe("Reports supervisor gating", () => {
	beforeEach(() => {
		setActivePinia(createPinia());
		vi.clearAllMocks();
		vi.stubGlobal("__", (value: string) => value);
		const uiStore = useUIStore();
		uiStore.setPosProfile({ name: "Main POS", currency: "PKR" } as any);
	});

	it("blocks non-supervisors from loading the dashboard", async () => {
		const employeeStore = useEmployeeStore();
		employeeStore.setCurrentCashier({
			user: "cashier@example.com",
			full_name: "Main Cashier",
			is_supervisor: false,
		});

		const wrapper = mount(Reports, {
			global: {
				components: {
					VContainer: BoxStub,
					VChip: BoxStub,
					VSelect: BoxStub,
					VTextField: BoxStub,
					VBtn: BoxStub,
					VAlert: BoxStub,
				},
			},
		});

		await flushPromises();

		expect(fetchDashboardData).not.toHaveBeenCalled();
		expect(wrapper.text()).toContain("POS supervisor");
	});

	it("allows supervisors to request dashboard data", async () => {
		const employeeStore = useEmployeeStore();
		employeeStore.setCurrentCashier({
			user: "supervisor@example.com",
			full_name: "Supervisor",
			is_supervisor: true,
		});

		mount(Reports, {
			global: {
				components: {
					VContainer: BoxStub,
					VChip: BoxStub,
					VSelect: BoxStub,
					VTextField: BoxStub,
					VBtn: BoxStub,
					VAlert: BoxStub,
				},
			},
		});

		await flushPromises();

		expect(fetchDashboardData).toHaveBeenCalledWith(
			expect.objectContaining({
				pos_profile: "Main POS",
			}),
		);
	});
});
