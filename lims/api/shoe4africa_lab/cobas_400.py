from datetime import datetime, date
from unittest import result
from lims.api.utils.lab_test import create_random_test
from lims.api.utils.log_comments import add_comment
from lims.api.utils.sms_notify import notify_lab_employee_sms
from lims.api.utils.template_update import save_test_uom, update_template_uom
from lims.api.utils.utils import get_range_data
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
    if frappe.db.exists('ASTM Message Logs',{'order_number':orderResult['OrderNumber']}):
        # print('already logged')
        return frappe.db.get_value('ASTM Message Logs',{'order_number':orderResult['OrderNumber']},'name')
    else:
        if orderResult['OrderNumber'] and frappe.db.exists('Lab Test',{'name':orderResult['OrderNumber']}):
            message_log = frappe.new_doc('ASTM Message Logs')
            message_log.lab_station = 'SHOE 4 AFRICA'
            message_log.lab_machine = 'COBAS INTEGRA 400'
            message_log.order_number = orderResult['OrderNumber']
            message_log.astm = json.dumps({'orderResult':orderResult})
            message_log.save(ignore_permissions=True)
            message_log.reload()
            process_astm_result(message_log.get('name'))
            # return {'message':'Results Posted Succesfully','payload':{'orderResult':orderResult,'ResultCount':ResultCount,'OrderCount':OrderCount,'processed':message_log.get('result_data')}}
            return message_log.get('name')
        else:
            return {'message':'Results Missing Data'}

def process_astm_result(log_name):
    # print('process cobas result log {0}'.format(log_name))
    # logs = frappe.db.get_all('ASTM Message Logs',filters={},fields=['*'])
    # sql = "select name from `tabLab Test` ORDER BY RAND () LIMIT 1;"
    # test = frappe.db.sql(sql,as_dict=1)
    # astm_data = frappe.db.get_value('ASTM Message Logs',{'name':log_name},'astm')
    # lab_name = 'LQ' #create_random_test() #'HLC-LAB-2022-00024'
    # lab_name = create_random_test() #'HLC-LAB-2022-00024'
    lab_name = ''
    # test_sharing_sample_with = frappe.db.get_value('Lab Test',{'name':lab_name},'share_sample_with')
    astm_data = frappe.db.get_value('ASTM Message Logs',{'name':log_name},'astm')
    orderResult = json.loads(astm_data)
    if orderResult and 'orderResult' in orderResult:
        orderNumber = orderResult['orderResult']['OrderNumber']
        lab_name = orderNumber
        # OrderDate = orderResult['orderResult']['OrderDate'] if 'OrderDate' in orderResult else '00/00/0000'
        Orders = orderResult['orderResult']['Orders']
        Result = orderResult['orderResult']['Result']
        Uom = orderResult['orderResult']['Uom']
        Ranges = orderResult['orderResult']['Ranges']
        # output = "{0} processed {1} res {2}".format(orderNumber,log_name,Result)
        # print(output)
        results = append_order_to_test_and_results(Orders,Result,Uom,Ranges,log_name,lab_name)
        sorted_results = results
        # print("result {0} {1}".format(orderNumber,str(results)))
        # sorted_results = sorted(results, key=lambda d: d['template_name']) 
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
    else:
        log  = frappe.new_doc('Lims Error Log')
        log.ordernumber  = lab_name
        log.log_number = log_name
        log.unprocessed_result = 'error in process_astm_result'
        log.save(ignore_permissions=True)



def append_order_to_test_and_results(orderlist,resultList,Uom,Ranges,log_name,lab_name):
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
                    # 'range':Ranges[index],
                    'uom':Uom[index]})
            # print('order_names {0}'.format(order_names))
        return order_names
    else:
        log  = frappe.new_doc('Lims Error Log')
        log.ordernumber  = lab_name
        log.log_number = log_name
        log.unprocessed_result = str({'orderlist':orderlist,'resultList':resultList,'Uom':Uom,
        'Ranges':Ranges,'log_name':log_name,'lab_name':lab_name})
        log.save(ignore_permissions=True)
        return []#"Order/results mismatch"

