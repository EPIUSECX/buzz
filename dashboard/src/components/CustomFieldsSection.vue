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
				:required="true"
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

// Get placeholder text based on field type
const getFieldPlaceholder = (field) => {
	switch (field.fieldtype) {
		case "Phone":
			return "Enter phone number";
		case "Email":
			return "Enter email address";
		case "Select":
			return `Select ${field.label.toLowerCase()}`;
		default:
			return `Enter ${field.label.toLowerCase()}`;
	}
};
</script>
