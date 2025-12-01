from odoo import models, fields


class TOWSLine(models.Model):
    _name = "upmin_iso.tows_line"
    _description = "TOWS Line"
    _rec_name = "description"
    _order = "swot_id"

    swot_id = fields.Many2one("upmin_iso.swot", string="SWOT", required=True)
    description = fields.Text(string="Description", required=True)
    tows_type = fields.Selection(
        string="Type",
        selection=[
            ("SO", "Strengths-Opportunities"),
            ("WO", "Weaknesses-Opportunities"),
            ("ST", "Strengths-Threats"),
            ("WT", "Weaknesses-Threats"),
        ],
        required=True,
    )

    strength_ids = fields.Many2many("upmin_iso.swot_line")
    weakness_ids = fields.Many2many("upmin_iso.swot_line")
    opportunity_ids = fields.Many2many("upmin_iso.swot_line")
    threat_ids = fields.Many2many("upmin_iso.swot_line")
