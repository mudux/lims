from warnings import filters
from billing.billing.api.sales_invoice.create_sales_invoice import re_eveluate_sales_orders
# from billing.billing.utils.payment_notifications import get_party_phone
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
    doc.patient_age = age_calc(dob,doc.name)
    doc.patient_sex = gender or sex 
    doc.save(ignore_permissions=True)
    enqueue(method=append_same_category_tests,name=doc.get('name'), queue='short', timeout=600)
    enqueue(method=tetst_age_fix, queue='short', timeout=600)
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

def age_calc(dob,lab_name=''):
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
        # if yearsInt>100:
        #     enqueue(method=log_error ,lab_name=lab_name,dob=dob, queue='short', timeout=600)
        # # print("{0}Y".format(yearsInt))
        # else:
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
    pats = frappe.get_all('Lab Test',fields=['name','patient'],filters={'patient':'1122083'})
    for p in pats:
        print(p['name'])
        dob = frappe.db.get_value('Patient',{ 'name': p['patient'] }, 'dob')
        # print(type(dob))
        print(str(dob))
        age = age_calc(dob,p['name'])
        print('age ',age)
        # frappe.db.set_value('Lab Test',p['name'],{'patient_age':age})

# bench execute lims.doc_hooks.lab_test.append_same_category_tests
@frappe.whitelist()
def append_same_category_tests(name):
    from mtrh_dev.mtrh_dev.utilities import get_link_to_form_new_tab
    # from clinical.hook.lab_test import get_sample_shares
    # name='3BQ'
    lab_doc = frappe.get_doc('Lab Test',name)
    sql="""select tlt.name,tlt.template,tlt.workflow_state,ltc.test_group,ltc.lab_test_template,tlt.patient from `tabLab Test` tlt RIGHT join `tabLab Test Codes` ltc on tlt.template=ltc.lab_test_template where  tlt.patient='{0}' and tlt.docstatus=0""".format(lab_doc.patient)
    # tlt.workflow_state='To Receive' and  and tlt.template='{1}' ,doc.template
    # print(sql)
    # link_arr=[]
    name_arr=[]
    res = frappe.db.sql(sql,as_dict=1)
    names = [x.name for x in res]
    for n in names:
        # link_arr.append(get_link_to_form_new_tab(doctype="Lab Test", name=n, label=n))
        name_arr.append({'name':get_link_to_form_new_tab(doctype="Lab Test", name=n, label=n) ,'Test':frappe.db.get_value('Lab Test',n,'template'),'workflow_state':frappe.db.get_value('Lab Test',n,'workflow_state')})
        update_sample_share(n,names)
    # frappe.msgprint(title='Labs Sharing Same Sample',msg=str(name_arr))
    get_sample_shares(name)
    return name_arr


def update_sample_share(name,names):
    lab_doc = frappe.get_doc('Lab Test',name)
    for n in names:
        if n!= lab_doc.get('name'):
            if not frappe.db.exists('Lab Test Sample Share',{'parent':name,'lab_test':n}):
                sample_share = lab_doc.append('lab_test_sample_share')
                sample_share.lab_test = n
                lab_doc.save(ignore_permissions=True)

def get_sample_shares(lab_name):
    tests_sharing_sample_child =  frappe.db.get_all('Lab Test Sample Share',filters={'lab_test':['IN',lab_name]},fields=['name','lab_test','parent'])
    tests_sharing_sample_parent =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':lab_name},fields=['name','lab_test','parent'])
    tests_sharing_sample = tests_sharing_sample_parent or tests_sharing_sample_child
    test_names = []
    if len(tests_sharing_sample)>0:
        parent_test = tests_sharing_sample[0]['parent']
        tests_sharing_sample =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':parent_test},fields=['name','lab_test'])
        for test in tests_sharing_sample:
            test_names.append(test['lab_test'])
        test_names.append(lab_name)
    else:
        test_names.append(lab_name)    
    shares = list(dict.fromkeys(test_names))
    process_lab_array= frappe.db.get_all('Lab Test',filters={'name':['IN',shares]},fields=['processing_lab'])
    employee_array = frappe.db.get_all('Lab Test',filters={'name':['IN',shares]},fields=['employee'])
    process_lab=''
    employee=''
    # print(str(process_lab))
    # print(str(employee))
    for l in process_lab_array:
        if l.processing_lab:
            process_lab = l.processing_lab
    for e in employee_array:
        if e.employee:
            employee = e.employee
    for n in shares:
        print(n)
        bulk_workflow_update(docname=n,process_lab=process_lab,employee=employee)
        
