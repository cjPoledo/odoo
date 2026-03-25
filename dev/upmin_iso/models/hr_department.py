from odoo import models


class HrDepartment(models.Model):
    _inherit = "hr.department"

    def name_get(self):
        if self.env.context.get("upmin_iso_dept_short"):
            return [(dept.id, dept.name) for dept in self]
        return super().name_get()


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
                ia = self.env["upmin_iso.internal_auditor"].search(
                    [("name", "=", emp.id)], limit=1
                )
                if ia:
                    ia._grant_group(emp.user_id)
        return result
