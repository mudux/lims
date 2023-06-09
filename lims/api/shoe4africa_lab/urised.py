import json
import frappe
from lims.api.chandaria_lab.horiba import get_loinc_description
from lims.api.shoe4africa_lab.cobas_400 import get_lab_uom
from lims.api.shoe4africa_lab.yumizen_550 import get_template_name
from lims.api.utils.lab_test import create_random_test
from lims.api.utils.log_comments import add_comment
from lims.api.utils.template_update import save_test_uom, update_template_uom

@frappe.whitelist(allow_guest=True)
def process_urised_hl7(HL7Message):
    # port 9700  
    message_log = frappe.new_doc('HL7 Message Logs')
    message_log.lab_station = 'SHOE 4 AFRICA'
    message_log.lab_machine = 'URISED'
    message_log.hl7 = json.dumps(HL7Message)
    # message_log.order_number = obr_filler_order_sample_number
    message_log.save(ignore_permissions=True)
    # parse hl7 data
    hl7_data = frappe.db.get_value('HL7 Message Logs',{'name':message_log.get('name')},'hl7')
    result_data = json.loads(hl7_data)
    # print(str(result_data))
    pid_data = result_data["PID"] if result_data["PID"] else {}
    patient_name = pid_data["PID.5"]["PID.5.1"] if pid_data["PID.3"] else 'No Patient Number'
    patient_dob = pid_data["PID.3"]["PID.3.1"] if pid_data["PID.3"] else 'No Patient DOB'
    patient_info={'patient_name':patient_name,'patient_dob':patient_dob}
    spm_data = result_data["SPM"]
    specimen_number = spm_data["SPM.2"]["SPM.2.1"] if spm_data["SPM.2"] else 'No specimen Number'
    if frappe.db.exists('ASTM Message Logs',{'order_number':specimen_number}):
        # print('already logged')
        return frappe.db.get_value('ASTM Message Logs',{'order_number':specimen_number},'name')
    else:
        specimen_type = spm_data["SPM.4"]["SPM.4.1"] if spm_data["SPM.4"] else 'No specimen Type'
        # obr_data = result_data["OBR"]
        obx_data_array = result_data["OBX"]
        parsed_obx = []
        custom_result = "<ol>"
        list_body='<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
        for obx_data in obx_data_array:
            obx_observation_set_id = obx_data["OBX.1"]["OBX.1.1"] if obx_data["OBX.1"] else 'No Set Id'
            obx_observation_value_type = obx_data["OBX.2"]["OBX.2.1"] if obx_data["OBX.2"] else 'No Observation Value Type'
            obx_observation_id = obx_data["OBX.3"]["OBX.3.1"] if obx_data["OBX.3"] else 'No Observation Id'
            obx_observation_analysis = obx_data["OBX.3"]["OBX.3.2"] if obx_data["OBX.3"] else 'No Analysis'
            obx_observation_sub_id = obx_data["OBX.4"]["OBX.4.1"] if obx_data["OBX.4"] else 'No Observation Sub Id'
            obx_observation_value = obx_data["OBX.5"]["OBX.5.1"] if obx_data["OBX.5"] else 'No Observation Value'
            obx_observation_units = obx_data["OBX.6"]["OBX.6.1"] if obx_data["OBX.6"] else 'No Units'
            obx_observation_ref_range = obx_data["OBX.7"]["OBX.7.1"] if obx_data["OBX.7"] else 'No Range Data'
            # obx_observation_abnormal_flags = obx_data["OBX.8"][0] + ' '+ obx_data["OBX.8"][1] if  obx_data["OBX.8"] and len(obx_data["OBX.8"])>1 else 'No Abnormal flags'
            # obx_probability = obx_data["OBX.9"]["OBX.9.1"] if obx_data["OBX.9"] else 'No Probability'
            # obx_nature_of_abnormal_test = obx_data["OBX.10"]["OBX.10.1"] if obx_data["OBX.10"] else 'No Nature Of abnormal Test'
            # obx_observation_result_status = obx_data["OBX.11"]["OBX.11.1"] if obx_data["OBX.11"] else 'No Result Status'
            # create_template(obx_observation_id)
            obj = {
                'obx_observation_set_id':obx_observation_set_id,
                'obx_observation_value_type':obx_observation_value_type,
                'obx_observation_sub_id':obx_observation_sub_id,
                'obx_observation_id':obx_observation_id,
                'obx_observation_value':obx_observation_value,
                'obx_observation_units':obx_observation_units,
                'obx_observation_ref_range':obx_observation_ref_range,
                'obx_observation_analysis':obx_observation_analysis
                # 'obx_observation_abnormal_flags':obx_observation_abnormal_flags,
                # 'obx_probability':obx_probability,
                # 'obx_nature_of_abnormal_test':obx_nature_of_abnormal_test,
                # 'obx_observation_result_status':obx_observation_result_status
                }
            if obx_data["OBX.6"]:
                parsed_obx.append(obj)
                custom_result += list_body + "{0}\t ({1}) {2}{3}\t ({4})</li>".format(get_template_name(obx_observation_analysis),obx_observation_id,obx_observation_value,obx_observation_units,obx_observation_ref_range)
        results =  {'parsed_obx':parsed_obx,'specimen_number':specimen_number,'specimen_type':specimen_type, 'patient_info':patient_info}
        frappe.db.set_value('HL7 Message Logs', message_log.get('name'),{'result_data': json.dumps(results)})
        frappe.db.set_value('HL7 Message Logs',message_log.get('name'),{'order_number': specimen_number})
        message_log.reload()
        lab_name = specimen_number # 'NW' #specimen_number #message_log.get('order_number') #'NW' #create_random_test()
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
        return message_log.get('name')

