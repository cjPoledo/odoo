from odoo import models, fields, api


class HrDepartment(models.Model):
    _inherit = "hr.department"

    def name_get(self):
        if self.env.context.get("upmin_iso_dept_short"):
            return [(dept.id, dept.name) for dept in self]
        return super().name_get()


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    iso_office_ids = fields.Many2many(
        comodel_name="hr.department",
        string="ISO Offices",
        compute="_compute_iso_office_ids",
        help="All offices from this employee's DC, UH, and IA directory records.",
    )

    @api.depends("department_id", "admin_department_id")
    def _compute_iso_office_ids(self):
        for rec in self:
            dc = self.env["upmin_iso.document_controller"].sudo().search(
                [("name", "=", rec.id)], limit=1
            )
            uh = self.env["upmin_iso.unit_head"].sudo().search(
                [("name", "=", rec.id)], limit=1
            )
            rec.iso_office_ids = dc.office | uh.office

    iso_ancestor_ids = fields.Many2many(
        comodel_name="hr.department",
        string="ISO Access Groups",
        compute="_compute_iso_ancestor_ids",
        help="College-level access group departments derived from this employee's directory offices.",
    )

    @api.depends("department_id", "admin_department_id")
    def _compute_iso_ancestor_ids(self):
        group_ids = set(
            self.env["upmin_iso.iso_access_group"].sudo().search([]).mapped("department_id").ids
        )
        for rec in self:
            ancestors = []
            seen = set()
            for dept in rec.iso_office_ids:
                d = dept
                while d:
                    if d.id in group_ids and d.id not in seen:
                        ancestors.append(d.id)
                        seen.add(d.id)
                    d = d.parent_id
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
                uh = self.env["upmin_iso.unit_head"].search(
                    [("name", "=", emp.id)], limit=1
                )
                if uh:
                    uh._grant_group(emp.user_id)
                ia = self.env["upmin_iso.internal_auditor"].search(
                    [("name", "=", emp.id)], limit=1
                )
                if ia:
                    ia._grant_group(emp.user_id)
        return result
