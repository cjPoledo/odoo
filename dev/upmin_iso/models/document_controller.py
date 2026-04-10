from odoo import models, fields, api


class DocumentController(models.Model):
    _name = "upmin_iso.document_controller"
    _description = "Document Controller"
    _rec_name = "name"
    _order = "name,trained"

    name = fields.Many2one(comodel_name="hr.employee", string="Name", required=True)
    email = fields.Char(
        string="Email", related="name.work_email", readonly=True, store=True
    )
    office = fields.Many2many(
        comodel_name="hr.department",
        string="Office",
        readonly=True,
        compute="_compute_office",
        store=True,
        relation="upmin_iso_dc_office_rel",
        column1="dc_id",
        column2="dept_id",
    )

    @api.depends("name", "name.department_id", "name.admin_department_id")
    def _compute_office(self):
        for rec in self:
            emp = rec.name
            if not emp:
                rec.office = self.env["hr.department"]
                continue
            office_ids = set()
            if emp.department_id:
                office_ids.add(emp.department_id.id)
            admin = getattr(emp, "admin_department_id", False)
            if admin:
                office_ids.add(admin.id)
            rec.office = self.env["hr.department"].browse(list(office_ids))

    trained = fields.Boolean(string="Trained", default=False)
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
        if not user or group not in user.groups_id:
            return
        # Keep perms if the employee still has an active Unit Head record
        emp = user.employee_id
        if emp and self.env["upmin_iso.unit_head"].sudo().search_count([("name", "=", emp.id)]):
            return
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