def set_lab_test_result(log_name,test_name,result_list=[]):
    # print('result_list** {0}'.format(str(result_list)))
    if len(result_list)>0:
        custom_result = "<ol>"
        list_body='<li data-list="ordered"><span class="ql-ui" contenteditable="false"></span>'
        lab_test = frappe.get_doc('Lab Test',test_name)
        lab_test.normal_toggle = 1
        # normal_test_results =  frappe.db.get_all('Normal Test Result',filters={'parent':test_name},fields=['name','lab_test_name'])
        # for res in normal_test_results:
            # frappe.delete_doc('Normal Test Result',res['name'])
        idx = 0
        sorted_results = result_list #sorted(result_list, key=lambda d: d['template_name']) 
        for result in sorted_results:
            subString = "E+99"
            # print(str(result))
            # print('======{0} {1}'.format(str(result),type(result)))
            result_value = result['results'][0:4] if subString in result['results'] else float(result['results'])
            formatted_result ='{:.{}f}'.format(float(result_value),2)
            save_test_uom(uom_value=result['uom'],description=result['template_name'])
            update_template_uom(template_name=result['template_name'],uom_value=result['uom'])
            range_data = get_range_data(template_name=result['template_name'],gender=lab_test.get('patient_sex'),age=0)
            range_str = "{0} - {1}".format(range_data['lower_limit_value'],range_data['upper_limit_value'])
            if not frappe.db.exists('Normal Test Result',{'parent':test_name,'lab_test_name':result['template_name'],'lab_test_event':result['analysis']}):
                normal_test_items = lab_test.append('normal_test_items')
                normal_test_items.idx = idx
                normal_test_items.lab_test_name = result['template_name']
                normal_test_items.lab_test_event = result['analysis']
                normal_test_items.result_value = "{0}".format(formatted_result) #,result['uom'])
                normal_test_items.lab_test_uom =  result['uom'] #get_lab_uom(test_name)
                normal_test_items.normal_range =  range_str #result['range']
                normal_test_items.test_range =  range_str
                normal_test_items.lab_test_comment = 'NA'
                lab_test.save(ignore_permissions=True)
                custom_result += list_body + "{0}\t{1}\t{2} {3} {4}</li>".format(result['template_name'], result['analysis'],formatted_result,result['uom'],range_str)
                idx+=1
        # frappe.db.set_value('Lab Test',test_name,{'custom_result': custom_result})
        from frappe.model.workflow import apply_workflow
        if lab_test.get('workflow_state')=='Processing':
            apply_workflow(doc=lab_test, action="Forward For Verification")
        if lab_test.get('employee'):
            msg = 'Test #{0} processed at {1} Cobas Integra posted through LIMS, awaiting verification.Thank you'.format(lab_test.get('name'),lab_test.get('processing_lab'))
            notify_lab_employee_sms(lab_test.get('employee'),message=msg)
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
        # print("code {0} cnt {1}".format(code['Code'],count))
    # print('complete')

# bench execute lims.api.shoe4africa_lab.cobas_400.process_cobas_raw_astm_results
def process_cobas_raw_astm_results():
    print('process_cobas_raw_astm_results')
    field_list = ['lab_station','lab_machine','astm_data','name']
    raw_astm  = frappe.get_all('Raw ASTM', filters={'is_processed': 0,'has_error':0,'lab_machine':'COBAS400-S4A'}, fields= field_list,order_by='creation asc',start=0,page_length=100)
    print(len(raw_astm))
    for data in raw_astm:
        try:
            raw_name = data['name'] #'a06e6641-c214'
            raw_astm_doc  = frappe.get_doc('Raw ASTM', raw_name)
            astm_data = raw_astm_doc.get('astm_data')
            parsed_data = ''
            if astm_data.startswith('"') and astm_data.endswith('"'):
                # print('string here')
                parsed_data = raw_astm_doc.get('astm_data')[1:-1]
                # print(' lan parsed_data ',len(parsed_data))
            else:
                # print('raw json')
                parsed_data = raw_astm_doc.get('astm_data')
            if len(parsed_data)>100:
                result_data = json.loads(parsed_data)
                # print(data['lab_machine'])
                # if data['lab_machine']=='COBAS400-S4A':
                # print('cobas machine')
                log_name = save_cobas_results(orderResult = result_data['orderResult'],OrderCount=result_data['OrderCount'],ResultCount=result_data['ResultCount'])
                print('log name ',str(log_name))
                print('raw name-2 ',raw_name)
                frappe.db.set_value('Raw ASTM', raw_name,{'astm_log': str(log_name),'is_processed':1})
                frappe.db.commit()
            else:
                print('ERROR')
                log  = frappe.new_doc('Lims Error Log')
                log.ordernumber  = raw_name
                log.log_number = raw_name
                log.unprocessed_result = str(parsed_data)
                log.save(ignore_permissions=True)
                # frappe.db.set_value('Raw ASTM', raw_name,{'is_processed':1,'has_error':1})
                frappe.db.sql("update `tabRaw ASTM` set is_processed=1,has_error=1 where name='{0}' ".format(raw_name))
            print('end process_raw_astm')
        except:
            print('error processing cobas-400-s4a result data')
        finally:
            continue
    return 1
    
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

# bench execute lims.api.shoe4africa_lab.cobas_400.po_workflow

def po_workflow():
    from frappe.model.workflow import apply_workflow
    # PUR-ORD-2023-04-22 20:07:04.515830  PUR-ORD-2023-04-22 19:07:23.626488
    # Reinstate Document, Forward for Approval 
    # 626488 -ex order
    doc = frappe.get_doc('Externally Generated Purchase Order','toilet locks')  
    apply_workflow(doc=doc, action="Confirm")