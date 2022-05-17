from ast import Pass
import frappe
import json

from lims.api.shoe4africa_lab.cobas_400 import process_astm_result, save_cobas_results

# bench execute lims.api.utils.process_raw_astm.process_raw_astm
def process_raw_astm():
    print('start process_raw_astm')
    field_list = ['lab_station','lab_machine','astm_data','name']
    raw_astm  = frappe.get_all('Raw ASTM', filters={'is_processed': 0,'has_error':0}, fields= field_list,order_by='creation asc',start=0,page_length=20,)
    print("data {0}".format(len(raw_astm)))
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
        except:
            # log  = frappe.new_doc('Lims Error Log')
            # log.ordernumber  = raw_name
            # log.log_number = raw_name
            # log.unprocessed_result = str(x)
            # log.save(ignore_permissions=True)
            pass

def process_raw_astm_single(data):
    try:
        raw_name = data['name'] #'a06e6641-c214'
        raw_astm_doc  = frappe.get_doc('Raw ASTM', raw_name)
        astm_data = raw_astm_doc.get('astm_data')
        parsed_data = ''
        if astm_data.startswith('"') and astm_data.endswith('"'):
            parsed_data = raw_astm_doc.get('astm_data')[1:-1]
        else:
            parsed_data = raw_astm_doc.get('astm_data')
        if len(parsed_data)>100:
            result_data = json.loads(parsed_data)
            if data['lab_machine']=='COBAS400-S4A':
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
            frappe.db.set_value('Raw ASTM', raw_name,{'is_processed':1,'has_error':1})
            pass
        print('end process_raw_astm')
    except:
        # log  = frappe.new_doc('Lims Error Log')
        # log.ordernumber  = raw_name
        # log.log_number = raw_name
        # log.unprocessed_result = str(x)
        # log.save(ignore_permissions=True)
        pass
def astm_debug():
    raw_name = '0584c8df-cf8f'
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