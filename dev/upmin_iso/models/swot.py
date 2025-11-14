from odoo import models, fields


class SWOT(models.Model):
    _name = "upmin_iso.swot"
    _description = "SWOT"
    _rec_name = "office"
    _order = "office,year"

    year = fields.Integer(string="Year", required=True)
    office = fields.Many2one(
        comodel_name="hr.department", string="Office", required=True
    )
    strengths = fields.One2many(
        comodel_name="upmin_iso.swot_line", inverse_name="swot_id", string="Strengths"
    )
    weaknesses = fields.One2many(
        comodel_name="upmin_iso.swot_line", inverse_name="swot_id", string="Weaknesses"
    )
    opportunities = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Opportunities",
    )
    threats = fields.One2many(
        comodel_name="upmin_iso.swot_line", inverse_name="swot_id", string="Threats"
    )
    so = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Strengths-Opportunities",
    )
    wo = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Weaknesses-Opportunities",
    )
    st = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Strengths-Threats",
    )
    wt = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="swot_id",
        string="Weaknesses-Threats",
    )
