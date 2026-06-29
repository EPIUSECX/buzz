import frappe
from frappe.tests import IntegrationTestCase

from buzz.api.forms import (
	STANDARD_EXCLUDE_FIELDS,
	get_custom_form_data,
	get_form_fields,
	parse_excluded_fields,
	submit_custom_form,
	validate_excluded_fields,
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


class TestParseExcludedFields(IntegrationTestCase):
	def test_blank_returns_none(self):
		self.assertIsNone(parse_excluded_fields(None))
		self.assertIsNone(parse_excluded_fields(""))
		self.assertIsNone(parse_excluded_fields("   "))
		self.assertIsNone(parse_excluded_fields(", ,,"))

	def test_trims_and_drops_empties(self):
		self.assertEqual(parse_excluded_fields("a, b ,,c"), {"a", "b", "c"})

	def test_single_field(self):
		self.assertEqual(parse_excluded_fields("title"), {"title"})


class TestGetFormFields(IntegrationTestCase):
	def test_excluding_a_field_drops_it(self):
		exclude_fields = TALK_PROPOSAL_EXCLUDE | {"phone"}
		fields = get_form_fields("Talk Proposal", exclude_fields)
		returned = {f["fieldname"] for f in fields}
		self.assertNotIn("phone", returned)
		self.assertTrue({"title", "description", "speakers"} <= returned)

	def test_no_extra_exclude_returns_all_renderable(self):
		fields = get_form_fields("Talk Proposal", TALK_PROPOSAL_EXCLUDE)
		returned = {f["fieldname"] for f in fields}
		self.assertTrue({"title", "description", "speakers", "phone"} <= returned)

	def test_layout_breaks_pass_through(self):
		# With layout breaks on, section/column breaks are emitted even when other fields are excluded.
		exclude_fields = TALK_PROPOSAL_EXCLUDE | {"description", "speakers", "phone"}
		fields = get_form_fields("Talk Proposal", exclude_fields, with_layout_breaks=True)
		real_fields = {
			f["fieldname"] for f in fields if f["fieldtype"] not in ("Section Break", "Column Break")
		}
		breaks = [f for f in fields if f["fieldtype"] in ("Section Break", "Column Break")]
		self.assertIn("title", real_fields)
		self.assertFalse({"description", "speakers", "phone"} & real_fields)
		self.assertTrue(breaks, "expected layout breaks to pass through")


class TestCustomFormExcludedFields(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.category = ensure_prompt_named_record("Event Category", "Test Forms Category")
		cls.host = ensure_prompt_named_record("Event Host", "Test Forms Host")

	def make_event(self, excluded_fields, form_route=None, publish=1):
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
				"excluded_fields": excluded_fields,
			},
		)
		event.insert(ignore_permissions=True)
		event.reload()
		return event, form_route

	def test_get_custom_form_data_hides_excluded_fields(self):
		event, form_route = self.make_event("phone")
		data = get_custom_form_data(event.route, form_route)
		returned = {f["fieldname"] for f in data["form_fields"]}
		self.assertNotIn("phone", returned)
		self.assertTrue({"title", "description", "speakers"} <= returned)

	def test_get_custom_form_data_empty_excluded_fields_returns_all(self):
		event, form_route = self.make_event("")
		data = get_custom_form_data(event.route, form_route)
		returned = {f["fieldname"] for f in data["form_fields"]}
		self.assertTrue({"title", "description", "speakers", "phone"} <= returned)

	def test_submit_drops_excluded_field_value(self):
		# phone is excluded -> a posted phone value must be dropped.
		event, form_route = self.make_event("phone")
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
		# Non-excluded fields (and child rows) must still be written.
		self.assertEqual(created.title, "Hidden Phone Test")
		self.assertEqual(created.description, "<p>desc</p>")
		self.assertEqual(len(created.speakers), 1)
		self.assertEqual(created.speakers[0].first_name, "Jane")
		self.assertEqual(created.speakers[0].email, "jane@example.com")


class TestValidateExcludedFields(IntegrationTestCase):
	def test_hiding_mandatory_field_throws(self):
		# speakers is mandatory; it cannot be hidden.
		with self.assertRaises(frappe.ValidationError):
			validate_excluded_fields("Talk Proposal", "speakers")

	def test_unknown_field_throws(self):
		with self.assertRaises(frappe.ValidationError):
			validate_excluded_fields("Talk Proposal", "phone, not_a_field")

	def test_hiding_optional_field_passes(self):
		# phone is optional -> safe to hide.
		validate_excluded_fields("Talk Proposal", "phone")

	def test_system_field_is_noop(self):
		# Auto-set/system fields are never rendered; listing them is a harmless no-op.
		validate_excluded_fields("Talk Proposal", "event, submitted_by")

	def test_blank_is_noop(self):
		validate_excluded_fields("Talk Proposal", "")
		validate_excluded_fields("Talk Proposal", None)


class TestBuzzEventSaveValidatesExcludedFields(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.category = ensure_prompt_named_record("Event Category", "Test Forms Category")
		cls.host = ensure_prompt_named_record("Event Host", "Test Forms Host")

	def make_event_doc(self, excluded_fields):
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
				"excluded_fields": excluded_fields,
			},
		)
		return event

	def test_save_hiding_mandatory_throws(self):
		event = self.make_event_doc("speakers")
		with self.assertRaises(frappe.ValidationError):
			event.insert(ignore_permissions=True)

	def test_save_with_unknown_field_throws(self):
		event = self.make_event_doc("phone, bogus_field")
		with self.assertRaises(frappe.ValidationError):
			event.insert(ignore_permissions=True)

	def test_save_hiding_optional_field_succeeds(self):
		event = self.make_event_doc("phone")
		event.insert(ignore_permissions=True)
		self.assertTrue(frappe.db.exists("Buzz Event", event.name))
