from odoo import models, fields, api


class TOWSLine(models.Model):
    _name = "upmin_iso.tows_line"
    _description = "TOWS Line"
    _rec_name = "description"
    _order = "tows_id"

    tows_id = fields.Many2one("upmin_iso.tows", string="TOWS", required=True, ondelete="cascade")
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

    related_swot_line_ids = fields.Many2many(
        comodel_name="upmin_iso.swot_line",
        string="Related SWOT Lines",
        domain="[('id', 'in', allowed_swot_line_ids)]",
    )

    allowed_swot_line_ids = fields.Many2many(
        comodel_name="upmin_iso.swot_line",
        compute="_compute_allowed_swot_lines",
        string="Allowed SWOT Lines",
        readonly=True,
    )

    @api.depends("tows_id", "tows_type")
    def _compute_allowed_swot_lines(self):
        for rec in self:
            if not rec.tows_id or not rec.tows_type:
                rec.allowed_swot_line_ids = [(5, 0, 0)]
                continue

            swot = rec.tows_id.swot
            # Map TOWS pairs to SWOT fields
            tow_map = {
                "SO": ["strengths", "opportunities"],
                "WO": ["weaknesses", "opportunities"],
                "ST": ["strengths", "threats"],
                "WT": ["weaknesses", "threats"],
            }

            fields_needed = tow_map.get(rec.tows_type, [])

            # Concatenate all relevant line sets
            lines = self.env["upmin_iso.swot_line"]

            for field_name in fields_needed:
                lines |= getattr(swot, field_name)

            rec.allowed_swot_line_ids = lines
