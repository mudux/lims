
import json
import frappe
from lims.api.shoe4africa_lab.cobas_400 import get_lab_uom
from lims.api.utils.lab_test import create_random_test
from lims.api.utils.log_comments import add_comment
from lims.api.utils.template_update import save_test_uom, update_template_uom

@frappe.whitelist(allow_guest=True)
def process_yumizen550_hl7(HL7Message):
    message_log = frappe.new_doc('HL7 Message Logs')
    message_log.lab_station = 'SHOE 4 AFRICA'
    message_log.lab_machine = 'HORIBA YUMIZEN 550'
    message_log.hl7 = json.dumps(HL7Message)
    # message_log.order_number = obr_filler_order_sample_number
    message_log.save(ignore_permissions=True)
    # parse hl7 data
    hl7_data = frappe.db.get_value('HL7 Message Logs',{'name':message_log.get('name')},'hl7')
    result_data = json.loads(hl7_data)
    # print(str(result_data))
    if len(result_data)>1:
        pid_data = result_data["PID"] if result_data["PID"] else None
        patient_number = pid_data["PID.3"]["PID.3.1"] if pid_data["PID.3"] else 'No Patient Number'
        patient_dob = pid_data["PID.7"]["PID.7.1"] if pid_data["PID.7"] else 'No dob'
        patient_gender = pid_data["PID.8"]["PID.8.1"] if pid_data["PID.8"] else 'No Patient Number'
        patient_info={'patient_number':patient_number,'patient_dob': patient_dob,'patient_gender':patient_gender}
        spm_data = result_data["SPM"] if result_data["SPM"] else {}
        specimen_number = spm_data["SPM.2"]["SPM.2.1"] if spm_data["SPM.2"] else 'No specimen Number'
        specimen_type = spm_data["SPM.4"]["SPM.4.1"] if spm_data["SPM.4"] else 'No specimen Type'
        frappe.db.set_value('HL7 Message Logs',message_log.get('name'),{'order_number': specimen_number})
        obx_data_array = result_data["OBX"] if result_data["OBX"] else []
        parsed_obx = []
        custom_result = "<ol>"
        list_body='<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
        for obx_data in obx_data_array:
            obx_observation_set_id = obx_data["OBX.1"]["OBX.1.1"] if obx_data["OBX.1"] else 'No Set Id'
            obx_observation_value_type = obx_data["OBX.2"]["OBX.2.1"] if obx_data["OBX.2"] else 'No Observation Value Type'
            obx_observation_id = obx_data["OBX.3"]["OBX.3.1"] if obx_data["OBX.3"] else 'No Observation Id'
            obx_observation_loinc = obx_data["OBX.3"]["OBX.3.1"] if obx_data["OBX.3"] else 'No Observation loinc Id'
            obx_observation_analysis = obx_data["OBX.3"]["OBX.3.2"] if obx_data["OBX.3"] else 'No Observation loinc Id'
            obx_observation_value = obx_data["OBX.5"]["OBX.5.1"] if obx_data["OBX.5"] else 'No Observation Value'
            obx_observation_units = obx_data["OBX.6"]["OBX.6.1"] if obx_data["OBX.6"] else 'No Units'
            obx_observation_ref_range = obx_data["OBX.7"]["OBX.7.1"] if obx_data["OBX.7"] else 'No Range Data'
            # obx_observation_abnormal_flags = obx_data["OBX.8"][0] + ' '+ obx_data["OBX.8"][1] if  obx_data["OBX.8"] and len(obx_data["OBX.8"])>1 else 'No Abnormal flags'
            # obx_probability = obx_data["OBX.9"]["OBX.9.1"] if obx_data["OBX.9"] else 'No Probability'
            # obx_nature_of_abnormal_test = obx_data["OBX.10"]["OBX.10.1"] if obx_data["OBX.10"] else 'No Nature Of abnormal Test'
            # obx_observation_result_status = obx_data["OBX.11"]["OBX.11.1"] if obx_data["OBX.11"] else 'No Result Status'
            obj = {
                'obx_observation_set_id':obx_observation_set_id,
                'obx_observation_value_type':obx_observation_value_type,
                'obx_observation_loinc':obx_observation_loinc,
                'obx_observation_analysis':obx_observation_analysis,
                'obx_observation_id':obx_observation_id,
                'obx_observation_value':obx_observation_value,
                'obx_observation_units':obx_observation_units,
                'obx_observation_ref_range':obx_observation_ref_range,
                # 'obx_observation_abnormal_flags':obx_observation_abnormal_flags,
                # 'obx_probability':obx_probability,
                # 'obx_nature_of_abnormal_test':obx_nature_of_abnormal_test,
                # 'obx_observation_result_status':obx_observation_result_status
                }
            if obx_data["OBX.6"] and obx_data["OBX.7"]:
                parsed_obx.append(obj)
                # obx_observation_id
                custom_result += list_body + "{0}\t ({1}) {2}{3}\t ({4})</li>".format(get_template_name(obx_observation_analysis),obx_observation_id,obx_observation_value,obx_observation_units,obx_observation_ref_range)

        results =  {'parsed_obx':parsed_obx,'specimen_number':specimen_number,'specimen_type':specimen_type, 'patient_info':patient_info}
        frappe.db.set_value('HL7 Message Logs', message_log.get('name'),{'result_data': json.dumps(results)})
        lab_name = specimen_number #create_random_test()
        tests_sharing_sample_child =  frappe.db.get_all('Lab Test Sample Share',filters={'lab_test':['IN',lab_name]},fields=['name','lab_test','parent'])
        tests_sharing_sample_parent =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':lab_name},fields=['name','lab_test','parent'])
        tests_sharing_sample = tests_sharing_sample_parent or tests_sharing_sample_child
        if len(tests_sharing_sample)>0:
            parent_test = tests_sharing_sample[0]['parent']
            tests_sharing_sample =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':parent_test},fields=['name','lab_test'])
            for test in tests_sharing_sample:
                update_lab_test(test['lab_test'],custom_result,parsed_obx,message_log.get('name'))
            update_lab_test(lab_name,custom_result,parsed_obx,message_log.get('name'))
        else:
            update_lab_test(lab_name,custom_result,parsed_obx,message_log.get('name'))
            return message_log.get('name') # results
    else:
        return {'Incoplete data'}

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
        template_name = get_loinc_description(result['obx_observation_id']) #get_template_name(result['obx_observation_id'])
        save_test_uom(uom_value=result['obx_observation_units'],description=template_name)
        update_template_uom(template_name=template_name,uom_value=result['obx_observation_units'])
        
        normal_test_items = lab_test.append('normal_test_items')
        normal_test_items.idx = idx
        normal_test_items.lab_test_name = template_name
        normal_test_items.lab_test_event = result['obx_observation_id']
        normal_test_items.result_value = str(result['obx_observation_value'])
        normal_test_items.lab_test_uom = result['obx_observation_units'] #get_lab_uom(test_name)
        # normal_test_items.secondary_uom = result['']
        normal_test_items.normal_range = result['obx_observation_ref_range']
        normal_test_items.test_range =  result['obx_observation_ref_range']
        # normal_test_items.lab_test_comment = result['obx_observation_result_status']
        lab_test.save(ignore_permissions=True)
        idx+=1
    for i, item in enumerate(sorted(lab_test.normal_test_items, key=lambda item: item.lab_test_name), start=1):
        item.idx = i
    from frappe.model.workflow import apply_workflow
    if lab_test.get('workflow_state')=='Processing':
        apply_workflow(doc=lab_test, action="Forward For Verification")
    add_comment(reference_name=test_name, reference_doctype="Lab Test",content="HL7 Log Document {0}".format(log_name))

# descriptive_test_items
def get_template_name(analysis_name):
    lab_test_code = frappe.db.get_all('Lab Test Codes',filters={'analysis':analysis_name},fields=['lab_test_template'])
    if len(lab_test_code)>0:
        return lab_test_code[0]['lab_test_template']
    else:
        return analysis_name

def get_loinc_description(loinc_code):
    description  = frappe.db.get_value('Loinc Code',{'name':loinc_code},'description')
    return description if description else 'No loinc description'