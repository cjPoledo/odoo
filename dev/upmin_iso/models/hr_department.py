from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = "hr.department"

    def name_get(self):
        if self.env.context.get("upmin_iso_dept_short"):
            return [(dept.id, dept.name) for dept in self]
        return super().name_get()


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    iso_ancestor_ids = fields.Many2many(
        comodel_name="hr.department",
        string="ISO Access Groups",
        compute="_compute_iso_ancestor_ids",
        help="Configured access group departments found in this employee's department chain.",
    )

    @api.depends(
        "department_id",
        "department_id.parent_id",
        "department_id.parent_id.parent_id",
        "department_id.parent_id.parent_id.parent_id",
    )
    def _compute_iso_ancestor_ids(self):
        group_ids = set(
            self.env["upmin_iso.iso_access_group"].sudo().search([]).mapped("department_id").ids
        )
        blocked_emp_ids = set(
            self.env["upmin_iso.document_controller"].sudo()
                .search([("allow_college_access", "=", False)])
                .mapped("name").ids
        )
        for rec in self:
            if rec.id in blocked_emp_ids:
                rec.iso_ancestor_ids = self.env["hr.department"]
                continue
            ancestors = []
            dept = rec.department_id
            while dept:
                if dept.id in group_ids:
                    ancestors.append(dept.id)
                dept = dept.parent_id
            rec.iso_ancestor_ids = self.env["hr.department"].browse(ancestors)

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
