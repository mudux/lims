from dataclasses import fields
from unicodedata import name
import frappe

# bench execute lims.api.utils.utils.get_range_data
def get_range_data(template_name,gender,age=0):
    # range_dict = frappe.db.get_value('Lab Test Range', {'lab_test_template':template_name,'gender':gender,'age': ["between", [0, age]]}, ['lower_limit_value', 'upper_limit_value'], as_dict=1)
    #  and start_age>={2} and end_age<={3}
    sql = "select lower_limit_value,upper_limit_value from `tabLab Test Range` where lab_test_template='{0}' and gender='{1}' limit 1;".format(template_name,gender)
    range_dict = frappe.db.sql(sql,as_dict=1)
    # print(sql)
    # print(str(range_dict))
    if len(range_dict)>0:
        return {'lower_limit_value':range_dict[0]['lower_limit_value'],'upper_limit_value':range_dict[0]['upper_limit_value']}    
    return {'lower_limit_value':'-','upper_limit_value':'-'}

def check_if_inpatient(patient):
    # sales_order_doc = frappe.get_doc('Sales Order', sales_order)
    # print(sales_order_doc.patient_visit)
    ip_ads = frappe.db.exists('Inpatient Record',{'patient': patient, 'status':'Admission Scheduled'})
    ip_ad = frappe.db.exists('Inpatient Record',{'patient': patient,'status':'Discharge Scheduled'})
    ip_dis = frappe.db.exists('Inpatient Record',{'patient': patient,'status':'Admitted'})
    ip = ip_ad or ip_ads or ip_dis
    inpatient = ip
    return inpatient 

def lab_su():
    labs = frappe.get_all('Lab Test',fields=['name','patient'])
    for l in labs:
        ip = check_if_inpatient(l['patient'])
        # print(ip)
        if ip:
            sql = "select service_unit,check_in,check_out,creation from `tabInpatient Occupancy` where parent='{0}' order by check_out desc limit 1;".format(ip)
            bed_sql="select service_unit from `tabInpatient Occupancy` where parent='{0}' order by check_out desc limit 1;".format(ip)
            last_bed = frappe.db.sql(bed_sql,as_dict=1)
            if len(last_bed)>0:
                bed=last_bed[0]['service_unit']
                print(bed)
                su = frappe.db.get_value('Healthcare Service Unit',bed,'parent_healthcare_service_unit')
                # print(su)
                if su:
                    frappe.db.set_value('Lab Test',l['name'],{'healthcare_service_unit':su})
                    frappe.db.commit()

def lab_service_unit_check(lab_name):
    labs_doc = frappe.get_doc('Lab Test',lab_name)
    ip = check_if_inpatient(labs_doc['patient'])
    # print(ip)
    if ip:
        sql = "select service_unit,check_in,check_out,creation from `tabInpatient Occupancy` where parent='{0}' order by check_out desc limit 1;".format(ip)
        bed_sql="select service_unit from `tabInpatient Occupancy` where parent='{0}' order by check_out desc limit 1;".format(ip)
        last_bed = frappe.db.sql(bed_sql,as_dict=1)
        if len(last_bed)>0:
            bed=last_bed[0]['service_unit']
            print(bed)
            su = frappe.db.get_value('Healthcare Service Unit',bed,'parent_healthcare_service_unit')
            print(su)
            if su:
                frappe.db.set_value('Lab Test',labs_doc['name'],{'healthcare_service_unit':su})
                frappe.db.commit()

#  bench execute lims.api.utils.utils.get_range_data_test
def get_range_data_test():
    # name="3E4"
    # name='3FC'
    # lab_doc = frappe.get_doc("Lab Test",name)
    normal_res = frappe.get_all("Normal Test Result",filters={"parent":name},fields=['name','lab_test_name','parent'])
    for result in normal_res:
        # print(res['name'])
        lab_doc = frappe.get_doc("Lab Test",result['parent'])
        range_data = get_range_data(template_name=result['lab_test_name'],gender=lab_doc.get('patient_sex'),age=0)
        range_str = "{0} - {1}".format(range_data['lower_limit_value'],range_data['upper_limit_value'])
        # print(get_range_data(template_name=res['lab_test_name'],gender=lab_doc.get('patient_sex'),age=0))
        print(result['lab_test_name'], ' ' ,range_str)
        frappe.db.set_value("Normal Test Result",result['name'],{'test_range':range_str})
        frappe.db.set_value("Normal Test Result",result['name'],{'normal_range':range_str})
