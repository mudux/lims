from billing.billing.utils.payment_notifications import get_party_phone
import frappe
from datetime import date
from frappe.utils.background_jobs import enqueue

from frappe.utils.data import nowdate

def calculate_age(birthDate):
    days_in_year = 365.2425
    age = int((date.today() - birthDate).days / days_in_year)
    return age

def lab_test_after_insert_hook(doc,state):
    patient = doc.get('patient')
    dob = frappe.db.get_value('Patient',{ 'name':patient }, 'dob')
    gender = frappe.db.get_value('Patient',{ 'name':patient }, 'gender')
    sex = frappe.db.get_value('Patient',{ 'name':patient }, 'sex')
    doc.patient_age = age_calc(dob)
    doc.patient_sex = gender or sex 
    doc.save(ignore_permissions=True)
    enqueue(method=append_same_category_tests,name=doc.get('name'), queue='short', timeout=600)
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

def age_calc(dob):
    currentDate = date.today()#nowdate() #datetime.datetime.now()
    # dob = '2022-05-01'
    # deadline= dob #input ('Plz enter your date of birth (mm/dd/yyyy) ')
    deadlineDate= dob# datetime.datetime.strptime(deadline,'%Y-%m-%d')
    # print (type(deadlineDate))
    # print (type(currentDate))

    daysLeft = currentDate - deadlineDate
    # print(daysLeft)

    years = ((daysLeft.total_seconds())/(365.242*24*3600))
    yearsInt=int(years)

    months=(years-yearsInt)*12
    monthsInt=int(months)

    days=(months-monthsInt)*(365.242/12)
    daysInt=int(days)

    hours = (days-daysInt)*24
    hoursInt=int(hours)
    if yearsInt>0:
        # print("{0}Y".format(yearsInt))
        return "{0}Y".format(yearsInt)
    if monthsInt>0:
        # print("{0}M".format(monthsInt))
        return "{0}M".format(monthsInt)
    if daysInt>0:
        # print("{0}D".format(daysInt))
        return "{0}D".format(daysInt)
    if hoursInt>0:
        # print("{0}H".format(hoursInt))
        return "{0}H".format(hoursInt)
    
# bench execute lims.doc_hooks.lab_test.age_test
def age_test():
    pats = frappe.get_all('Lab Test',filters={},fields=['name','patient'])
    for p in pats:
        print(p['name'])
        dob = frappe.db.get_value('Patient',{ 'name': p['patient'] }, 'dob')
        print(str(dob))
        age = age_calc(dob)
        frappe.db.set_value('Lab Test',p['name'],{'patient_age':age})

# bench execute lims.doc_hooks.lab_test.append_same_category_tests

def append_same_category_tests(name):
    # name='3BQ'
    lab_doc = frappe.get_doc('Lab Test',name)
    sql="""select tlt.name,tlt.template,tlt.workflow_state,ltc.test_group,ltc.lab_test_template,tlt.patient from `tabLab Test` tlt RIGHT join `tabLab Test Codes` ltc on tlt.template=ltc.lab_test_template where  tlt.patient='{0}' and tlt.docstatus=0""".format(lab_doc.patient)
    # tlt.workflow_state='To Receive' and  and tlt.template='{1}' ,doc.template
    # print(sql)
    res = frappe.db.sql(sql,as_dict=1)
    names = [x.name for x in res]
    # print(str(names))
    for n in names:
        sample_share = lab_doc.append('lab_test_sample_share')
        sample_share.lab_test = n
        lab_doc.save(ignore_permissions=True)
