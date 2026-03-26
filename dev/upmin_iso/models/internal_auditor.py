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
        compute="_compute_office",
        store=True,
    )

    @api.depends("name")
    def _compute_office(self):
        for rec in self:
            emp = rec.name
            rec.office = getattr(emp, "admin_department_id", emp.department_id) or emp.department_id
    trained = fields.Boolean(string="Trained", default=False)
    certified = fields.Boolean(string="Certified", default=False)
    have_internal_auditor_perms = fields.Boolean(
        string="Have Internal Auditor Permissions?",
        readonly=True,
        compute="_compute_have_internal_auditor_perms",
    )
    perms_label = fields.Selection(
        selection=[("active", "Access Active"), ("inactive", "No Access")],
        string="System Access",
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
            has = bool(user and group in user.groups_id)
            rec.have_internal_auditor_perms = has
            rec.perms_label = "active" if has else "inactive"

    def _grant_group(self, user):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")
        if user:
            user.sudo().write({"groups_id": [(4, group.id)]})

    def _revoke_group(self, user):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")
        if user and group in user.groups_id:
            user.sudo().write({"groups_id": [(3, group.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            self._grant_group(rec.name.user_id)
        return records

    def write(self, vals):
        if "name" in vals:
            old_users = {rec.id: rec.name.user_id for rec in self}

        result = super().write(vals)

        if "name" in vals:
            for rec in self:
                self._revoke_group(old_users[rec.id])
                self._grant_group(rec.name.user_id)

        return result

    def unlink(self):
        users = [rec.name.user_id for rec in self]
        result = super().unlink()
        for user in users:
            self._revoke_group(user)
        return result