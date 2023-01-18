import frappe
from frappe.desk.form.document_follow import follow_document
# from frappe.utils.file_manager import extract_images_from_html
from frappe.core.doctype.file.utils import extract_images_from_html

def add_comment(reference_name, reference_doctype,content):
    """allow any logged user to post a comment"""
    doc = frappe.get_doc(dict(
        doctype='Comment',
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        comment_email='erp@mtrh.go.ke',
        comment_type='Comment',
        comment_by='Administrator'
    ))
    doc.content = extract_images_from_html(doc, content)
    doc.insert(ignore_permissions=True)
    follow_document(doc.reference_doctype, doc.reference_name, 'Administrator')
    return doc.as_dict()