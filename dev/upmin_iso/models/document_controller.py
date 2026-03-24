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
        related="name.department_id",
        store=True,
    )
    trained = fields.Boolean(string="Trained", default=False)
    is_unit_head = fields.Boolean(string="Unit Head", default=False)
    have_doc_control_perms = fields.Boolean(
        string="Have Document Control Permissions?",
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
            rec.have_doc_control_perms = user and group in user.groups_id

    def _assign_doc_controller_group(self):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")

        for rec in self:
            user = rec.name.user_id
            if user:
                user.sudo().write({"groups_id": [(4, group.id)]})

    @api.model_create_multi
    def create(self, vals):
        record = super().create(vals)
        record._assign_doc_controller_group()
        return record

    def write(self, vals):
        record = super().write(vals)
        self._assign_doc_controller_group()
        return record

    def unlink(self):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")

        for rec in self:
            user = rec.name.user_id
            if user and group in user.groups_id:
                user.sudo().write({"groups_id": [(3, group.id)]})

        return super().unlink()