def bulk_workflow_update(docname,process_lab='',employee=''):
    from frappe.model.workflow import apply_workflow
    doc=frappe.get_doc('Lab Test',docname )#'IP'ß
    # print(get_sample_shares(doc.name))
    # actions=['Forward For Payment','Approve Payment','Send To Lab','Receive Lab Test','Forward For Verification']
    # state_action_dict=[
    #     { 'state':'Awaiting Checkin','action':actions[0]},
    #     { 'state':'Awaiting Payment','action':actions[1]},
    #     { 'state':'Awaiting Sampling','action':actions[2]},
    #     { 'state':'To receive','action':actions[3]},
    #     { 'state':'Processing','action':actions[4]},
    #     { 'state':'Awaiting Verification','action':actions[5]}
    # ]
    workflow_state = doc.get('workflow_state')
    if workflow_state=='Awaiting Checkin':
        apply_workflow(doc=doc, action="Forward For Payment")
    if workflow_state=='Awaiting Payment':
        # apply_workflow(doc=doc, action="Approve Payment")
        re_eveluate_sales_orders(patient_name=doc.patient,lab_name=doc.name)
        apply_workflow(doc=doc, action="Approve Payment")
    if workflow_state=='Awaiting Sampling':
        doc.processing_lab = process_lab
        doc.employee = employee
        doc.save(ignore_permissions=True)
        apply_workflow(doc=doc, action="Send To Lab")
    if workflow_state=='To receive':
        doc.processing_lab = process_lab
        doc.employee = employee
        doc.save(ignore_permissions=True)
        apply_workflow(doc=doc, action="Receive Lab Test")
    if workflow_state=='Processing':
        apply_workflow(doc=doc, action="Forward For Verification")
    if workflow_state=='Awaiting Verification':
        apply_workflow(doc=doc, action="Post Lab Test")
 
# bench execute lims.doc_hooks.lab_test.lab_clean
        
def lab_clean():
    sql = "select name,idx from `tabNormal Test Result` where parent='B73'"
    items=frappe.db.sql(sql,as_dict=1)
    count = 0
    for i in items:
        count +=1
        if count>1:
            sq= "delete from `tabNormal Test Result` where name='{0}'".format(i.name)
            frappe.db.sql(sq,as_dict=1)
            print(count)

# bench execute lims.doc_hooks.lab_test.comment_count            
def comment_count(name='B73'):
    return 1
    # sqlc="select count(name) as cnt,reference_name from tabComment where reference_doctype='Lab Test' and reference_name is not null group by reference_name HAVING COUNT(name) > 2 order by reference_name limit 5"
    # parents=frappe.db.sql(sqlc,as_dict=1)
    # for p in parents:
    #     print(p.reference_name, '  ',p.cnt)
    #     sql = "select name,reference_doctype,reference_name from tabComment where reference_name='{0}' limit 3".format(p.reference_name)
    #     print(sql)
    #     items=frappe.db.sql(sql,as_dict=1)
    #     count = 0
    #     for i in items:
    #         count +=1
    #         if count>1:
    #             print('item count ',count)
    #             # sq= "delete from tabComment where name='{0}'".format(i.name)
    #             # frappe.db.sql(sq,as_dict=1)
    #             frappe.delete_doc('Comment',i.name)
    #             frappe.db.commit()
    #             # print(count)

 # bench execute lims.doc_hooks.lab_test.tetst_age_fix              
def tetst_age_fix():
    sql = "select name,patient,docstatus from `tabLab Test` where patient_age is null;"
    labs = frappe.db.sql(sql,as_dict=1)
    for lab in labs:
        patient = lab.get('patient')
        # print(' patient ', patient)
        dob = frappe.db.get_value('Patient',{ 'name':patient }, 'dob')
        patient_age = age_calc(dob,lab.get('name'))
        # print(patient_age)
        up_sq = "update `tabLab Test` set patient_age ='{0}' where name='{1}';".format(patient_age,lab.get('name'))
        print(up_sq)
        frappe.db.sql(up_sq,as_dict=1)
        
def log_error(lab_name,dob):
    log  = frappe.new_doc('Lims Error Log')
    log.ordernumber  = lab_name
    log.log_number = ''
    log.unprocessed_result = str(dob)
    log.save(ignore_permissions=True)
    
# bench execute lims.doc_hooks.lab_test.patient_record_exist 
def patient_record_exist():
    # labs = frappe.get_all("Lab Test",filters={'docstatus':1},fields=['name','patient'])
    labs = frappe.db.count('Lab Test', {'docstatus': 1})
    recs = frappe.db.count('Patient Medical Record', {'reference_doctype': 'Lab Test'})
    print('labs ',labs, ' recs ',recs)