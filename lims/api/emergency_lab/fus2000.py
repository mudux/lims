
import frappe

@frappe.whitelist(allow_guest=True)
def process_fus2000_hl7(HL7Message):
    return HL7Message