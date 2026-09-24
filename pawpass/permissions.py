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
def get_shop_name():
    return frappe.db.get_single_value("PAWPASS SETTING", "shop_name") or "PawPass"
def check_upcoming_checkouts():
    settings = frappe.get_single("PAWPASS SETTING")
    reminder_days = settings.reminder_days_before_checkout or 1

    today = frappe.utils.getdate()
    reminder_date = frappe.utils.add_days(today, reminder_days)

    stays = frappe.get_all(
        "Stay Card",
        filters={
            "expected_checkout_date": ["between", [today, reminder_date]],
            "status": ["not in", ["Picked Up", "Cancelled"]]
        },
        fields=["name", "pet", "owner_name", "expected_checkout_date"]
    )

    for stay in stays:
        email = frappe.db.get_value(
            "PET",
            stay.pet,
            "owner_email"
        )

        if email:
            frappe.sendmail(
                recipients=[email],
                subject="PawPass Checkout Reminder",
                message=(
                    f"Dear {stay.owner_name},<br><br>"
                    f"Your pet {stay.pet} is scheduled for checkout "
                    f"on {frappe.utils.formatdate(stay.expected_checkout_date)}."
                )
            )