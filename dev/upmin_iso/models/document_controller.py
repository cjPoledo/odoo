from odoo import models, fields, api


class DocumentController(models.Model):
    _name = "upmin_iso.document_controller"
    _description = "Document Controller"
    _rec_name = "name"
    _order = "office,name,trained"

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
    secondary_office = fields.Many2one(
        comodel_name="hr.department",
        string="Secondary Office",
        readonly=True,
        compute="_compute_secondary_office",
        store=False,
    )

    @api.depends("name")
    def _compute_office(self):
        for rec in self:
            emp = rec.name
            rec.office = getattr(emp, "admin_department_id", emp.department_id) or emp.department_id

    @api.depends("name", "is_unit_head")
    def _compute_secondary_office(self):
        for rec in self:
            emp = rec.name
            admin = getattr(emp, "admin_department_id", False)
            if rec.is_unit_head and admin and admin != emp.department_id:
                rec.secondary_office = emp.department_id
            else:
                rec.secondary_office = False

    trained = fields.Boolean(string="Trained", default=False)
    is_unit_head = fields.Boolean(string="Unit Head", default=False)
    allow_college_access = fields.Boolean(
        string="Allow College Access",
        default=True,
        help="When disabled, this DC's ISO access is restricted to their department and admin office only — no college-level documents.",
    )
    have_doc_control_perms = fields.Boolean(
        string="Have Document Control Permissions?",
        readonly=True,
        compute="_compute_have_doc_control_perms",
    )
    perms_label = fields.Selection(
        selection=[("active", "Access Active"), ("inactive", "No Access")],
        string="System Access",
        readonly=True,
        compute="_compute_have_doc_control_perms",
    )

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Document Controller already exists.",
        ),
    ]

    def _compute_have_doc_control_perms(self):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
        for rec in self:
            user = rec.name.user_id
            has = bool(user and group in user.groups_id)
            rec.have_doc_control_perms = has
            rec.perms_label = "active" if has else "inactive"

    def _grant_group(self, user):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
        if user:
            user.sudo().write({"groups_id": [(4, group.id)]})

    def _revoke_group(self, user):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
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

        if "allow_college_access" in vals:
            self.env.registry.clear_caches()

        return result

    def unlink(self):
        users = [rec.name.user_id for rec in self]
        result = super().unlink()
        for user in users:
            self._revoke_group(user)
        return result