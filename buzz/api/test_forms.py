import frappe
from frappe.tests import IntegrationTestCase

from buzz.api.forms import (
	STANDARD_EXCLUDE_FIELDS,
	get_custom_form_data,
	get_form_fields,
	parse_visible_fields,
	submit_custom_form,
	validate_visible_fields,
)

# Renderable Talk Proposal fields (after STANDARD_EXCLUDE_FIELDS + auto-set event/submitted_by):
#   title (reqd, Data), description (Text Editor), speakers (reqd, Table), phone (Phone)
TALK_PROPOSAL_EXCLUDE = STANDARD_EXCLUDE_FIELDS | {"event", "submitted_by"}


def ensure_prompt_named_record(doctype, name):
	# Event Category / Event Host use autoname "prompt" -> name set explicitly.
	if frappe.db.exists(doctype, name):
		return name
	doc = frappe.new_doc(doctype)
	doc.name = name
	doc.insert(ignore_permissions=True)
	return doc.name


class TestParseVisibleFields(IntegrationTestCase):
	def test_blank_returns_none(self):
		self.assertIsNone(parse_visible_fields(None))
		self.assertIsNone(parse_visible_fields(""))
		self.assertIsNone(parse_visible_fields("   "))
		self.assertIsNone(parse_visible_fields(", ,,"))

	def test_trims_and_drops_empties(self):
		self.assertEqual(parse_visible_fields("a, b ,,c"), {"a", "b", "c"})

	def test_single_field(self):
		self.assertEqual(parse_visible_fields("title"), {"title"})


class TestGetFormFields(IntegrationTestCase):
	def test_include_fields_returns_only_subset(self):
		subset = {"title", "description", "speakers"}
		fields = get_form_fields("Talk Proposal", TALK_PROPOSAL_EXCLUDE, include_fields=subset)
		returned = {f["fieldname"] for f in fields}
		self.assertEqual(returned, subset)
		self.assertNotIn("phone", returned)

	def test_none_returns_all_renderable(self):
		fields = get_form_fields("Talk Proposal", TALK_PROPOSAL_EXCLUDE, include_fields=None)
		returned = {f["fieldname"] for f in fields}
		self.assertEqual(returned, {"title", "description", "speakers", "phone"})

	def test_layout_breaks_pass_through_include_fields(self):
		# With layout breaks on, section/column breaks are emitted even if not in include_fields.
		subset = {"title"}
		fields = get_form_fields(
			"Talk Proposal", TALK_PROPOSAL_EXCLUDE, with_layout_breaks=True, include_fields=subset
		)
		real_fields = {
			f["fieldname"] for f in fields if f["fieldtype"] not in ("Section Break", "Column Break")
		}
		breaks = [f for f in fields if f["fieldtype"] in ("Section Break", "Column Break")]
		self.assertEqual(real_fields, {"title"})
		self.assertTrue(breaks, "expected layout breaks to pass through")


class TestCustomFormVisibleFields(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.category = ensure_prompt_named_record("Event Category", "Test Forms Category")
		cls.host = ensure_prompt_named_record("Event Host", "Test Forms Host")

	def make_event(self, visible_fields, form_route=None, publish=1):
		form_route = form_route or f"propose-{frappe.generate_hash(length=6)}"
		event = frappe.new_doc("Buzz Event")
		event.update(
			{
				"title": f"Test Event {frappe.generate_hash(length=6)}",
				"start_date": "2030-01-01",
				"end_date": "2030-01-01",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
				"medium": "Online",
				"category": self.category,
				"host": self.host,
				"is_published": 1,
			}
		)
		event.set("custom_forms", [])
		event.append(
			"custom_forms",
			{
				"form_doctype": "Talk Proposal",
				"route": form_route,
				"publish": publish,
				"visible_fields": visible_fields,
			},
		)
		event.insert(ignore_permissions=True)
		event.reload()
		return event, form_route

	def test_get_custom_form_data_returns_only_visible_fields(self):
		event, form_route = self.make_event("title, description, speakers")
		data = get_custom_form_data(event.route, form_route)
		returned = {f["fieldname"] for f in data["form_fields"]}
		self.assertEqual(returned, {"title", "description", "speakers"})
		self.assertNotIn("phone", returned)

	def test_get_custom_form_data_empty_visible_fields_returns_all(self):
		event, form_route = self.make_event("")
		data = get_custom_form_data(event.route, form_route)
		returned = {f["fieldname"] for f in data["form_fields"]}
		self.assertEqual(returned, {"title", "description", "speakers", "phone"})

	def test_submit_drops_non_visible_field_value(self):
		# phone is NOT in visible_fields -> a posted phone value must be dropped.
		event, form_route = self.make_event("title, description, speakers")
		submit_custom_form(
			event.route,
			form_route,
			data={
				"title": "Hidden Phone Test",
				"description": "<p>desc</p>",
				"speakers": [{"first_name": "Jane", "email": "jane@example.com"}],
				"phone": "+919999999999",
			},
		)
		created = frappe.get_last_doc("Talk Proposal", filters={"title": "Hidden Phone Test"})
		self.assertEqual(str(created.event), str(event.name))
		self.assertFalse(created.phone, f"phone should be dropped but was {created.phone!r}")


class TestValidateVisibleFields(IntegrationTestCase):
	def test_omitting_mandatory_field_throws(self):
		# speakers is mandatory; omit it.
		with self.assertRaises(frappe.ValidationError):
			validate_visible_fields("Talk Proposal", "title, description")

	def test_unknown_field_throws(self):
		with self.assertRaises(frappe.ValidationError):
			validate_visible_fields("Talk Proposal", "title, description, speakers, not_a_field")

	def test_valid_subset_passes(self):
		# All mandatory (title, speakers) included + an optional one. Should not raise.
		validate_visible_fields("Talk Proposal", "title, speakers, description")

	def test_blank_is_noop(self):
		validate_visible_fields("Talk Proposal", "")
		validate_visible_fields("Talk Proposal", None)


class TestBuzzEventSaveValidatesVisibleFields(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.category = ensure_prompt_named_record("Event Category", "Test Forms Category")
		cls.host = ensure_prompt_named_record("Event Host", "Test Forms Host")

	def make_event_doc(self, visible_fields):
		event = frappe.new_doc("Buzz Event")
		event.update(
			{
				"title": f"Test Event {frappe.generate_hash(length=6)}",
				"start_date": "2030-01-01",
				"end_date": "2030-01-01",
				"start_time": "10:00:00",
				"end_time": "18:00:00",
				"medium": "Online",
				"category": self.category,
				"host": self.host,
				"is_published": 1,
			}
		)
		event.set("custom_forms", [])
		event.append(
			"custom_forms",
			{
				"form_doctype": "Talk Proposal",
				"route": f"propose-{frappe.generate_hash(length=6)}",
				"publish": 1,
				"visible_fields": visible_fields,
			},
		)
		return event

	def test_save_with_missing_mandatory_throws(self):
		event = self.make_event_doc("title, description")
		with self.assertRaises(frappe.ValidationError):
			event.insert(ignore_permissions=True)

	def test_save_with_unknown_field_throws(self):
		event = self.make_event_doc("title, speakers, bogus_field")
		with self.assertRaises(frappe.ValidationError):
			event.insert(ignore_permissions=True)

	def test_save_with_valid_subset_succeeds(self):
		event = self.make_event_doc("title, speakers, description")
		event.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Buzz Event", event.name))
