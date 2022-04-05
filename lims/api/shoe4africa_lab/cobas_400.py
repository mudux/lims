
from datetime import datetime, date
from unittest import result
from lims.api.utils.lab_test import create_random_test
from lims.api.utils.log_comments import add_comment
from lims.api.utils.template_update import save_test_uom, update_template_uom
import requests
import frappe
import json

def calculate_age(birthDate):
    days_in_year = 365.2425
    age = int((date.today() - birthDate).days / days_in_year)
    return age

def get_template_name(lab_name):
    # astm_codes=['592','551','495','609','712']
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
    templates = frappe.db.get_all('Lab Test',filters={'name': ['IN', test_names]},fields=['template'])
    template_names = [x.template for x in templates]
    # lab_test_code = frappe.db.get_all('Lab Test Codes',filters={'astm_code': ['IN', astm_codes]},fields=['lab_test_template','analysis','astm_code'])
    lab_test_code = frappe.db.get_all('Lab Test Codes',filters={'lab_test_template': ['IN',template_names ]},fields=['lab_test_template','analysis','astm_code'])
    return lab_test_code

@frappe.whitelist(allow_guest=True)
def get_test_name(OrderNumber):
    data = get_template_name(OrderNumber)
    return data

@frappe.whitelist(allow_guest=True)
def get_order_details(OrderNumber):
    # test = create_random_test() # will use order# to get lab test
    # sql = "select name from `tabLab Test` ORDER BY RAND () LIMIT 1;"
    # test = frappe.db.sql(sql,as_dict=1)
    url = 'http://172.16.0.45:9002'
    # lab_test = frappe.get_doc('Lab Test',test[0]['name'])
    lab_test = frappe.get_doc('Lab Test',OrderNumber)

    myobj = {
        'order_number': OrderNumber,
        'patient_name': lab_test.get('patient_name'),
        'age': lab_test.get('patient_age'),
        'gender': lab_test.get('patient_sex'),
        'lab_test': lab_test.get('lab_test_name'),
        'status': lab_test.get('status'),
        'invoiced':'yes' if lab_test.get('invoiced')== 1 else 'No',
        'practitioner_name':lab_test.get('practitioner_name'),
        'lab_test_name':lab_test.get('name'),
        'test_codes': get_template_name(lab_test.get('name')) 
        #get_template_name(['592','551','495','609','712'])
    }
    x = requests.post(url, json = json.dumps(myobj))
    return {'message':'it works'}

@frappe.whitelist(allow_guest=True)
def save_cobas_results(orderResult,OrderCount,ResultCount):
    if orderResult['OrderNumber']:
        message_log = frappe.new_doc('ASTM Message Logs')
        message_log.lab_station = 'SHOE 4 AFRICA'
        message_log.lab_machine = 'COBAS INTEGRA 400'
        message_log.order_number = orderResult['OrderNumber'] or 'HLC-LAB-2022-00024'
        message_log.astm = json.dumps({'orderResult':orderResult})
        message_log.save(ignore_permissions=True)
        message_log.reload()
        process_astm_result(message_log.get('name'))
        return {'message':'Results Posted Succesfully','payload':{'orderResult':orderResult,'ResultCount':ResultCount,'OrderCount':OrderCount,'processed':message_log.get('result_data')}}
    else:
        return {'message':'Results Missing Data'}

