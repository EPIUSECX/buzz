# Copyright (c) 2025, BWH Studios and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase

# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestEventProposal(IntegrationTestCase):
	"""
	Integration tests for EventProposal.
	Use this class for testing interactions between multiple components.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Event Category", "Test Proposal Category"):
			category = frappe.new_doc("Event Category")
			category.name = "Test Proposal Category"
			category.insert(ignore_permissions=True)
		cls.category = "Test Proposal Category"

	def make_proposal(self, **kwargs):
		proposal = frappe.new_doc("Event Proposal")
		proposal.update(
			{
				"title": f"Proposal {frappe.generate_hash(length=6)}",
				"category": self.category,
				"medium": "Online",
				"start_date": "2030-01-01",
				"about": "<p>About the event</p>",
			}
		)
		proposal.update(kwargs)
		proposal.insert(ignore_permissions=True)
		return proposal

	def test_create_host_creates_and_links_event_host(self):
		company = f"Acme {frappe.generate_hash(length=6)}"
		proposal = self.make_proposal(host_company=company, about_the_company="We host events.")

		host_name = proposal.create_host()

		self.assertEqual(host_name, company)
		self.assertEqual(proposal.host, company)
		self.assertTrue(frappe.db.exists("Event Host", company))
		self.assertEqual(frappe.db.get_value("Event Host", company, "about"), "We host events.")

	def test_create_host_reuses_existing_host(self):
		company = f"Existing {frappe.generate_hash(length=6)}"
		existing = frappe.new_doc("Event Host")
		existing.name = company
		existing.insert(ignore_permissions=True)

		proposal = self.make_proposal(host_company=company)
		proposal.create_host()

		self.assertEqual(proposal.host, company)

	def test_create_host_requires_company_name(self):
		proposal = self.make_proposal()
		with self.assertRaises(frappe.ValidationError):
			proposal.create_host()

	def test_create_host_throws_if_already_linked(self):
		company = f"Acme {frappe.generate_hash(length=6)}"
		proposal = self.make_proposal(host_company=company)
		proposal.create_host()
		with self.assertRaises(frappe.ValidationError):
			proposal.create_host()
