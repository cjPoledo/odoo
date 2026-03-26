from datetime import date
from odoo import models, fields, api


class SWOT(models.Model):
    _name = "upmin_iso.swot"
    _description = "SWOT"
    _rec_name = "office"
    _order = "office,year"

    year = fields.Char(
        string="Year", required=True, default=lambda self: str(date.today().year)
    )
    office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        required=True,
        domain=lambda self: (
            [("id", "in", list(filter(None, [
                self.env.user.employee_id.department_id.id,
                self.env.user.employee_id.admin_department_id.id,
            ])))]
            if self.env.user.employee_id
            else []
        ),
    )
    strengths = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Strengths",
        context={"default_swot_type": "S"},
        domain=[("swot_type", "=", "S")],
    )
    weaknesses = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Weaknesses",
        context={"default_swot_type": "W"},
        domain=[("swot_type", "=", "W")],
    )
    opportunities = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Opportunities",
        context={"default_swot_type": "O"},
        domain=[("swot_type", "=", "O")],
    )
    threats = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Threats",
        context={"default_swot_type": "T"},
        domain=[("swot_type", "=", "T")],
    )

    strengths_count = fields.Integer(compute="_compute_counts", store=True)
    weaknesses_count = fields.Integer(compute="_compute_counts", store=True)
    opportunities_count = fields.Integer(compute="_compute_counts", store=True)
    threats_count = fields.Integer(compute="_compute_counts", store=True)

    @api.depends("strengths", "weaknesses", "opportunities", "threats")
    def _compute_counts(self):
        for rec in self:
            rec.strengths_count = len(rec.strengths)
            rec.weaknesses_count = len(rec.weaknesses)
            rec.opportunities_count = len(rec.opportunities)
            rec.threats_count = len(rec.threats)

    _sql_constraints = [
        (
            "unique_year_office",
            "unique(year, office)",
            "SWOT for this year and office already exists.",
        )
    ]

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.office.name} - {rec.year}"
            result.append((rec.id, name))
        return result
