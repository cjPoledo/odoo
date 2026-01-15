from odoo import models, fields


class ROR(models.Model):
    _name = "upmin_iso.ror"
    _description = "Risk and Opportunities Register"
    _rec_name = "office"
    _order = "create_date"

    office = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        required=True,
        domain=lambda self: (
            [("id", "=", self.env.user.employee_id.department_id.id)]
            if self.env.user.employee_id and self.env.user.employee_id.department_id
            else []
        ),
    )
    related_swot = fields.Many2one(
        comodel_name="upmin_iso.swot",
        string="Related SWOT",
        help="Select the SWOT analysis related to ROR.",
        domain=lambda self: (
            [("office", "=", self.env.user.employee_id.department_id.id)]
            if self.env.user.employee_id and self.env.user.employee_id.department_id
            else []
        ),
        required=True,
    )
    internal_issues = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        string="Internal Issues",
        related="related_swot.weaknesses",
        readonly=False,
        help="What could affect the attainment of goals?\nInternal issues are Weaknesses in your SWOT.",
    )
    external_issues = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        string="External Issues",
        related="related_swot.threats",
        readonly=False,
        help="What could affect the attainment of goals?\nExternal issues are Threats in your SWOT.",
    )

    _sql_constraints = [
        (
            "unique_swot",
            "unique(related_swot)",
            "ROR for this SWOT already exists.",
        )
    ]
