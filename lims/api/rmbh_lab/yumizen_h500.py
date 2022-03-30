import frappe

@frappe.whitelist(allow_guest=True)
def process_yumizen_hl7(HL7Message):
    return HL7Message