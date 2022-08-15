import frappe

def normal_report_count():
    sql = "select ntr.parent,ntr.lab_test_name,ntr.lab_test_event,lt.processing_lab,lt.lab_test_name,lt.template from `tabNormal Test Result` ntr inner join `tabLab Test` lt on ntr.parent=lt.name where MONTH(ntr.creation)=MONTH(now())"
    sql1 = "select ntr.parent,ntr.lab_test_name,count(ntr.lab_test_name) as count_number,lt.processing_lab from `tabNormal Test Result` ntr inner join `tabLab Test` lt on ntr.parent=lt.name where MONTH(ntr.creation)=MONTH(now()) group by lt.lab_test_name"
    x = """
        select 
            ntr.lab_test_name, 
            ntr.docstatus, 
            count(ntr.lab_test_name) as count_number, 
            lt.processing_lab 
            from 
            `tabNormal Test Result` ntr 
            inner join `tabLab Test` lt on lt.name = ntr.parent 
            where 
            lt.docstatus < 2 
            AND MONTH(ntr.creation)= MONTH(now()) 
            AND ntr.result_value is not null 
            group by 
            ntr.lab_test_name
            order by 
            ntr.lab_test_name ASC 
    """
    data = frappe.db.sql(sql1,as_dict=1)