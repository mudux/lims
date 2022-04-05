import json
import frappe
from lims.api.utils.log_comments import add_comment

@frappe.whitelist(allow_guest=True)
def process_sysmex_hl7(HL7Message):
    # https://www.spheregen.com/custom-web-service-connections-from-mirth-connect/
    # https://gist.githubusercontent.com/pkays/a94b1c6b746601cc8975/raw/3464a2a1ab8453621e32d9f9c95e6eca6ea1ee4f/MirthConnect%20Webservice%20connection-1
    message_log = frappe.new_doc('HL7 Message Logs')
    message_log.lab_station = 'SHOE 4 AFRICA'
    message_log.lab_machine = 'SYSMEX XN330'
    message_log.hl7 = json.dumps(HL7Message)
    # message_log.order_number = obr_filler_order_sample_number
    message_log.save(ignore_permissions=True)
    # parse hl7 data
    hl7_data = frappe.db.get_value('HL7 Message Logs',{'name':message_log.get('name')},'hl7')