// Copyright (c) 2025, BWH Studios and contributors
// For license information, please see license.txt

frappe.ui.form.on("FE Event", {
	refresh(frm) {
		frappe.call("frappe.geo.country_info.get_country_timezone_info").then(({ message }) => {
			frm.fields_dict.time_zone.set_data(message.all_timezones);
		});

		if (frm.doc.route && frm.doc.is_published) {
			frm.add_web_link(`/events/${frm.doc.route}`);
		}

		frm.add_custom_button(__("Start Check In"), () => {
			frappe.prompt(
				{
					label: "Track",
					fieldname: "track",
					fieldtype: "Link",
					options: "Event Track",
					get_query() {
						return {
							filters: {
								event: frm.doc.name,
							},
						};
					},
				},
				(values) => {
					const track = values.track;
					new frappe.ui.Scanner({
						dialog: true, // open camera scanner in a dialog
						multiple: false, // TODO: make multiple work (Danny says use a prev variable to avoid duplicate)
						on_scan(data) {
							const ticket_id = data.decodedText;
							frm.call("check_in", { ticket_id, track })
								.then(() => {
									frappe.show_alert(__("Check In Complete!"));
									frm.refresh();
								})
								.catch(() => {
									frappe.utils.play_sound("error");
								});
						},
					});
				}
			);
		});

		const button_label = frm.doc.is_published ? __("Unpublish") : __("Publish");
		frm.add_custom_button(button_label, () => {
			frm.set_value("is_published", !frm.doc.is_published);
			frm.save();
		});

		frm.set_query("track", "schedule", (doc, cdt, cdn) => {
			return {
				filters: {
					event: doc.name,
				},
			};
		});

		frm.add_custom_button("Pay", () => {
			// Replace this token with your dynamically generated one
			const payment_url =
				"https://accept.paymob.com/api/acceptance/iframes/967335?payment_token=ZXlKaGJHY2lPaUpJVXpVeE1pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SjFjMlZ5WDJsa0lqb3lNRFkyTlRRMExDSmhiVzkxYm5SZlkyVnVkSE1pT2pFd01Dd2lZM1Z5Y21WdVkza2lPaUpGUjFBaUxDSnBiblJsWjNKaGRHbHZibDlwWkNJNk5UTTFNVFV5TUN3aWIzSmtaWEpmYVdRaU9qUXdOVEk1T0RRMk15d2lZbWxzYkdsdVoxOWtZWFJoSWpwN0ltWnBjbk4wWDI1aGJXVWlPaUpCWkcxcGJtbHpkSEpoZEc5eUlpd2liR0Z6ZEY5dVlXMWxJam9pUVdSdGFXNXBjM1J5WVhSdmNpSXNJbk4wY21WbGRDSTZJazVCSWl3aVluVnBiR1JwYm1jaU9pSk9RU0lzSW1ac2IyOXlJam9pVGtFaUxDSmhjR0Z5ZEcxbGJuUWlPaUpPUVNJc0ltTnBkSGtpT2lKRFlXbHlieUlzSW5OMFlYUmxJam9pVGtFaUxDSmpiM1Z1ZEhKNUlqb2lSVWNpTENKbGJXRnBiQ0k2SWtGa2JXbHVhWE4wY21GMGIzSWlMQ0p3YUc5dVpWOXVkVzFpWlhJaU9pSXJNakF4TVRFeE1URXhNVEV4SWl3aWNHOXpkR0ZzWDJOdlpHVWlPaUpPUVNJc0ltVjRkSEpoWDJSbGMyTnlhWEIwYVc5dUlqb2lUa0VpZlN3aWJHOWphMTl2Y21SbGNsOTNhR1Z1WDNCaGFXUWlPbVpoYkhObExDSmxlSFJ5WVNJNmUzMHNJbk5wYm1kc1pWOXdZWGx0Wlc1MFgyRjBkR1Z0Y0hRaU9tWmhiSE5sTENKbGVIQWlPakUzTmpFeU1UazVOREVzSW5CdGExOXBjQ0k2SWpFNU55NDBPUzR5TURndU1UYzVJbjAuWVVQQkdGaWFzNWQwWkFWaWdLNjdfcXlEV0c3N2dWNmJEMkVCUXhFNlhQalRaYTBLaVNMX0htTTkwTkgwV29ndl8tWnJ1QXJ5SFZFNGdMSklGN3BDdUE=";
			// Open in new tab (or use window.location.href to open in same tab)
			window.open(payment_url, "_blank");
		});
	},
});