def process_astm_result(log_name):
    # logs = frappe.db.get_all('ASTM Message Logs',filters={},fields=['*'])
    sql = "select name from `tabLab Test` ORDER BY RAND () LIMIT 1;"
    test = frappe.db.sql(sql,as_dict=1)
    # lab_name = test[0]['name'] #create_random_test() #'HLC-LAB-2022-00024'
    lab_name = create_random_test() #'HLC-LAB-2022-00024'
    # test_sharing_sample_with = frappe.db.get_value('Lab Test',{'name':lab_name},'share_sample_with')
    astm_data = frappe.db.get_value('ASTM Message Logs',{'name':log_name},'astm')
    orderResult = json.loads(astm_data)
    if orderResult and 'orderResult' in orderResult:
        orderNumber = orderResult['orderResult']['OrderNumber']
        OrderDate = orderResult['orderResult']['OrderDate'] if 'OrderDate' in orderResult else '00/00/0000'
        Orders = orderResult['orderResult']['Orders']
        Result = orderResult['orderResult']['Result']
        Uom = orderResult['orderResult']['Uom']
        Ranges = orderResult['orderResult']['Ranges']
        # output = "{0} processed {1} res {2}".format(orderNumber,log_name,Result)
        # print(output)
        results = append_order_to_test_and_results(Orders,Result,Uom,Ranges)
        # print("result {0} {1}".format(orderNumber,str(results)))
        sorted_results = sorted(results, key=lambda d: d['template_name']) 
        frappe.db.set_value('ASTM Message Logs', log_name,{'result_data': json.dumps(sorted_results)})
        tests_sharing_sample_child =  frappe.db.get_all('Lab Test Sample Share',filters={'lab_test':['IN',lab_name]},fields=['name','lab_test','parent'])
        tests_sharing_sample_parent =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':lab_name},fields=['name','lab_test','parent'])
        tests_sharing_sample = tests_sharing_sample_parent or tests_sharing_sample_child
        if len(tests_sharing_sample)>0:
            parent_test = tests_sharing_sample[0]['parent']
            tests_sharing_sample =  frappe.db.get_all('Lab Test Sample Share',filters={'parent':parent_test},fields=['name','lab_test'])
            for test in tests_sharing_sample:
                set_lab_test_result(log_name=log_name, test_name=test['lab_test'],result_list=sorted_results)
                # add_descriptive_result_items(test_name=test['lab_test'],results=sorted_results)
            set_lab_test_result(log_name=log_name, test_name=lab_name,result_list=sorted_results)
            # add_descriptive_result_items(test_name=lab_name,results=sorted_results)
        else:
            set_lab_test_result(log_name=log_name, test_name=lab_name,result_list=sorted_results)
        # set_lab_test_result(log_name=log_name, test_name=lab_name,result_list=sorted_results)
        # if test_sharing_sample_with:
        # # get test template to filter results
        #     set_lab_test_result(log_name=log_name, test_name=test_sharing_sample_with,result_list=sorted_results)



def append_order_to_test_and_results(orderlist,resultList,Uom,Ranges):
    if len(orderlist) == len(resultList):
        order_names = []
        for index in range(0,len(orderlist)):
            lab_test_code = frappe.db.get_all('Lab Test Codes',filters={'astm_code':orderlist[index]},fields=['lab_test_template','analysis'])
            # print('lab_test_code {0} idx {1}'.format(lab_test_code, orderlist[index]))
            if len(lab_test_code)>0:
                order_names.append({
                    'astm_code':orderlist[index],
                    'template_name':lab_test_code[0]['lab_test_template'],
                    'analysis':lab_test_code[0]['analysis'],
                    'results':resultList[index],
                    'range':Ranges[index],
                    'uom':Uom[index]})
            # print('order_names {0}'.format(order_names))
        return order_names
    else:
        return "Order/results mismatch"

def set_lab_test_result(log_name,test_name,result_list=[]):
    custom_result = "<ol>"
    list_body='<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
    lab_test = frappe.get_doc('Lab Test',test_name)
    lab_test.normal_toggle = 1
    normal_test_results =  frappe.db.get_all('Normal Test Result',filters={'parent':test_name},fields=['name','lab_test_name'])
    for res in normal_test_results:
        frappe.delete_doc('Normal Test Result',res['name'])
    idx = 0
    sorted_results = sorted(result_list, key=lambda d: d['template_name']) 
    for result in sorted_results:
        subString = "E+99"
        result_value = result['results'][0:4] if subString in ['results'] else float(result['results'])
        formatted_result ='{:.{}f}'.format(result_value,2)
        save_test_uom(uom_value=result['uom'],description=result['template_name'])
        update_template_uom(template_name=result['template_name'],uom_value=result['uom'])
        normal_test_items = lab_test.append('normal_test_items')
        normal_test_items.idx = idx
        normal_test_items.lab_test_name = result['template_name']
        normal_test_items.lab_test_event = result['analysis']
        normal_test_items.result_value = "{0}".format(formatted_result) #,result['uom'])
        normal_test_items.lab_test_uom =  result['uom'] #get_lab_uom(test_name)
        normal_test_items.normal_range = result['range']
        normal_test_items.lab_test_comment = 'NA'
        lab_test.save(ignore_permissions=True)
        custom_result += list_body + "{0}\t{1}\t{2} {3} {4}</li>".format(result['template_name'], result['analysis'],formatted_result,result['uom'],result['range'])
    idx+=1
    frappe.db.set_value('Lab Test',test_name,{'custom_result': custom_result})
    add_comment(reference_name=test_name, reference_doctype="Lab Test",content="ASTM Log Document {0}".format(log_name))
    # pass


