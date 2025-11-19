# Copyright (c) 2025, BWH Studios and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TicketCancellationRequest(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from buzz.ticketing.doctype.ticket_cancellation_item.ticket_cancellation_item import (
			TicketCancellationItem,
		)

		amended_from: DF.Link | None
		booking: DF.Link
		cancel_full_booking: DF.Check
		status: DF.Literal["In Review", "Accepted", "Rejected"]
		tickets: DF.Table[TicketCancellationItem]
	# end: auto-generated types

	def on_submit(self):
		if self.status != "Accepted":
			frappe.throw(frappe._("You must accept the request in order to submit it!"))

		if self.cancel_full_booking:
			frappe.get_cached_doc("Event Booking", self.booking).cancel()
		else:
			# cancel individual tickets
			for ticket_item in self.tickets:
				frappe.get_cached_doc("Event Ticket", ticket_item.ticket).cancel()
