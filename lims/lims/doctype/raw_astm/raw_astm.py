# Copyright (c) 2022, erp@mtrh.go.ke and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from lims.api.utils.process_raw_astm import process_raw_astm_single
class RawASTM(Document):
	@frappe.whitelist()
	def reprocess_astm_data(self):
		process_raw_astm_single(self)
		return 'Success'
		
