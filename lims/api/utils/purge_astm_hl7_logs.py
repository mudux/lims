import frappe
from datetime import datetime,date,timedelta

def purge_lim_logs():
    purge_astm_logs()
    purge_hl7_logs()

def purge_astm_logs():
    today = datetime.now()    
    n_days_ago = today - timedelta(days=10)
    print('n_days_ago {0}'.format(n_days_ago))
    sql = "select name,creation from `tabASTM Message Logs` where creation > '{0}' limit 4".format(n_days_ago)
    print(str(frappe.db.sql(sql)))
    # frappe.db.sql('DELETE FROM `tab` WHERE ')
     

def purge_hl7_logs():
    today = datetime.now()    
    n_days_ago = today - timedelta(days=10)
    print('n_days_ago {0}'.format(n_days_ago))
    sql = "select name,creation from `tabHL7 Message Logs` where creation > '{0}' limit 4".format(n_days_ago)
    print(str(frappe.db.sql(sql)))