def update_lab_test(test_name,custom_result,result_list,log_name):
    # frappe.db.set_value('Lab Test',test_name,{'custom_result': custom_result})
    if  frappe.db.exists('Lab Test',{'name':test_name}):
        loinc_codes = ['798-9','51487-7','53297-8','51484-4','51481-0','51480-2','51478-6','51486-9']
        loinc_ranges=['0-10','0-12','0-6','0-2','0-3','0-130','0-264','0-5']
        tests=['UROBILINOGEN','SPECIFIC GRAVITY (SG)','GLUCOSE','LEUKOCYTES-MICROSCOPY','KETONE','NITRITES','BILIRUBIN','BLOOD','PH','PROTEIN'] # prevent deletion of manual items
        lab_test = frappe.get_doc('Lab Test',test_name)
        normal_test_results =  frappe.db.get_all('Normal Test Result',filters={'parent':test_name,'lab_test_name':['NOT IN',tests]},fields=['name','lab_test_name'])
        lab_test.normal_toggle = 1
        for res in normal_test_results:
            frappe.delete_doc('Normal Test Result',res['name'])
        idx = 0
        sorted_results = result_list #sorted(result_list, key=lambda d: d['obx_observation_id'])
        for result in sorted_results:
            template_name = get_loinc_description(result['obx_observation_id'])
            if template_name != 'No loinc description' and result['obx_observation_id'] in loinc_codes:
                # save_test_uom(uom_value=result['obx_observation_units'],description=template_name)
                # update_template_uom(template_name=template_name,uom_value=result['obx_observation_units'])
                normal_test_items = lab_test.append('normal_test_items')
                # normal_test_items.idx = idx
                normal_test_items.lab_test_name = template_name #get_template_name(result['obx_observation_id'])
                # normal_test_items.lab_test_event = result['obx_observation_id']
                normal_test_items.result_value = str(result['obx_observation_value'])
                normal_test_items.lab_test_uom = result['obx_observation_units']  #get_lab_uom(test_name)
                # normal_test_items.secondary_uom = result['']
                normal_test_items.normal_range = loinc_ranges[loinc_codes.index(result['obx_observation_id'])] #result['obx_observation_ref_range']
                normal_test_items.test_range = loinc_ranges[loinc_codes.index(result['obx_observation_id'])] #result['obx_observation_ref_range']
                # normal_test_items.lab_test_comment = result['obx_observation_result_status']
                # idx+=1
        # for test in tests:
        #         # print(test)
        #         normal_test_items = lab_test.append('normal_test_items')
        #         normal_test_items.lab_test_name = test
        lab_test.save(ignore_permissions=True)
        from frappe.model.workflow import apply_workflow
        if lab_test.get('workflow_state')=='Processing':
            apply_workflow(doc=lab_test, action="Forward For Verification")
        add_comment(reference_name=test_name, reference_doctype="Lab Test",content="HL7 Log Document {0}".format(log_name))
