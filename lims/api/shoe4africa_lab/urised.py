import frappe

@frappe.whitelist(allow_guest=True)
def process_urised_hl7(HL7Message):
    # port 9700
    return HL7Message