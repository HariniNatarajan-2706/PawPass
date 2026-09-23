import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class PET(Document):
    def autoname(self):
        if self.pet_code:
            self.name = self.pet_code.strip().upper()
        else:
            self.name = make_autoname("PET-.#####")