<template>
	<div v-if="customFields.length > 0" class="space-y-4">
		<h5 v-if="showTitle" class="text-base font-medium text-ink-gray-8 border-b pb-2">
			{{ title || "Additional Information" }}
		</h5>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
			<FormControl
				v-for="field in customFields"
				:key="field.fieldname"
				:model-value="getFieldValue(field.fieldname)"
				@update:model-value="updateFieldValue(field.fieldname, $event)"
				:label="field.label"
				:type="getFormControlType(field.fieldtype)"
				:options="getFieldOptions(field)"
				:required="field.mandatory"
				:placeholder="getFieldPlaceholder(field)"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	customFields: {
		type: Array,
		default: () => [],
	},
	modelValue: {
		type: Object,
		default: () => ({}),
	},
	title: {
		type: String,
		default: "",
	},
	showTitle: {
		type: Boolean,
		default: true,
	},
});

const emit = defineEmits(["update:modelValue"]);

// Get field value from model
const getFieldValue = (fieldname) => {
	return props.modelValue[fieldname] || "";
};

// Update field value in model
const updateFieldValue = (fieldname, value) => {
	const updatedValue = { ...props.modelValue, [fieldname]: value };
	emit("update:modelValue", updatedValue);
};

// Convert Frappe field types to form control types
const getFormControlType = (fieldtype) => {
	switch (fieldtype) {
		case "Phone":
			return "text";
		case "Email":
			return "email";
		case "Select":
			return "select";
		default:
			return "text";
	}
};

// Get field options for select fields
const getFieldOptions = (field) => {
	if (field.fieldtype === "Select" && field.options) {
		return field.options.split("\n").map((option) => ({
			label: option.trim(),
			value: option.trim(),
		}));
	}
	return [];
};

// Get placeholder text - use custom placeholder if available, otherwise no placeholder
const getFieldPlaceholder = (field) => {
	// If custom placeholder is provided, use it
	if (field.placeholder?.trim()) {
		const placeholder = field.placeholder.trim();
		return field.mandatory ? `${placeholder} (required)` : placeholder;
	}

	// If no custom placeholder is provided, return empty string (no placeholder)
	return "";
};
</script>
