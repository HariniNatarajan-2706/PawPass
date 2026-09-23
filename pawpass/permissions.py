import frappe
def stay_card_query(user):
    if "PP Attendant" not in frappe.get_roles(user):
        return "NO PERMISSION"

    return """
        `tabStay Card`.assigned_attendant IN (
            SELECT name
            FROM `tabATTENDANT`
            WHERE user = {user}
        )
    """.format(user=frappe.db.escape(user))

def after_install():
    default_service_types = [
        {
            "service_name": "Overnight Boarding",
            "is_boarding": 1,
            "base_rate": 1000,
        },
        {
            "service_name": "Deshedding Treatment",
            "is_boarding": 0,
            "base_rate": 1000,
        },
        {
            "service_name": "Nail Trim",
            "is_boarding": 0,
            "base_rate": 100,
        },
        {
            "service_name": "Bath and Brush",
            "is_boarding": 0,
            "base_rate": 500,
        },
    ]

    for service in default_service_types:
        if not frappe.db.exists(
            "SERVICE TYPE",
            {"service_name": service["service_name"]}
        ):
            doc = frappe.get_doc(
                {
                    "doctype": "SERVICE TYPE",
                    "service_name": service["service_name"],
                    "is_boarding": service["is_boarding"],
                    "base_rate": service["base_rate"],
                }
            )

            doc.insert(ignore_permissions=True)

    settings = frappe.get_single("PAWPASS SETTING")

    if not settings.shop_name:
        settings.shop_name = "Pawpass"
        settings.manager_email = "harininatarajan2706@gmail.com"
        settings.default_boarding_rate = 400
        settings.vaccination_grace_days = 0
        settings.reminder_days_before_checkout = 1

        settings.save(ignore_permissions=True)

    print("PawPass installed successfully.")