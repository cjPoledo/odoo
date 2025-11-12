from odoo import models, fields, api


class InternalAuditor(models.Model):
    _name = "upmin_iso.internal_auditor"
    _description = "Internal Auditor"
    _rec_name = "name"
    _order = "office,name,certified,trained"

    name = fields.Many2one(comodel_name="hr.employee", string="Name", required=True)
    email = fields.Char(
        string="Email", related="name.work_email", readonly=True, store=True
    )
    office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        readonly=True,
        related="name.department_id",
        store=True,
    )
    trained = fields.Boolean(string="Trained", default=False)
    certified = fields.Boolean(string="Certified", default=False)
    have_internal_auditor_perms = fields.Boolean(
        string="Have Internal Auditor Permissions?",
        readonly=True,
        compute="_compute_have_internal_auditor_perms",
    )

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Auditor already exists.",
        ),
    ]

    def _compute_have_internal_auditor_perms(self):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")

        for rec in self:
            user = rec.name.user_id
            rec.have_internal_auditor_perms = user and group in user.groups_id

    def _assign_internal_auditor_group(self):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")

        for rec in self:
            user = rec.name.user_id
            if user:
                user.sudo().write({"groups_id": [(4, group.id)]})

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._assign_internal_auditor_group()
        return record

    def write(self, vals):
        record = super().write(vals)
        self._assign_internal_auditor_group()
        return record

    def unlink(self):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")

        for rec in self:
            user = rec.name.user_id
            if user and group in user.groups_id:
                user.sudo().write({"groups_id": [(3, group.id)]})

        return super().unlink()
