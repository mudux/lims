from ast import Pass
import frappe
import json
from frappe.utils.background_jobs import enqueue

from lims.api.shoe4africa_lab.cobas_400 import process_astm_result, save_cobas_results,process_cobas_raw_astm_results
from lims.api.shoe4africa_lab.sysmex import sysmex_append_to_lab_test,process_sysmex_astm

# bench execute lims.api.utils.process_raw_astm.process_raw_astm
def process_raw_astm():
    process_cobas_raw_astm_results()
    process_sysmex_astm()
    
def process_raw_astm_deprecated():
    # print('start process_raw_astm')
    field_list = ['lab_station','lab_machine','astm_data','name']
    raw_astm  = frappe.get_all('Raw ASTM', filters={'is_processed': 0,'has_error':0,'lab_machine':'SYSMEX-330-S4A'}, fields= field_list,order_by='creation asc',start=0,page_length=100)
    # print("data {0}".format(len(raw_astm)))
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
                if data['lab_machine']=='COBAS400-S4A':
                    # print('cobas machine')
                    log_name = save_cobas_results(orderResult = result_data['orderResult'],OrderCount=result_data['OrderCount'],ResultCount=result_data['ResultCount'])
                    print('log name ',str(log_name))
                    print('raw name-2 ',raw_name)
                    frappe.db.set_value('Raw ASTM', raw_name,{'astm_log': str(log_name),'is_processed':1})
                    frappe.db.commit()
                if data['lab_machine']=='SYSMEX-330-S4A':
                    print('s4a sysmex')
                    # raw_name = data['name'] #'a06e6641-c214'
                    # raw_astm_doc  = frappe.get_doc('Raw ASTM', raw_name)
                    astm_data = raw_astm_doc.get('astm_data')
                    # print(astm_data)
                    result_data = json.loads(astm_data[1:-1])
                    lab_name = result_data['OrderNumber']
                    patient = result_data['Patient']
                    orders = result_data['Orders']
                    results = result_data['Result']
                    uoms = result_data['Uom']
                    print(' patient ',patient,' lab_name ',lab_name)
                    sysmex_append_to_lab_test(lab_name,orders,results,uoms)
                    # frappe.db.set_value('Raw ASTM', raw_name,{'astm_log': str(log_name),'is_processed':1})
                    frappe.db.sql("update `tabRaw ASTM` set is_processed=1 where name='{0}' ".format(raw_name))
                    print('closing raw astm ',raw_name)
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
                pass
            print('end process_raw_astm')
        except:
            # log  = frappe.new_doc('Lims Error Log')
            # log.ordernumber  = raw_name
            # log.log_number = raw_name
            # log.unprocessed_result = str(x)
            # log.save(ignore_permissions=True)
            pass
        finally:
            continue

# bench execute lims.api.utils.process_raw_astm.process_raw_astm_single
def process_raw_astm_single(data=''):
    try:
        raw_name = data.get('name') #'7d9641ba-f78b' #
        raw_astm_doc  = frappe.get_doc('Raw ASTM', raw_name)
        astm_data = raw_astm_doc.get('astm_data')
        parsed_data = ''
        if astm_data.startswith('"') and astm_data.endswith('"'):
            parsed_data = raw_astm_doc.get('astm_data')[1:-1]
        else:
            parsed_data = raw_astm_doc.get('astm_data')
        if len(parsed_data)>100:
            result_data = json.loads(parsed_data)
            if raw_astm_doc.get('lab_machine')=='COBAS400-S4A':
                # print('cobas machine')
                log_name = save_cobas_results(orderResult = result_data['orderResult'],OrderCount=result_data['OrderCount'],ResultCount=result_data['ResultCount'])
                # print('log name ',str(log_name))
                # print('raw name-2 ',raw_name)
                frappe.db.set_value('Raw ASTM', raw_name,{'astm_log': str(log_name),'is_processed':1})
                frappe.db.commit()
        else:
            print('ERROR')
            log  = frappe.new_doc('Lims Error Log')
            log.ordernumber  = raw_name
            log.log_number = raw_name
            log.unprocessed_result = str(parsed_data)
            log.save(ignore_permissions=True)
            frappe.db.set_value('Raw ASTM', raw_name,{'is_processed':1,'has_error':1})
            pass
        print('end process_raw_astm')
        return 1
    except:
        # log  = frappe.new_doc('Lims Error Log')
        # log.ordernumber  = raw_name
        # log.log_number = raw_name
        # log.unprocessed_result = str(x)
        # log.save(ignore_permissions=True)
        pass
    
# bench execute lims.api.utils.process_raw_astm.astm_debug

def astm_debug():
    raw_name = 'ce016893-9e04'
    raw_astm_doc = frappe.get_doc('Raw ASTM',raw_name)
    astm_data = raw_astm_doc.get('astm_data')
    parsed_data = ''
    if astm_data.startswith('"') and astm_data.endswith('"'):
        print('string here')
        parsed_data = raw_astm_doc.get('astm_data')[1:-1]
    else:
        print('raw json')
        parsed_data = raw_astm_doc.get('astm_data')
    if len(parsed_data)>100:
        # print('NO ISSUE')
        result_data = json.loads(parsed_data)
        # print(result_data['orderResult'])
        if raw_astm_doc.get('lab_machine')=='COBAS400-S4A':
            print('cobas 400 s4a')
            log_name = save_cobas_results(orderResult = result_data['orderResult'],OrderCount=result_data['OrderCount'],ResultCount=result_data['ResultCount'])

            # print('finish save_cobas_results')
            frappe.db.set_value('Raw ASTM', raw_name,{'astm_log': log_name,'is_processed':1})
            print(log_name)
            
# SAL-ORD-2022-139992
# SAL-ORD-2022-140949
# SAL-ORD-2022-139993
# SAL-ORD-2022-132412
# SAL-ORD-2022-132411
# SAL-ORD-2022-143331
# SAL-ORD-2022-139983
# SAL-ORD-2022-141675