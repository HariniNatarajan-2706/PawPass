import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class PET(Document):
    def autoname(self):
        if self.pet_code:
            self.name = self.pet_code.strip().upper()
        else:
            self.name = make_autoname("PET-.#####")
    def after_insert(self):
        if self.owner_email:
            frappe.sendmail(
                recipients=[self.owner_email],
                subject="PawPass Test Email",
                message=(
                    f"Hello {self.owner_name},<br><br>"
                    f"Your pet {self.name} has been successfully registered."
                )
            )