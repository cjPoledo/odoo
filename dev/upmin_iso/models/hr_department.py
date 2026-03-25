from odoo import models


class HrDepartment(models.Model):
    _inherit = "hr.department"
    _rec_name = "name"


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def write(self, vals):
        result = super().write(vals)
        if "user_id" in vals and vals["user_id"]:
            for emp in self:
                dc = self.env["upmin_iso.document_controller"].search(
                    [("name", "=", emp.id)], limit=1
                )
                if dc:
                    dc._grant_group(emp.user_id)
        return result
