import json
import frappe
from lims.api.utils.log_comments import add_comment
from frappe.model.workflow import apply_workflow


@frappe.whitelist(allow_guest=True)
def process_sysmex_hl7(HL7Message):
    #  # https://www.spheregen.com/custom-web-service-connections-from-mirth-connect/
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
# bench execute lims.api.shoe4africa_lab.sysmex.process_sysmex_astm
def process_sysmex_astm():
    field_list = ['lab_station','lab_machine','astm_data','name']
    machine_name = 'SYSMEX-330-S4A'
    raw_astm_docs  = frappe.get_all('Raw ASTM', filters={'is_processed': 1,'has_error':0,'lab_machine':machine_name}, fields= field_list,order_by='creation asc',start=0,page_length=1)
    # print(len(raw_astm))
    for data in raw_astm_docs:
        raw_name = data['name'] #'a06e6641-c214'
        raw_astm_doc  = frappe.get_doc('Raw ASTM', raw_name)
        astm_data = raw_astm_doc.get('astm_data')
        # print(astm_data)
        result_data = json.loads(astm_data[1:-1])
        lab_name = result_data['OrderNumber']
        patient = result_data['Patient']
        orders = result_data['Orders']
        results = result_data['Result']
        uoms = result_data['Uom']
        print(' patient ',patient,' lab_name ',lab_name)
        sysmex_append_to_lab_test(lab_name,orders,results,uoms)

def sysmex_append_to_lab_test(lab_name,orders,results,uoms):
    # lab_test = frappe.get_doc('Lab Test','6X2')
    lab_test = frappe.get_doc('Lab Test',lab_name)
    idx = 1
    # create_test_uom(uoms)
    for order in orders[1:]:
        # uom = words = uoms[idx].split('\/')
        # print(uom)
        range_str = '----'
        normal_test_items = lab_test.append('normal_test_items')
        normal_test_items.idx = idx
        normal_test_items.lab_test_name = order
        normal_test_items.lab_test_event = order
        normal_test_items.result_value = "{0}".format(results[idx]) #,result['uom'])
        normal_test_items.lab_test_uom =  uoms[idx] #get_lab_uom(test_name)
        normal_test_items.normal_range =  range_str #result['range']
        normal_test_items.test_range =  range_str
        normal_test_items.lab_test_comment = 'NA'
        # lab_test.save(ignore_permissions=True)
        idx+=1
    lab_test.save()
    if lab_test.get('workflow_state')=='Processing':
        apply_workflow(doc=lab_test, action="Forward For Verification")
    frappe.db.commit()

def create_test_uom(uoms):
    for uom in uoms[1:]:
        if len(uom) and not frappe.db.exists('Lab Test UOM',{'name':uom}):
            um = frappe.new_doc('Lab Test UOM')
            um.lab_test_uom = uom
            um.uom_description = uom
            um.save()
            frappe.db.commit()
        