
import frappe

# http://172.16.0.115/api/method/lims.api.emergency_lab.medonic.http://172.16.0.115/api/method/lims.api.emergency_lab.sysmex330.process_medonic_hl7
@frappe.whitelist(allow_guest=True)
def process_sysmex_hl7(HL7Message):
    return HL7Message