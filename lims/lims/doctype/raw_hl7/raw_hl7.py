# Copyright (c) 2022, erp@mtrh.go.ke and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from lims.api.utils.process_raw_hl7 import process_raw_hl7_single

class RawHL7(Document):
	@frappe.whitelist()
	def reprocess_hl7_data(self):
		process_raw_hl7_single(self)
