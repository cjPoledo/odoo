from datetime import date
from odoo import models, fields


class TOWS(models.Model):
    _name = "upmin_iso.tows"
    _description = "TOWS"
    _rec_name = "swot"
    _order = "swot"

    swot = fields.Many2one(comodel_name="upmin_iso.swot", string="SWOT", required=True, ondelete="cascade")
    year = fields.Char(string="Year", related="swot.year", readonly=True, store=True)
    office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        related="swot.office",
        readonly=True,
        store=True,
    )
    so = fields.One2many(
        comodel_name="upmin_iso.tows_line",
        inverse_name="tows_id",
        string="Strengths-Opportunities",
        domain=[("tows_type", "=", "SO")],
        context={"default_tows_type": "SO"},
    )
    wo = fields.One2many(
        comodel_name="upmin_iso.tows_line",
        inverse_name="tows_id",
        string="Weaknesses-Opportunities",
        domain=[("tows_type", "=", "WO")],
        context={"default_tows_type": "WO"},
    )
    st = fields.One2many(
        comodel_name="upmin_iso.tows_line",
        inverse_name="tows_id",
        string="Strengths-Threats",
        domain=[("tows_type", "=", "ST")],
        context={"default_tows_type": "ST"},
    )
    wt = fields.One2many(
        comodel_name="upmin_iso.tows_line",
        inverse_name="tows_id",
        string="Weaknesses-Threats",
        domain=[("tows_type", "=", "WT")],
        context={"default_tows_type": "WT"},
    )

    _sql_constraints = [
        (
            "unique_swot",
            "unique(swot)",
            "TOWS for this SWOT analysis already exists.",
        )
    ]
