from cgi import test
import random
import frappe

def create_random_test():
    lab_test = frappe.new_doc('Lab Test')
    rand_temp = random_template() #'Liver Function' #
    lab_test.template = rand_temp
    lab_test.lab_test_name = rand_temp
    lab_test.department = 'radiology'
    patient = random_patient()
    lab_test.patient = patient['name']
    lab_test.patient_name = patient['patient_name']
    lab_test.patient_age = random.randint(1, 100 - 1)
    lab_test.patient_sex = patient['gender'] or patient['sex']
    lab_test.practitioner = 'HLC-PRAC-2021-00003'
    lab_test.practitioner_name = 'duncan Namakoto'
    lab_test.requesting_department = 'radiology'
    shares = append_sample_share()
    for x in shares:
        shared_sample = lab_test.append('lab_test_sample_share')
        shared_sample.lab_test = x['name']
    lab_test.save(ignore_permissions=True)
    lab_test.reload()
    return lab_test.get('name')

def append_sample_share():
    sql = "select name from `tabLab Test` order by creation desc limit 3 offset 1;"
    tests = frappe.db.sql(sql,as_dict=1)
    return tests


def random_patient():
    sql = "select name,patient_name, sex,dob,gender from tabPatient order by RAND() LIMIT 1"
    pat = frappe.db.sql(sql,as_dict=1)
    return pat[0]

def random_template():
    sql = "select name from `tabLab Test Template` order by RAND() LIMIT 1"
    test = frappe.db.sql(sql,as_dict=1)
    lab_test = test[0]
    return lab_test['name']