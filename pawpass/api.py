import frappe
from frappe.query_builder import DocType
from frappe.utils import add_days, today

#b2a
@frappe.whitelist()
def get_upcoming_checkouts():
    StayCard = DocType("Stay Card")

    checkout_limit = add_days(today(), 2)

    result = (
        frappe.qb.from_(StayCard)
        .select(
            StayCard.name,
            StayCard.pet,
            StayCard.owner_name,
            StayCard.expected_checkout_date,
        )
        .where(
            StayCard.status.isin(["Checked In", "In Service"])
        )
        .where(
            StayCard.expected_checkout_date <= checkout_limit
        )
        .orderby(
            StayCard.expected_checkout_date
        )
        .run(as_dict=True)
    )

    return result

#b2b
@frappe.whitelist()
def transfer_stays(from_attendant, to_attendant):
    try:
        frappe.db.sql(
            """
            UPDATE `tabStay Card`
            SET assigned_attendant = %s
            WHERE assigned_attendant = %s
            AND status NOT IN ('Picked Up', 'Cancelled')
            """,
            (to_attendant, from_attendant),
        )

        frappe.db.commit()

        return {
            "success": True,
            "from_attendant": from_attendant,
            "to_attendant": to_attendant,
        }

    except Exception:
        frappe.db.rollback()

        frappe.log_error(
            title="PawPass Stay Transfer Failed",
            message=frappe.get_traceback(),
        )

        raise
#d--d1

@frappe.whitelist()
def share_stay_card(stay_card_name, user_email):
    #if not frappe.db.exists("Stay Card", stay_card_name):
    #    frappe.throw(f"Stay Card {stay_card_name} does not exist")
    #if not frappe.db.exists("User", user_email):
    #    frappe.throw(f"User {user_email} does not exist")
    frappe.share.add(
        "Stay Card",
        stay_card_name,
        user_email,
        read=1
    )
    return {
        "message": f"Read access granted to {user_email} for {stay_card_name}"
    }
#d2------

@frappe.whitelist()
def get_stay_cards_unsafe():
    return frappe.get_all(
        "Stay Card",
        fields=["*"]
    )

@frappe.whitelist()
def get_stay_cards_safe():
    stay_cards = frappe.get_list(
        "Stay Card",
        fields=["*"]
    )

    if "PP Attedant" not in frappe.get_roles(frappe.session.user):
        for stay_card in stay_cards:
            stay_card.pop("owner_phone", None)
            stay_card.pop("owner_email", None)

    return stay_cards

@frappe.whitelist()
def rename_attendant(old_name, new_name):
    return frappe.rename_doc(
        "ATTENDANT",
        old_name,
        new_name,
        merge=False
    )

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_attendants_for_stay_card(
    doctype, txt, searchfield, start, page_len, filters
):
    purpose = (filters.get("purpose") or "").lower()

    if purpose == "both":
        return frappe.db.sql(
            """
            SELECT
                a.name,
                a.attendant_name
            FROM
                `tabATTENDANT` a
            WHERE
                a.status = "Active"
                AND (
                    a.name LIKE %(txt)s
                    OR a.attendant_name LIKE %(txt)s
                )
            ORDER BY
                a.attendant_name
            LIMIT %(start)s, %(page_len)s
            """,
            {
                "txt": f"%{txt}%",
                "start": start,
                "page_len": page_len,
            },
        )

    is_boarding = 1 if purpose == "boarding" else 0

    return frappe.db.sql(
        """
        SELECT
            a.name,
            a.attendant_name
        FROM
            `tabATTENDANT` a
        INNER JOIN
            `tabSERVICE TYPE` s
            ON a.specialization = s.name
        WHERE
            a.status = "Active"
            AND s.is_boarding = %(is_boarding)s
            AND (
                a.name LIKE %(txt)s
                OR a.attendant_name LIKE %(txt)s
            )
        ORDER BY
            a.attendant_name
        LIMIT %(start)s, %(page_len)s
        """,
        {
            "is_boarding": is_boarding,
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len,
        },
    )