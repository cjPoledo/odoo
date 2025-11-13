from odoo import models, fields


class SWOTLine(models.Model):
    _name = "upmin_iso.swot_line"
    _description = "SWOT Line"
    _rec_name = "description"
    _order = "swot_id"

    swot_id = fields.Many2one(
        comodel_name="upmin_iso.swot", string="SWOT", required=True
    )
    description = fields.Text(string="Description", required=True)
