import json
import frappe
from lims.api.utils.log_comments import add_comment

@frappe.whitelist(allow_guest=True)
def process_medonic_hl7(HL7Message):
    # print('data received')
    # url = 'http://172.16.0.45:9003'
    # x = requests.post(url, json = json.dumps({'HL7Data':HL7Message}))
    # print(x.text)
    # result_data = json.loads(str(HL7Message))
    # https://lyniate.com/resources/hl7-msh-message-header/
    # https://docs.oracle.com/cd/E19509-01/820-4408/agvfq/index.html
    # https://lyniate.com/resources/hl7-obr-segment/
    # https://lyniate.com/resources/hl7-nte-notes-comments/
    # https://lyniate.com/resources/hl7-obx-segment/
    # save the received payload
    message_log = frappe.new_doc('HL7 Message Logs')
    message_log.lab_station = 'SHOE 4 AFRICA'
    message_log.lab_machine = 'MEDONIC'
    message_log.hl7 = json.dumps(HL7Message)
    # message_log.order_number = obr_filler_order_sample_number
    message_log.save(ignore_permissions=True)
    # parse hl7 data
    hl7_data = frappe.db.get_value('HL7 Message Logs',{'name':message_log.get('name')},'hl7')
    result_data = json.loads(hl7_data)
    # print(str(result_data))
    if len(result_data)>1:
        obr_data = result_data["OBR"]
        obr_filler_order_sample_number = obr_data["OBR.3"]["OBR.3.1"] if obr_data["OBR.3"] else 'No Filler Order Number'
        obr_universal_service_id = obr_data["OBR.4"]["OBR.4.1"] if obr_data["OBR.4"] else 'No universal Service Id'
        obr_result_time = obr_data["OBR.22"]["OBR.22.1"] if obr_data["OBR.22"] else 'No result Time'
        nte_data = result_data["NTE"]
        nte_comment = nte_data["NTE.3"]["NTE.3.1"] if nte_data["NTE.3"] else 'No Coment segment'
        # add order number to log
        frappe.db.set_value('HL7 Message Logs',message_log.get('name'),{'order_number': obr_filler_order_sample_number})
        obx_data_array = result_data["OBX"] if result_data["OBX"] else [] 
        parsed_obx = []
        # <ol><li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>hjkljl</li>
        custom_result = "<ol>"
        list_body='<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
        for obx_data in obx_data_array:
            obx_observation_set_id = obx_data["OBX.1"]["OBX.1.1"] if obx_data["OBX.1"] else 'No Set Id'
            obx_observation_value_type = obx_data["OBX.2"]["OBX.2.1"] if obx_data["OBX.2"] else 'No Observation Value Type'
            obx_observation_id = obx_data["OBX.3"]["OBX.3.1"] if obx_data["OBX.3"] else 'No Observation Id'
            obx_observation_sub_id = obx_data["OBX.4"]["OBX.4.1"] if obx_data["OBX.4"] else 'No Observation Sub Id'
            obx_observation_value = obx_data["OBX.5"]["OBX.5.1"] if obx_data["OBX.3"] else 'No Observation Value'
            obx_observation_units = obx_data["OBX.6"]["OBX.6.1"] if obx_data["OBX.6"] else 'No Units'
            obx_observation_ref_range = obx_data["OBX.7"]["OBX.7.1"] if obx_data["OBX.7"] else 'No Range Data'
            obx_observation_abnormal_flags = obx_data["OBX.8"]["OBX.8.1"] if obx_data["OBX.8"] else 'No Abnormal flags'
            obx_probability = obx_data["OBX.9"]["OBX.9.1"] if obx_data["OBX.9"] else 'No Probability'
            obx_nature_of_abnormal_test = obx_data["OBX.10"]["OBX.10.1"] if obx_data["OBX.10"] else 'No Nature Of abnormal Test'
            obx_observation_result_status = obx_data["OBX.11"]["OBX.11.1"] if obx_data["OBX.11"] else 'No Result Status'
            obj = {
                'obx_observation_set_id':obx_observation_set_id,
                'obx_observation_value_type':obx_observation_value_type,
                'obx_observation_sub_id':obx_observation_sub_id,
                'obx_observation_id':obx_observation_id,
                'obx_observation_value':obx_observation_value,
                'obx_observation_units':obx_observation_units,
                'obx_observation_ref_range':obx_observation_ref_range,
                'obx_observation_abnormal_flags':obx_observation_abnormal_flags,
                'obx_probability':obx_probability,
                'obx_nature_of_abnormal_test':obx_nature_of_abnormal_test,
                'obx_observation_result_status':obx_observation_result_status
                }
            if obx_data["OBX.6"] and obx_data["OBX.7"]:
                parsed_obx.append(obj)
                custom_result += list_body + "{0}\t {1} {2}{3}\t ({4})</li>".format(get_template_name(obx_observation_id),obx_observation_id,obx_observation_value,obx_observation_units,obx_observation_ref_range)
        # return {'HL7Data':result_data["MSH"]}
        # return {'HL7Data':type(hl7_data)}
        results = {
            'log_id':message_log.get('name'),
            'obr_filler_order_sample_number':obr_filler_order_sample_number,
            'obr_universal_service_id':obr_universal_service_id,
            'obr_result_time':obr_result_time,
            'nte_comment':nte_comment,
            'parsed_obx':parsed_obx,
            'custom_result':custom_result
        }
        frappe.db.set_value('HL7 Message Logs', message_log.get('name'),{'result_data': json.dumps(results)})
        lab_name = 'HLC-LAB-2022-00012' # HARD CODE FOR TESTING
        obr_filler_order_sample_number = lab_name
        tests_sharing_sample_child =  frappe.db.get_all('Lab Test Sample Share',filters={'lab_test':['IN',lab_name]},fields=['name','lab_test','parent'])
        tests_sharing_sample_parent =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':lab_name},fields=['name','lab_test','parent'])
        tests_sharing_sample = tests_sharing_sample_parent or tests_sharing_sample_child
        if len(tests_sharing_sample)>0:
            parent_test = tests_sharing_sample[0]['parent']
            tests_sharing_sample =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':parent_test},fields=['name','lab_test'])
            for test in tests_sharing_sample:
                update_lab_test(test['lab_test'],custom_result,parsed_obx,message_log.get('name'))
            update_lab_test(obr_filler_order_sample_number,custom_result,parsed_obx,message_log.get('name'))
        else:
            update_lab_test(obr_filler_order_sample_number,custom_result,parsed_obx,message_log.get('name'))
        return results
    return {'wrong data format'}

