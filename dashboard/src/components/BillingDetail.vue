<template>
	<div
		class="bg-surface-white border border-outline-gray-3 rounded-xl p-4 md:p-6 mb-6 shadow-sm"
	>
		<h3 class="text-base font-medium text-ink-gray-8 border-b pb-2 mb-4">
			{{ __("Billing Details") }}
		</h3>
		<div class="flex flex-col gap-4">
			<FormControl
				type="checkbox"
				:model-value="requestInvoice"
				@update:model-value="$emit('update:requestInvoice', $event)"
				:label="__('Do you want an invoice?')"
			/>
			<template v-if="requestInvoice">
				<FormControl
					:model-value="taxId"
					@update:model-value="$emit('update:taxId', $event)"
					type="text"
					:label="taxIdLabel"
					:placeholder="__('Enter {0}', [taxIdLabel])"
				/>
				<div class="space-y-1.5">
					<label class="text-xs text-ink-gray-5 block">
						{{ __("Billing Address") }}
						<span class="text-ink-red-4">*</span>
					</label>
					<Textarea
						:model-value="billingAddress"
						@update:model-value="$emit('update:billingAddress', $event)"
						:placeholder="__('Enter billing address')"
						:required="true"
						variant="outline"
					/>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { FormControl, Textarea } from "frappe-ui";

const props = defineProps({
	requestInvoice: {
		type: Boolean,
		default: false,
	},
	taxId: {
		type: String,
		default: "",
	},
	billingAddress: {
		type: String,
		default: "",
	},
	taxLabel: {
		type: String,
		default: "Tax",
	},
});

defineEmits(["update:requestInvoice", "update:taxId", "update:billingAddress"]);

const taxIdLabel = computed(() => __("{0} ID", [props.taxLabel]));
</script>
