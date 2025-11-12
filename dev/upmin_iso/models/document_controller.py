from odoo import models, fields


class DocumentController(models.Model):
    _name = "upmin_iso.document_controller"
    _description = "Document Controller"
    _rec_name = "name"
    _order = "office,name,trained"

    name = fields.Many2one(
        comodel_name="hr.employee", string="Document Controller Name", required=True
    )
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

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Document Controller already exists.",
        ),
    ]
