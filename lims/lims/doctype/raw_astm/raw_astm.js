// Copyright (c) 2022, erp@mtrh.go.ke and contributors
// For license information, please see license.txt

frappe.ui.form.on('Raw ASTM', {
	refresh: function(frm) {
		frm.add_custom_button('Reprocess', () => {
            frm.call('reprocess_astm_data')
			.then(r => {
				// if (r.message) {}
				frm.reload_doc();
				frm.reload_doc();
				frappe.show_alert({
					message:'Success',
					indicator:'green'
				}, 5);
			})
        });
	}
});