def update_lab_test(test_name,custom_result,result_list,log_name):
    frappe.db.set_value('Lab Test',test_name,{'custom_result': custom_result})
    lab_test = frappe.get_doc('Lab Test',test_name)
    normal_test_results =  frappe.db.get_all('Normal Test Result',filters={'parent':test_name},fields=['name','lab_test_name'])
    lab_test.normal_toggle = 1
    for res in normal_test_results:
        frappe.delete_doc('Normal Test Result',res['name'])
    idx = 0
    sorted_results = sorted(result_list, key=lambda d: d['obx_observation_id'])
    for result in sorted_results:
        normal_test_items = lab_test.append('normal_test_items')
        normal_test_items.idx = idx
        normal_test_items.lab_test_name = get_template_name(result['obx_observation_id'])
        normal_test_items.lab_test_event = result['obx_observation_id']
        normal_test_items.result_value = str(result['obx_observation_value'])
        normal_test_items.lab_test_uom = result['obx_observation_units']
        # normal_test_items.secondary_uom = result['']
        normal_test_items.normal_range = result['obx_observation_ref_range']
        normal_test_items.lab_test_comment = result['obx_observation_result_status']
        lab_test.save(ignore_permissions=True)
        idx+=1
    for i, item in enumerate(sorted(lab_test.normal_test_items, key=lambda item: item.lab_test_name), start=1):
        item.idx = i
    add_comment(reference_name=test_name, reference_doctype="Lab Test",content="HL7 Log Document {0}".format(log_name))


def get_template_name(analysis_name):
    lab_test_code = frappe.db.get_all('Lab Test Codes',filters={'analysis':analysis_name},fields=['lab_test_template'])
    if len(lab_test_code)>0:
        return lab_test_code[0]['lab_test_template']
    else:
        return analysis_name

# def get_template_name(analysis_list,template_name):
#     lab_test_code = frappe.db.get_all('Lab Test Codes',
#     filters={'analysis':['IN',analysis_list],'lab_test_template':template_name},fields=['lab_test_template'])
#     if len(lab_test_code)>0:
#         return lab_test_code[0]['lab_test_template']
#     else:
#         return ''

