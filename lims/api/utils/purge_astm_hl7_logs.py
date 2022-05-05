import frappe
from datetime import datetime,date,timedelta

# bench execute lims.api.utils.purge_astm_hl7_logs.purge_lims_logs
def purge_lims_logs():
    purge_astm_logs()
    purge_hl7_logs()
    clear_raw_astm_older_than()
    clear_raw_hl7_older_than()


def purge_astm_logs():
    today = datetime.now()    
    n_days_ago = today - timedelta(days=10)
    print('n_days_ago {0}'.format(n_days_ago))
    sql = "DELETE FROM `tabASTM Message Logs` where DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    # print(str(frappe.db.sql(sql)))
    # frappe.db.sql('DELETE FROM `tab` WHERE ')
     

def purge_hl7_logs():
    # today = datetime.now()    
    # n_days_ago = today - timedelta(days=10)
    # print('n_days_ago {0}'.format(n_days_ago))
    sql = "DELETE FROM `tabHL7 Message Logs` where DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    # print(str(frappe.db.sql(sql)))

def clear_raw_astm_older_than():
    today = datetime.now()    
    n_days_ago = today - timedelta(days=5)
    print('n_days_ago {0}'.format(n_days_ago))
    sql = "DELETE FROM `tabRaw ASTM` where is_processed=1 AND has_error=0 AND DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    # print(str(frappe.db.sql(sql)))

def clear_raw_hl7_older_than():
    today = datetime.now()    
    n_days_ago = today - timedelta(days=5)
    print('n_days_ago {0}'.format(n_days_ago))
    sql = "DELETE FROM `tabRaw HL7` where is_processed=1 AND has_error=0 AND DATEDIFF(CURDATE(), DATE(creation)) > 10;"
    # print(str(frappe.db.sql(sql)))