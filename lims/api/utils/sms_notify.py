from billing.billing.utils.payment_notifications import get_party_phone
import frappe

# bench execute lims.api.utils.sms_notify.notify_lab_employee_sms

def notify_lab_employee_sms(employee_name,message):
    from mtrh_dev.mtrh_dev.utilities import schedule_sms_to_user
    mobiles = get_party_phone(party_type='Employee', party=employee_name)
    phone_arr = [mobile.phone for mobile in mobiles]
    if len(phone_arr) > 0:
        for number in phone_arr:
            schedule_sms_to_user(userid=None, sms_message=message, phone_number=number)
    else:
        create_contact(employee_name=employee_name)

# bench execute clinical.hook.lab_test.create_contact

def create_contact(employee_name):
    doc = frappe.get_doc('Employee',employee_name)
    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": doc.first_name,
        "status": "Open",
        'middle_name': doc.middle_name,
        'last_name': doc.last_name,
        'gender': doc.gender,
    })
    contact.append('email_ids', dict(email_id=doc.company_email, is_primary=1))

    contact.append('phone_nos', dict(
        phone=doc.cell_number, is_primary_phone=1))
    contact.append('links', dict(link_doctype="Employee", link_name=doc.name))
    contact.insert()
    # notify_lab_employee_sms()