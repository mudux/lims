import frappe
from datetime import datetime,date,timedelta

# bench execute lims.api.utils.purge_astm_hl7_logs.purge_lims_logs
def purge_lims_logs():
    purge_astm_logs()
    purge_hl7_logs()
    clear_raw_astm_older_than()
    clear_raw_hl7_older_than()


def purge_astm_logs():
    sql = "SELECT name FROM `tabASTM Message Logs` where DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    log_data = frappe.db.sql(sql,as_dict=1)
    for d in log_data:
        frappe.delete_doc('ASTM Message Logs',d['name'])
     
def purge_hl7_logs():
    sql = "SELECT name FROM `tabHL7 Message Logs` where DATEDIFF(CURDATE(), DATE(creation)) > 10;"
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