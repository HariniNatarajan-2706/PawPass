import frappe
from frappe.model.naming import make_autoname
from frappe.model.document import Document

class PET(Document):
    def autoname(self):
        if self.pet_code:
            self.pet_code = self.pet_code.upper()
            self.name = self.pet_code
        else:
            self.name = make_autoname("PET-.YYYY.-.####")