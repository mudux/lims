import frappe
from erpnext.healthcare.doctype.lab_test_template.lab_test_template import make_item_price

def update_template_to_descriptive():
    templates = frappe.db.get_all('Lab Test Template',filters={},fields=['name'])
    for template_name in templates:
        print(template_name['name'])
        template = frappe.get_doc('Lab Test Template',template_name['name'])
        descriptive_test_templates = template.append('descriptive_test_templates')
        descriptive_test_templates.particulars = template_name['name']
        descriptive_test_templates.allow_blank = 0
        # Descriptive Test Template
        template.save(ignore_permissions=True)

def create_template_from_loinc(loinc_code):
    description  = frappe.db.get_value('Loinc Code',{'name':loinc_code},'description')
    if description and not frappe.db.exists('Item', description):
        test_template = frappe.new_doc('Lab Test Template')
        test_template.lab_test_name = description
        test_template.item = description 
        test_template.lab_test_code = description
        test_template.lab_test_group = 'Services'
        test_template.department = 'Eye clinic'
        test_template.lab_test_rate = 250
        test_template.is_billable = 1
        test_template.disabled = 0
        test_template.lab_test_template_type = 'Single'
        create_item_from_template(test_template)
        test_template.save(ignore_permissions=True)
        test_code = frappe.new_doc('Lab Test Codes')
        test_code.lab_test_template = description
        test_code.loinc_code = loinc_code
        test_code.save(ignore_permissions=True)


def create_item_from_template(doc):
	uom = frappe.db.exists('UOM', 'Unit') or frappe.db.get_single_value('Stock Settings', 'stock_uom')
	# Insert item
	item =  frappe.get_doc({
		'doctype': 'Item',
		'item_code': doc.lab_test_code,
		'item_name':doc.lab_test_name,
		'item_group': doc.lab_test_group,
		'description':doc.lab_test_description,
		'is_sales_item': 1,
		'is_service_item': 1,
		'is_purchase_item': 0,
		'is_stock_item': 0,
		'include_item_in_manufacturing': 0,
		'show_in_website': 0,
		'is_pro_applicable': 0,
		'disabled': 0 if doc.is_billable and not doc.disabled else doc.disabled,
		'stock_uom': uom
	}).insert(ignore_permissions=True, ignore_mandatory=True)

	# Insert item price
	if doc.is_billable and doc.lab_test_rate != 0.0:
		price_list_name = frappe.db.get_value('Price List', {'selling': 1})
		if doc.lab_test_rate:
			make_item_price(item.name, price_list_name, doc.lab_test_rate)
		else:
			make_item_price(item.name, price_list_name, 0.0)
	# Set item in the template
	frappe.db.set_value('Lab Test Template', doc.name, 'item', item.name)

	doc.reload()

def save_test_uom(uom_value,description):
    args = {
        "doctype": "Lab Test UOM",
        'lab_test_uom':uom_value,
        'uom_description':description
    }
    uom = frappe.db.exists('Lab Test UOM', uom_value)
    if not uom:
        doc = frappe.get_doc(args).insert(ignore_permissions=True, ignore_mandatory=True)
        print("Inserted UOM {0} ".format(uom_value))

def update_template_uom(template_name,uom_value):
    lab_test_uom  = frappe.db.get_value('Lab Test Template',{'name':template_name},'lab_test_uom')
    if not lab_test_uom:
        frappe.db.set_value('Lab Test Template',template_name,{'lab_test_uom': uom_value})
        print("Updated Lab Test Template {0} UOM {1}".format(template_name,uom_value))

        

