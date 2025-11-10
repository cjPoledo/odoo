from odoo import models, fields


class InternalAuditor(models.Model):
    _name = "upmin_iso.internal_auditor"
    _description = "Internal Auditor"
    _rec_name = "name"
    _order = "office,name,certified,trained"

    name = fields.Many2one(
        comodel_name="hr.employee", string="Auditor Name", required=True
    )
    office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        readonly=True,
        related="name.department_id",
    )
    trained = fields.Boolean(string="Trained", default=False)
    certified = fields.Boolean(string="Certified", default=False)
