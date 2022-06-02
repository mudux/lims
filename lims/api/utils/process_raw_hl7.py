import json
import frappe
from lims.api.shoe4africa_lab.urised import process_urised_hl7

# bench execute lims.api.utils.process_raw_hl7.process_raw_hl7
def process_raw_hl7():
    field_list = ['lab_station','lab_machine','hl7_data','name']
    raw_hl7  = frappe.get_all('Raw HL7', filters={'is_processed': 0,'has_error':0}, fields= field_list,order_by='creation asc',start=0,page_length=10,)
    print("data {0}".format(len(raw_hl7)))
    for data in raw_hl7:
        raw_name =  data['name'] #'827ea493-c493'
        print(raw_name)
        raw_astm_doc  = frappe.get_doc('Raw HL7', raw_name)
        hl7_data = raw_astm_doc.get('hl7_data')
        parsed_data = ''
        if hl7_data.startswith('"') and hl7_data.endswith('"'):
            print('string here')
            parsed_data = raw_astm_doc.get('hl7_data')[1:-1]
        else:
            print('raw json')
            parsed_data = raw_astm_doc.get('hl7_data')
        # print(str(parsed_data))
        if len(parsed_data) > 100:
            # print('len gt 100')
            result_data = json.loads(parsed_data)
            # print(str(result_data))
            if data['lab_machine'] == 'URISED-S4A':
                log_name = process_urised_hl7(result_data['HL7Message'])
                frappe.db.set_value('Raw HL7', raw_name,{'hl7_log': log_name,'is_processed':1})
                # print(log_name)
        else:
            print('ERROR')
            log  = frappe.new_doc('Lims Error Log')
            log.ordernumber  = raw_name
            log.log_number = raw_name
            log.unprocessed_result = str(parsed_data)
            log.save(ignore_permissions=True)
            frappe.db.set_value('Raw ASTM', raw_name,{'is_processed':1,'has_error':1})
    # parsed_data = raw_astm_doc.get('astm_data')[1:
    # process_raw_astm
    # lims.api.utils.process_raw_astm.process_raw_astm