def process_astm_results():
    logs = frappe.db.get_all('ASTM Message Logs',filters={},fields=['*'])
    for log in logs:
        orderResult = json.loads(log.get('astm'))
        if orderResult and 'orderResult' in orderResult:
            orderNumber = orderResult['orderResult']['OrderNumber']
            OrderDate = orderResult['orderResult']['OrderDate'] if 'OrderDate' in orderResult else '00/00/0000'
            Orders = orderResult['orderResult']['Orders']
            Result = orderResult['orderResult']['Result']
            Uom = orderResult['orderResult']['Uom']
            output = "{0} processed {1}".format(orderNumber,log.get('name'))
            # print(output)
            results = append_order_to_test_and_results(Orders,Result,Uom)
            # print("{0} {1}".format(orderNumber,str(results)))
            frappe.db.set_value('ASTM Message Logs', log.get('name'),{'result_data': json.dumps(results)})

def get_lab_uom(lab_name):
    template = frappe.db.get_value('Lab Test',{'name':lab_name},'template')
    lab_test_uom = frappe.db.get_value('Lab Test Template',{'name':template},'lab_test_uom')
    secondary_uom = frappe.db.get_value('Lab Test Template',{'name':template},'secondary_uom')
    # print("Fetch Lab Test UOM {0} UOM {1}".format(template,lab_test_uom))
    return lab_test_uom or secondary_uom

def import_loinc():
    from lims.api.utils.loinc_import import get_loinc
    loinc_codes = get_loinc() 
    count = 0
    for loinc_code in loinc_codes:
        code = dict(loinc_code)
        args =  {
            "doctype": "Loinc Code",
            "code": code['Code'],
            "description": code['Description'],
            "property": code['Property'],
            "class": code['Class'],
            "units_required": code['Units Required'],
            "related_names": code['Related Names'],
            "short_name": code['Short Name'],
            "order_obs":code['Order Obs'],
            "uom":code['UOM']
        }
        # print(args)
        doc = frappe.get_doc(args).insert()
        count+=1
        print("code {0} cnt {1}".format(code['Code'],count))
    print('complete')

# lab types posting to patient chart
# 
# def add_descriptive_result_items(test_name,results):
#     # results to contain template/value/uom/ranges
#     lab_test = frappe.get_doc('Lab Test',test_name)
#     # frappe.db.set_value('Lab Test', test_name,{'descriptive_toggle': 1})
#     # sql = "update `tabLab Test` set descriptive_toggle=1 where name='{0}';".format(test_name)
#     # frappe.db.sql(sql,as_dict=1)
#     # frappe.db.set_value('Lab Test', test_name,{'sensitivity_toggle': 1})
#     # frappe.db.set_value('Lab Test', test_name,{'normal_toggle': 1})
#     lab_test.descriptive_toggle=1
#     lab_test.normal_toggle = 1
#     idx = 0
#     for _result in results:
#         subString = "E+99"
#         result_value = _result['results'][0:4] if subString in ['results'] else float(_result['results'])
#         formatted_result ='{:.{}f}'.format(result_value,2)
#         descriptive_test_items = lab_test.append('descriptive_test_items')
#         descriptive_test_items.idx = idx
#         descriptive_test_items.lab_test_particulars = _result['template_name']
#         descriptive_test_items.template = _result['template_name']
#         descriptive_test_items.result_value =  "{0}".format(formatted_result)
#         lab_test.save(ignore_permissions=True)
#         idx+=1
#     for i, item in enumerate(sorted(lab_test.descriptive_test_items, key=lambda item: item.template), start=1):
#         item.idx = i

# def add_organism_test_items(lab_test,results):
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
#     for _result in results:
#         sensitivity_test_items = lab_test.append('sensitivity_test_items')
#         sensitivity_test_items.idx = idx
#         sensitivity_test_items.antibiotic =  _result['template_name']
#         sensitivity_test_items.antibiotic_sensitivity='colony_population'
#         lab_test.save(ignore_permissions=True)
#         idx+=1
#     for i, item in enumerate(sorted(lab_test.sensitivity_test_items, key=lambda item: item.template), start=1):
#         item.idx = i