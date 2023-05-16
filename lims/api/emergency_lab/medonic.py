
import frappe
import json
import re
from lims.api.shoe4africa_lab.medonic import get_template_name

@frappe.whitelist(allow_guest=True)
def process_medonic_hl7(HL7Message):
    return HL7Message

class LazyDecoder(json.JSONDecoder):
    def decode(self, s, **kwargs):
        regex_replacements = [
            (re.compile(r'([^\\])\\([^\\])'), r'\1\\\\\2'),
            (re.compile(r',(\s*])'), r'\1'),
        ]
        for regex, replacement in regex_replacements:
            s = regex.sub(replacement, s)
        return super().decode(s, **kwargs)

def remove_escape_sequences(string):
    return string.encode('utf-8').decode('unicode_escape')

# # bench execute lims.api.emergency_lab.medonic.sanitize_medonic_hl7

def sanitize_medonic_hl7():
    # json from mirth server is malformed, has to be sanitized before processing.
    # replaced = frappe.db.sql(" SELECT REPLACE(%s,%s,%s) as new_str",[HL7Message,'""""','""'],as_dict=1)
    field_list = ['lab_station','lab_machine','hl7_data','name']
    machine_name = 'MEDONIC-ERL'
    raw_hl7_docs  = frappe.get_all('Raw HL7', filters={'is_processed': 0,'has_error':0,'lab_machine':machine_name}, fields= field_list,order_by='creation asc')
    for doc in raw_hl7_docs:
        replaced = frappe.db.sql(" SELECT REPLACE(%s,%s,%s) as new_str",[doc.get('hl7_data'),'""""','""'],as_dict=1)
        parsed_data = replaced[0].get('new_str')[1:-1]
        # print(parsed_data)
        frappe.db.sql("update `tabRaw HL7` set hl7_data = '%s' where name='%s' ",[parsed_data,doc.get('name')])
        print(doc.get('name'))
    
# bench execute lims.api.emergency_lab.medonic.process_medonic_hl7
def process_medonic_hl7():
    # hl7_data = frappe.db.sql("select name from `tabRaw HL7` where lab_machine='MEDONIC-ERL' and is_processed=0",as_dict=1)
    field_list = ['lab_station','lab_machine','hl7_data','name']
    machine_name = 'MEDONIC-ERL'
    raw_hl7_docs  = frappe.get_all('Raw HL7', filters={'is_processed': 0,'has_error':0,'lab_machine':machine_name}, fields= field_list,order_by='creation asc',start=0,page_length=5)
    print(len(raw_hl7_docs))
    for doc in raw_hl7_docs:
        process_medonic_data(doc.get('hl7_data'),doc.name)

def process_medonic_data(HL7Message,raw_name):
    replaced = frappe.db.sql(" SELECT REPLACE(%s,%s,%s) as new_str",[HL7Message,'""""','""'],as_dict=1)
    message_log = frappe.new_doc('HL7 Message Logs')
    message_log.lab_station = 'ROUTINE-LAB'
    message_log.lab_machine = 'MEDONIC'
    frappe.db.sql("update `tabRaw HL7` set is_processed=1,has_error=1 where name='{0}' ".format(raw_name))
    frappe.db.commit()
    parsed_data = replaced[0].get('new_str')[1:-1]
    result_data = json.loads(remove_escape_sequences(rf"""{parsed_data}"""), cls=LazyDecoder)
    message_log.hl7 = json.dumps(result_data)
    message_log.save(ignore_permissions=True)
    # START PROCESSING HL7 DATA
    main_body = result_data["HL7Message"]
    obr_data = main_body["OBR"]
    obr_filler_order_sample_number = obr_data["OBR.3"]["OBR.3.1"] if obr_data["OBR.3"] else 'No Filler Order Number'
    obr_universal_service_id = obr_data["OBR.4"]["OBR.4.1"] if obr_data["OBR.4"] else 'No universal Service Id'
    obr_result_time = obr_data["OBR.22"]["OBR.22.1"] if obr_data["OBR.22"] else 'No result Time'
    nte_data = main_body["NTE"]
    nte_comment = nte_data["NTE.3"]["NTE.3.1"] if nte_data["NTE.3"] else 'No Coment segment'
    # add order number to log
    frappe.db.set_value('HL7 Message Logs',message_log.get('name'),{'order_number': obr_filler_order_sample_number})
    obx_data_array = main_body["OBX"] if main_body["OBX"] else [] 
    parsed_obx = []
    custom_result = 'cr'
    td = ''
    tail=""" </tbody></table></div>"""
    head="""<div class="ql-editor read-mode"><table class="table table-bordered" WIDTH="100%"><tbody><tr><td data-row="insert-column-right"><strong>Test</strong></td><td data-row="insert-column-right"><strong>Result</strong></td><td data-row="insert-column-right"><strong>Range</strong></td></tr>"""
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
            td+='<tr>'
            td+= """<td width="50%">{0}</td>""".format(get_template_name(obx_observation_id))
            td+="""<td width="25%">{0} {1}</td>""".format(obx_observation_value,obx_observation_units)
            td+="""<td width="25%">{0}</td> </tr>""".format(obx_observation_ref_range)
            # td += list_body + "{0}\t {1} {2}{3}\t ({4})</li>".format(,obx_observation_id,obx_observation_value,obx_observation_units,obx_observation_ref_range)
    result_table =  head + td + tail
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
    if frappe.db.exists("Patient",{'name':obr_universal_service_id}):
        create_pmr(result_data=result_table,sample_number=obr_filler_order_sample_number,patient=obr_universal_service_id)
  
    
def create_pmr(result_data,sample_number,patient):
    patient_record = frappe.new_doc('Patient Medical Record')
    # patient_record.subject = '<strong>Full Hemogram Results sample #({0}): </strong>'.format(sample_number) + '\n' + '\n'
    patient_record.patient = patient
    patient_record.subject =  '<strong>Full Hemogram Results sample #({0}): </strong><br>'.format(sample_number) + '\n' + result_data
    patient_record.reference_doctype = 'Lab Test'
    patient_record.reference_name = '6X2' #doc.get('name')
    patient_record.reference_owner = frappe.session.user
    patient_record.user = frappe.session.user   
    patient_record.reference_service_unit = 'Ambulatory Triage - MTRH' #doc.get('healthcare_service_unit') 
    patient_record.save(ignore_permissions=True)

# bench execute lims.api.emergency_lab.medonic.clear_medonic_hl7
def clear_medonic_hl7():
    data = frappe.db.sql("select name from `tabRaw HL7`",as_dict=1)
    for d in data:
        frappe.db.sql("delete from `tabRaw HL7` where name='{0}'".format(d.name))
        print(d.name)
    print(len(data))