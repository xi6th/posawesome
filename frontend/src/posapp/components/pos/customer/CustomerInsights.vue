<template>
	<div v-if="showInsights" class="customer-insights">
		<div v-if="showStoredValue" class="customer-insights__card" data-test="stored-value-insight">
			<p class="customer-insights__eyebrow">{{ __("Stored Value") }}</p>
			<div class="customer-insights__value">{{ formatCurrency(storedValueBalance) }}</div>
			<p class="customer-insights__meta">
				{{ storedValueSourcesLabel }}
			</p>
		</div>
		<div v-if="showLoyalty" class="customer-insights__card" data-test="loyalty-insight">
			<p class="customer-insights__eyebrow">{{ __("Loyalty") }}</p>
			<div class="customer-insights__value">{{ loyaltyPointsLabel }}</div>
			<p class="customer-insights__meta">{{ __("Points available for redemption") }}</p>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	customerInfo: {
		type: Object,
		default: () => ({}),
	},
	formatCurrency: {
		type: Function,
		default: (value) => String(value ?? 0),
	},
});

const __ = window.__;

const storedValueBalance = computed(() => Number(props.customerInfo?.stored_value_balance || 0));
const storedValueSources = computed(() => Number(props.customerInfo?.stored_value_sources || 0));
const loyaltyPoints = computed(() => Number(props.customerInfo?.loyalty_points || 0));

const showStoredValue = computed(() => storedValueBalance.value > 0);
const showLoyalty = computed(() => loyaltyPoints.value > 0);
const showInsights = computed(() => showStoredValue.value || showLoyalty.value);

const storedValueSourcesLabel = computed(() =>
	storedValueSources.value === 1 ? __("1 source") : __(`${storedValueSources.value} sources`),
);

const loyaltyPointsLabel = computed(() => __(`${loyaltyPoints.value} pts`));
</script>

<style scoped>
.customer-insights {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
	gap: 10px;
	margin-top: 10px;
}

.customer-insights__card {
	background: var(--pos-surface-raised);
	border: 1px solid var(--pos-border-light);
	border-radius: 12px;
	padding: 12px;
}

.customer-insights__eyebrow {
	margin: 0 0 6px;
	font-size: 0.72rem;
	font-weight: 700;
	letter-spacing: 0.08em;
	text-transform: uppercase;
	color: var(--pos-text-secondary);
}

.customer-insights__value {
	font-size: 1rem;
	font-weight: 700;
	line-height: 1.2;
	color: var(--pos-text-primary);
}

.customer-insights__meta {
	margin: 6px 0 0;
	font-size: 0.8rem;
	color: var(--pos-text-secondary);
}
</style>
