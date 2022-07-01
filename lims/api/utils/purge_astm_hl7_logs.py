import frappe
from datetime import datetime,date,timedelta
from frappe.utils.background_jobs import enqueue

# bench execute lims.api.utils.purge_astm_hl7_logs.purge_lims_logs
def purge_lims_logs():
    enqueue(method=purge_astm_logs, queue='long', timeout=3600)
    enqueue(method=purge_hl7_logs, queue='long', timeout=3600)
    enqueue(method=clear_raw_astm_older_than, queue='long', timeout=3600)
    enqueue(method=clear_raw_hl7_older_than, queue='long', timeout=3600)

# bench execute lims.api.utils.purge_astm_hl7_logs.purge_astm_logs
def purge_astm_logs():
    sql = "SELECT name FROM `tabASTM Message Logs` where DATEDIFF(CURDATE(), DATE(creation)) > 15;"
    log_data = frappe.db.sql(sql,as_dict=1)
    for d in log_data:
        print(d['name'])
        frappe.delete_doc('ASTM Message Logs',d['name'])
     
def purge_hl7_logs():
    sql = "SELECT name FROM `tabHL7 Message Logs` where DATEDIFF(CURDATE(), DATE(creation)) > 15;"
    log_data = frappe.db.sql(sql,as_dict=1)
    for d in log_data:
        frappe.delete_doc('HL7 Message Logs',d['name'])

def clear_raw_astm_older_than():
    sql = "SELECT name FROM `tabRaw ASTM` where is_processed=1 AND has_error=0 AND DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    log_data = frappe.db.sql(sql,as_dict=1)
    for d in log_data:
        frappe.delete_doc('Raw ASTM',d['name'])

def clear_raw_hl7_older_than():
    sql = "SELECT name FROM `tabRaw HL7` where is_processed=1 AND has_error=0 AND DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    log_data = frappe.db.sql(sql,as_dict=1)
    for d in log_data:
        frappe.delete_doc('Raw HL7',d['name'])