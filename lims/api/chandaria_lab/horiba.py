import json
from erpnext.healthcare.doctype.lab_test.lab_test import create_sample_collection
import frappe
from frappe.utils import getdate
from lims.api.shoe4africa_lab.cobas_400 import get_lab_uom
# from lims.api.shoe4africa_lab.urised import create_template_from_loinc
from lims.api.shoe4africa_lab.yumizen_550 import get_template_name
from lims.api.utils.lab_test import create_random_test
from lims.api.utils.log_comments import add_comment
from lims.api.utils.template_update import save_test_uom, update_template_uom

# https://lyniate.com/resources/hl7-msh-message-header/
# https://hl7.org/fhir/uv/v2mappings/2020Sep/ConceptMap-segment-spm-to-specimen.html
@frappe.whitelist(allow_guest=True)
def process_horiba_hl7(HL7Message):
    message_log = frappe.new_doc('HL7 Message Logs')
    message_log.lab_station = 'CHANDARIA'
    message_log.lab_machine = 'YUMIZEN-HORIBA-550'
    message_log.hl7 = json.dumps(HL7Message)
    message_log.save(ignore_permissions=True)
    # parse hl7 data
    hl7_data = frappe.db.get_value('HL7 Message Logs',{'name':message_log.get('name')},'hl7')
    result_data = json.loads(hl7_data)
    pid_data = result_data["PID"]
    patient_number = pid_data["PID.3"]["PID.3.1"] if pid_data["PID.3"] else 'No Patient Number'
    patient_dob = pid_data["PID.7"]["PID.7.1"] if pid_data["PID.7"] else 'No Patient DOB'
    patient_info={'patient_number':patient_number,'patient_dob':patient_dob}
    spm_data = result_data["SPM"]
    specimen_number = spm_data["SPM.2"]["SPM.2.1"] if spm_data["SPM.2"] else 'No specimen Number'
    specimen_type = spm_data["SPM.4"]["SPM.4.1"] if spm_data["SPM.4"] else 'No specimen Type'
    obr_data = result_data["OBR"]
    result_time = obr_data["OBR.22"]["OBR.22.1"] if obr_data["OBR.22"] else 'No result time'
    result_status = obr_data["OBR.25"]["OBR.25.1"] if obr_data["OBR.25"] else 'No result status'
    frappe.db.set_value('HL7 Message Logs',message_log.get('name'),{'order_number': specimen_number})
    nte_data_array = result_data["NTE"]["NTE.3"] if  result_data["NTE"] else []
    parsed_nte = []
    for nte_data in nte_data_array:
        parsed_nte.append(nte_data)
        # nte_source = nte_data["NTE.3.2"] if nte_data["NTE.3.2"] else 'No Source'
        # nte_comment = nte_data["NTE.3.3"] if nte_data["NTE.3.3"] else 'No comment'
        # parsed_nte.append({'nte_source':nte_source,'nte_comment':nte_comment})
    # return HL7Message  'nte_data_array':nte_data_array,'parsed_nte':parsed_nte,
    obx_data_array = result_data["OBX"]
    parsed_obx = []
    custom_result = "<ol>"
    list_body='<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
    for obx_data in obx_data_array:
        obx_observation_set_id = obx_data["OBX.1"]["OBX.1.1"] if obx_data["OBX.1"] else 'No Set Id'
        obx_observation_value_type = obx_data["OBX.2"]["OBX.2.1"] if obx_data["OBX.2"] else 'No Observation Value Type'
        obx_observation_id = obx_data["OBX.3"]["OBX.3.1"] if obx_data["OBX.3"] else 'No Observation Id'
        obx_observation_sub_id = obx_data["OBX.4"]["OBX.4.1"] if obx_data["OBX.4"] else 'No Observation Sub Id'
        obx_observation_value = obx_data["OBX.5"]["OBX.5.1"] if obx_data["OBX.5"] else 'No Observation Value'
        obx_observation_units = obx_data["OBX.6"]["OBX.6.1"] if obx_data["OBX.6"] else 'No Units'
        obx_observation_ref_range = obx_data["OBX.7"]["OBX.7.1"] if obx_data["OBX.7"] else 'No Range Data'
        # obx_observation_abnormal_flags = obx_data["OBX.8"][0] + ' '+ obx_data["OBX.8"][1] if  obx_data["OBX.8"] and len(obx_data["OBX.8"])>1 else 'No Abnormal flags'
        # obx_probability = obx_data["OBX.9"]["OBX.9.1"] if obx_data["OBX.9"] else 'No Probability'
        # obx_nature_of_abnormal_test = obx_data["OBX.10"]["OBX.10.1"] if obx_data["OBX.10"] else 'No Nature Of abnormal Test'
        # obx_observation_result_status = obx_data["OBX.11"]["OBX.11.1"] if obx_data["OBX.11"] else 'No Result Status'
        # create_template_from_loinc(obx_observation_id)
        obj = {
            'obx_observation_set_id':obx_observation_set_id,
            'obx_observation_value_type':obx_observation_value_type,
            'obx_observation_sub_id':obx_observation_sub_id,
            'obx_observation_id':obx_observation_id,
            'obx_observation_value':obx_observation_value,
            'obx_observation_units':obx_observation_units,
            'obx_observation_ref_range':obx_observation_ref_range,
            'loinc_description':get_loinc_description(obx_observation_id)
            # 'obx_observation_abnormal_flags':obx_observation_abnormal_flags,
            # 'obx_probability':obx_probability,
            # 'obx_nature_of_abnormal_test':obx_nature_of_abnormal_test,
            # 'obx_observation_result_status':obx_observation_result_status
            }
        if obx_data["OBX.6"] and obx_data["OBX.7"]:
            parsed_obx.append(obj)
            custom_result += list_body + "{0}\t ({1}) {2}{3}\t ({4})</li>".format(get_loinc_description(obx_observation_id),obx_observation_id,obx_observation_value,obx_observation_units,obx_observation_ref_range)

    results =  {'parsed_obx':parsed_obx,'specimen_number':specimen_number,'specimen_type':specimen_type, 'patient_info':patient_info}
    frappe.db.set_value('HL7 Message Logs', message_log.get('name'),{'result_data': json.dumps(results)})
    lab_name = create_random_test()
    tests_sharing_sample_child =  frappe.db.get_all('Lab Test Sample Share',filters={'lab_test':['IN',lab_name]},fields=['name','lab_test','parent'])
    tests_sharing_sample_parent =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':lab_name},fields=['name','lab_test','parent'])
    tests_sharing_sample = tests_sharing_sample_parent or tests_sharing_sample_child
    if len(tests_sharing_sample)>0:
        parent_test = tests_sharing_sample[0]['parent']
        tests_sharing_sample =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':parent_test},fields=['name','lab_test'])
        for test in tests_sharing_sample:
            # add_descriptive_result_items(test['lab_test'],parsed_obx)
            update_lab_test(test['lab_test'],custom_result,parsed_obx,message_log.get('name'))
        update_lab_test(lab_name,custom_result,parsed_obx,message_log.get('name'))
        # add_descriptive_result_items(test['lab_test'],parsed_obx)
    else:
        update_lab_test(lab_name,custom_result,parsed_obx,message_log.get('name'))
    return results

