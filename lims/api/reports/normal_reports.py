import frappe

def normal_report_count():
    sql = "select ntr.parent,ntr.lab_test_name,ntr.lab_test_event,lt.processing_lab,lt.lab_test_name,lt.template from `tabNormal Test Result` ntr inner join `tabLab Test` lt on ntr.parent=lt.name where MONTH(ntr.creation)=MONTH(now())"
    sql1 = "select ntr.parent,ntr.lab_test_name,count(ntr.lab_test_name) as count_number,lt.processing_lab from `tabNormal Test Result` ntr inner join `tabLab Test` lt on ntr.parent=lt.name where MONTH(ntr.creation)=MONTH(now()) group by lt.lab_test_name"
    data = frappe.db.sql(sql1,as_dict=1)