import frappe

def tat_report():
    sql="select lt.name,lt.template,tta.workflow_state from `tabLab Test` lt inner join `tabTime to Action` tta where lt.docstatus=1 and tta.reference_name=lt.name and tta.reference_doctype='Lab Test'"