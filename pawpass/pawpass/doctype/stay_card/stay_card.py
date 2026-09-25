# Copyright (c) 2026, harini and contributors

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today
from frappe.model.document import Document


class StayCard(Document):

    def validate(self):
        if self.check_in_date and self.expected_checkout_date:
            if getdate(self.expected_checkout_date) < getdate(self.check_in_date):
                frappe.throw(
                    _("Expected Checkout Date cannot be before Check-in Date.")
                )

        if self.pet:
            expiry = frappe.db.get_value(
                "PET", self.pet, "vaccination_expiry"
            )
            settings = frappe.get_single("PAWPASS SETTING")
            grace_days = settings.vaccination_grace_days or 0

            if not expiry:
                self.vaccination_status = "Expired"
            else:
                allowed_until = add_days(getdate(expiry), grace_days)
                self.vaccination_status = (
                    "Valid"
                    if getdate(today()) <= allowed_until
                    else "Expired"
                )

            pet = frappe.get_doc("PET", self.pet)
            self.owner_name = pet.owner_name
            self.owner_phone = pet.owner_phone

            if self.status != "Draft" and self.vaccination_status != "Valid":
                frappe.throw(
                    _(
                        "Vaccination must be Valid before the Stay Card "
                        "can progress beyond Draft."
                    )
                )

        nights = 1

        if self.check_in_date and self.expected_checkout_date:
            nights = max(
                (
                    getdate(self.expected_checkout_date)
                    - getdate(self.check_in_date)
                ).days,
                1,
            )

        for row in self.service_line:
            if not row.service_type:
                continue

            service = frappe.get_doc("SERVICE TYPE", row.service_type)
            row.rate = service.base_rate

            if service.is_boarding:
                row.quantity = nights
            else:
                row.quantity = row.quantity or 1

            row.line_total = row.rate * row.quantity

        self.service_total = sum(
            row.line_total or 0 for row in self.service_line
        )
        self.final_amount = self.service_total

    def before_save(self):
        if (
            self.status == "Draft"
            and self.vaccination_status == "Valid"
            and self.assigned_attendant
        ):
            self.status = "Checked In"

    def before_submit(self):
        if self.status != "Ready for Pickup":
            frappe.throw(
                _("Stay Card can be submitted only when Status is Ready for Pickup.")
            )

        if not self.service_line:
            frappe.throw(
                _("At least one Service Line is required before submitting.")
            )

        if self.vaccination_status != "Valid":
            frappe.throw(
                _("Stay Card cannot be submitted because vaccination is not Valid.")
            )

    def on_submit(self):
        if self.pet:
            total_stays = (
                frappe.db.get_value("PET", self.pet, "total_stays") or 0
            ) + 1

            frappe.db.set_value(
                "PET",
                self.pet,
                {
                    "last_visit_date": self.check_in_date,
                    "total_stays": total_stays,
                },
                update_modified=False,
            )

        invoice = frappe.new_doc("Invoice")
        invoice.stay_card = self.name
        invoice.owner_name = self.owner_name
        invoice.invoice_date = today()
        invoice.service_total = self.service_total
        invoice.total_amount = self.final_amount
        invoice.payment_status = "Unpaid"
        invoice.insert(ignore_permissions=True)

        frappe.enqueue(
            "pawpass.pawpass.doctype.stay_card.stay_card.send_stay_complete_email",
            stay_card=self.name,
            queue="short",
        )
    def send_stay_complete_email(stay_card):
        doc = frappe.get_doc("Stay Card", stay_card)

        if not doc.owner_email:
            return

        frappe.sendmail(
            recipients=[doc.owner_email],
            subject=f"Stay Completed - {doc.pet}",
            message=f"""
                <p>Dear {doc.owner_name},</p>

                <p>Your pet <b>{doc.pet}</b>'s stay has been completed.</p>

                <p><b>Total Amount:</b> {doc.final_amount}</p>

                <p>Thank you for choosing PawPass.</p>
            """,
        )

    def on_cancel(self):
        if self.pet:
            total_stays = (
                frappe.db.get_value("PET", self.pet, "total_stays") or 0
            )

            frappe.db.set_value(
                "PET",
                self.pet,
                "total_stays",
                max(total_stays - 1, 0),
            )

        invoice = frappe.db.get_value(
            "Invoice",
            {"stay_card": self.name},
        )

        if invoice:
            invoice_doc = frappe.get_doc("Invoice", invoice)

            if invoice_doc.docstatus == 1:
                invoice_doc.cancel()

        frappe.db.set_value(
            "Stay Card",
            self.name,
            "status",
            "Cancelled",
        )

    def on_trash(self):
        if self.status not in ("Draft", "Cancelled"):
            frappe.throw(
                _("Stay Card can only be deleted when Draft or Cancelled.")
            )

    def on_update(self):
        pass

    def before_print(self, print_settings=None):
        self.print_summary = f"{self.owner_name} - {self.pet}"