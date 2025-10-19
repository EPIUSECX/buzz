import { createResource, toast } from "frappe-ui";
import { ref } from "vue";
import beepFailSound from "../assets/audio/beep-fail.wav";
import beepSound from "../assets/audio/beep.wav";

// Singleton state - shared across all components
let ticketValidationState = null;

export function useTicketValidation() {
	// Return existing state if it exists
	if (ticketValidationState) {
		return ticketValidationState;
	}

	// Create new state only if it doesn't exist
	const isProcessingTicket = ref(false);
	const isCheckingIn = ref(false);
	const validationResult = ref(null);
	const lastScanResult = ref(null);
	const showTicketModal = ref(false);

	const playSuccessSound = () => {
		const audio = new Audio(beepSound);
		audio.play();
	};

	const playErrorSound = () => {
		const audio = new Audio(beepFailSound);
		audio.play();
	};

	// Ticket validation resource
	const validateTicketResource = createResource({
		url: "buzz.api.validate_ticket_for_checkin",
		onSuccess: (data) => {
			validationResult.value = data;
			lastScanResult.value = {
				success: data.success,
				message: data.message,
				ticket: data.ticket,
			};
			showTicketModal.value = true;
			playSuccessSound();
			isProcessingTicket.value = false;
		},
		onError: (error) => {
			validationResult.value = null;
			lastScanResult.value = null;
			isProcessingTicket.value = false;
			let errorData = JSON.stringify(error);
			if (errorData.includes("Ticket not found")) {
				toast.error("Ticket not found");
			} else if (
				errorData.includes("This ticket is not confirmed and cannot be used for check-in")
			) {
				toast.error("This ticket is not confirmed and cannot be used for check-in");
			} else if (errorData.includes("This ticket was already checked in today")) {
				toast.error("This ticket was already checked in today.");
			} else {
				toast.error("Error validating ticket");
			}
			playErrorSound();
		},
	});

	// Check-in resource
	const checkInResource = createResource({
		url: "buzz.api.checkin_ticket",
		onSuccess: (data) => {
			if (data.success) {
				validationResult.value = data;
				lastScanResult.value = {
					success: true,
					message: data.message,
					ticket: data.ticket,
				};
				showTicketModal.value = false;
			}
			isCheckingIn.value = false;
		},
		onError: (error) => {
			isCheckingIn.value = false;
		},
	});

	// Methods
	const validateTicket = (ticketId) => {
		isProcessingTicket.value = true;
		validateTicketResource.submit({ ticket_id: ticketId });
	};

	const checkInTicket = () => {
		if (!validationResult.value?.ticket?.id) return;

		isCheckingIn.value = true;
		checkInResource.submit({ ticket_id: validationResult.value.ticket.id });
	};

	const clearResults = () => {
		validationResult.value = null;
		lastScanResult.value = null;
		isProcessingTicket.value = false;
		isCheckingIn.value = false;
		showTicketModal.value = false;
	};

	const closeModal = () => {
		showTicketModal.value = false;
	};

	ticketValidationState = {
		// State
		isProcessingTicket,
		isCheckingIn,
		validationResult,
		lastScanResult,
		showTicketModal,

		// Methods
		validateTicket,
		checkInTicket,
		clearResults,
		closeModal,
	};

	return ticketValidationState;
}
