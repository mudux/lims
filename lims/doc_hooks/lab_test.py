import frappe
from datetime import datetime, date

def calculate_age(birthDate):
    days_in_year = 365.2425
    age = int((date.today() - birthDate).days / days_in_year)
    return age

def lab_test_after_insert_hook(doc,state):
    patient = doc.get('patient')
    dob = frappe.db.get_value('Patient',{ 'name':patient }, 'dob')
    gender = frappe.db.get_value('Patient',{ 'name':patient }, 'gender')
    sex = frappe.db.get_value('Patient',{ 'name':patient }, 'sex')
    doc.patient_age = calculate_age(dob)
    doc.patient_sex = gender or sex 
    doc.save(ignore_permissions=True)
    # test_sharing_sample_with = doc.get('share_sample_with')
    # frappe.msgprint("sharing sample  " + test_sharing_sample_with)
    # if test_sharing_sample_with:
    #     frappe.db.set_value('Lab Test', test_sharing_sample_with,{'share_sample_with': doc.name})
    # tests_sharing_sample =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':doc.name},fields=['name','lab_test'])
    # if len(tests_sharing_sample)>0:
    #     for test in tests_sharing_sample:
    #         lab_test = frappe.get_doc('Lab Test',test['lab_test'])
    #         test_item = lab_test.append('lab_test_sample_share')
    #         test_item.lab_test = test['lab_test']
    #         lab_test.save(ignore_permissions=True)
    #     frappe.msgprint('updated related')
