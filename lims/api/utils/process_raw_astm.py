from ast import Pass
import frappe
import json

from lims.api.shoe4africa_lab.cobas_400 import process_astm_result, save_cobas_results

# bench execute lims.api.utils.process_raw_astm.process_raw_astm
def process_raw_astm():
    print('start process_raw_astm')
    field_list = ['lab_station','lab_machine','astm_data','name']
    raw_astm  = frappe.get_all('Raw ASTM', filters={'is_processed': 0,'has_error':0}, fields= field_list,order_by='creation asc',start=0,page_length=5,)
    print("data {0}".format(len(raw_astm)))
    for data in raw_astm:
        try:
            raw_name = data['name'] #'a06e6641-c214'
            print(raw_name)
            raw_astm_doc  = frappe.get_doc('Raw ASTM', raw_name)
            astm_data = raw_astm_doc.get('astm_data')
            parsed_data = ''
            if astm_data.startswith('"') and astm_data.endswith('"'):
                print('string here')
                parsed_data = raw_astm_doc.get('astm_data')[1:-1]
            else:
                print('raw json')
                parsed_data = raw_astm_doc.get('astm_data')
            # parsed_data = raw_astm_doc.get('astm_data')[1:-1]
            print(len(parsed_data))
            # print("EROROR" if len(x)<100 else "CLEAR")
            if len(parsed_data)>100:
                print('NO ISSUE')
                result_data = json.loads(parsed_data)
                # print(result_data['orderResult'])
                if data['lab_machine']=='COBAS400-S4A':
                    log_name = save_cobas_results(orderResult = result_data['orderResult'],OrderCount=result_data['OrderCount'],ResultCount=result_data['ResultCount'])
                    print('finish save_cobas_results')
                    frappe.db.set_value('Raw ASTM', raw_name,{'astm_log': raw_name,'is_processed':1})
                    print(log_name)
            else:
                print('ERROR')
                log  = frappe.new_doc('Lims Error Log')
                log.ordernumber  = raw_name
                log.log_number = raw_name
                log.unprocessed_result = str(parsed_data)
                log.save(ignore_permissions=True)
                frappe.db.set_value('Raw ASTM', raw_name,{'is_processed':1,'has_error':1})
            print('end process_raw_astm')
        except:
            # log  = frappe.new_doc('Lims Error Log')
            # log.ordernumber  = raw_name
            # log.log_number = raw_name
            # log.unprocessed_result = str(x)
            # log.save(ignore_permissions=True)
            pass