def get_loinc_description(loinc_code):
    description  = frappe.db.get_value('Loinc Code',{'name':loinc_code},'description')
    return description if description else 'No loinc description'

def update_lab_test(test_name,custom_result,result_list,log_name):
    frappe.db.set_value('Lab Test',test_name,{'custom_result': custom_result})
    lab_test = frappe.get_doc('Lab Test',test_name)
    lab_test.normal_toggle = 1
    normal_test_results =  frappe.db.get_all('Normal Test Result',filters={'parent':test_name},fields=['name','lab_test_name'])
    for res in normal_test_results:
        frappe.delete_doc('Normal Test Result',res['name'])
    idx = 0
    sorted_results = sorted(result_list, key=lambda d: d['obx_observation_id'])
    for result in sorted_results:
        save_test_uom(uom_value=result['obx_observation_units'],description=result['loinc_description'])
        update_template_uom(template_name=result['loinc_description'],uom_value=result['obx_observation_units'])
        normal_test_items = lab_test.append('normal_test_items')
        normal_test_items.idx = idx
        normal_test_items.lab_test_name = result['loinc_description'] #get_template_name(result['obx_observation_id'])
        normal_test_items.lab_test_event = result['obx_observation_id']
        normal_test_items.result_value = str(result['obx_observation_value'])
        normal_test_items.lab_test_uom =  result['obx_observation_units'] #get_lab_uom(test_name)
        # normal_test_items.secondary_uom = result['']
        normal_test_items.normal_range = result['obx_observation_ref_range']
        # normal_test_items.lab_test_comment = result['obx_observation_result_status']
        lab_test.save(ignore_permissions=True)
        idx+=1
    for i, item in enumerate(sorted(lab_test.normal_test_items, key=lambda item: item.lab_test_name), start=1):
        item.idx = i
    add_comment(reference_name=test_name, reference_doctype="Lab Test",content="HL7 Log Document {0}".format(log_name))

# def add_descriptive_result_items(test_name,results):
#     # results to contain template/value/uom/ranges
#     lab_test = frappe.get_doc('Lab Test',test_name)
#     frappe.db.set_value('Lab Test', test_name,{'descriptive_toggle': 1})
#     idx = 0
#     for _result in results:
#         if   _result['loinc_description'] != 'Basophils':
#             descriptive_test_items = lab_test.append('descriptive_test_items')
#             descriptive_test_items.idx = idx
#             descriptive_test_items.template =  _result['loinc_description']
#             descriptive_test_items.result_value = str(_result['obx_observation_value'])
#             lab_test.save(ignore_permissions=True)
#             idx+=1
#     for i, item in enumerate(sorted(lab_test.descriptive_test_items, key=lambda item: item.template), start=1):
#         item.idx = i

# def add_organism_test_items(lab_test,results):
#     frappe.db.set_value('Lab Test', lab_test.get('name'),{'descriptive_toggle': 1})
#     idx = 0
#     for _result in results:
#         organism_test_items = lab_test.append('organism_test_items')
#         organism_test_items.idx = idx
#         organism_test_items.organism =  _result['template_name']
#         organism_test_items.colony_population='colony_population'
#         organism_test_items.colony_uom = 'colony_uom'
#         lab_test.save(ignore_permissions=True)
#         idx+=1
#     for i, item in enumerate(sorted(lab_test.organism_test_items, key=lambda item: item.organism), start=1):
#         item.idx = i

# def add_sensitivity_test_items(lab_test,results):
#     idx = 0
#     frappe.db.set_value('Lab Test', lab_test.get('name'),{'sensitivity_toggle': 1})
#     for _result in results:
#         sensitivity_test_items = lab_test.append('sensitivity_test_items')
#         sensitivity_test_items.idx = idx
#         sensitivity_test_items.antibiotic =  _result['template_name']
#         sensitivity_test_items.antibiotic_sensitivity='colony_population'
#         lab_test.save(ignore_permissions=True)
#         idx+=1
#     for i, item in enumerate(sorted(lab_test.sensitivity_test_items, key=lambda item: item.template), start=1):
#         item.idx = i
