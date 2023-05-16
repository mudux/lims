
import frappe
from lims.api.emergency_lab.medonic import create_pmr
import json
from lims.api.utils.utils import sysmex_ranges


# http://172.16.0.115/api/method/lims.api.emergency_lab.medonic.http://172.16.0.115/api/method/lims.api.emergency_lab.sysmex330.process_medonic_hl7
@frappe.whitelist(allow_guest=True)
def process_sysmex_hl7(HL7Message):
    return HL7Message

# bench execute lims.api.emergency_lab.sysmex330.process_e_lab_sysmemx_astm
def process_e_lab_sysmemx_astm():
    print('processe_lab__sysmex_astm')
    field_list = ['lab_station','lab_machine','astm_data','name']
    machine_name = 'SYSMEX-E-LAB'
    raw_astm_docs  = frappe.get_all('Raw ASTM', filters={'is_processed': 0,'has_error':0,'lab_machine':machine_name}, fields= field_list,order_by='creation asc',start=0,page_length=1)
    # print(len(raw_astm))
    for data in raw_astm_docs:
        # print(data)
        try:
            raw_name = data.get('name')
            result_data = json.loads(data.get('astm_data')[1:-1])
            lab_name = result_data['OrderNumber']
            patient = result_data['Patient']
            orders = result_data['Orders']
            results = result_data['Result']
            uoms = result_data['Uom']
            print(' patient ',patient,' lab_name ',lab_name,' raw_name ',raw_name)
            create_result_table(patient,orders,results,uoms)
            frappe.db.sql("update `tabRaw ASTM` set is_processed=1,modified=now() where name='{0}' ".format(raw_name))
        except:
            print('error processing sysmex-330-s4a result data ')
            frappe.db.sql("update `tabRaw ASTM` set is_processed=1,has_error=1,modified=now() where name='{0}' ".format(raw_name))
        finally:
            continue
    return 1
        
def create_result_table(patient,orders,results,uoms):
    range_dict = sysmex_ranges()
    idx = 1
    td = ''
    tail=""" </tbody></table></div>"""
    head="""<div class="ql-editor read-mode"><table class="table table-bordered" WIDTH="100%"><tbody><tr><td data-row="insert-column-right"><strong>Test</strong></td><td data-row="insert-column-right"><strong>Result</strong></td><td data-row="insert-column-right"><strong>Range</strong></td></tr>"""
    for order in orders[1:]:
        td+='<tr>'
        td+= """<td width="50%">{0}</td>""".format(order)
        td+="""<td width="25%">{0} {1}</td>""".format(results[idx],uoms[idx])
        td+="""<td width="25%">{0}</td> </tr>""".format(range_dict[order])
        idx += 1
    result_table =  head + td + tail
    if frappe.db.exists("Patient",{'name':patient}):
        create_pmr(result_data=result_table,sample_number='',patient=patient)