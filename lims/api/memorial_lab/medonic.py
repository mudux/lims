import frappe

@frappe.whitelist(allow_guest=True)
def process_medonic_hl7(HL7Message):
    return HL7Message