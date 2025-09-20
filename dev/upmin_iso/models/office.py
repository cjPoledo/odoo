from odoo import models, fields


class Office(models.Model):
    _name = "upmin_iso.office"
    _description = "Office"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Office Name", required=True)
    cluster = fields.Many2one(
        comodel_name="upmin_iso.office",
        string="Cluster",
        domain="[('cluster_head', '=', True)]",
    )
    cluster_head = fields.Boolean(string="Cluster Head?", default=False)
    doc_controllers = fields.Many2many(
        comodel_name="res.partner", string="Document Controllers"
    )
