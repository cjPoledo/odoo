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

    bypass_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="upmin_iso_tows_bypass_user_rel",
        column1="tows_id",
        column2="user_id",
        string="Additional Viewers",
        domain=lambda self: [("groups_id", "in", [self.env.ref("upmin_iso.group_iso_doc_controller").id])],
    )

    _sql_constraints = [
        (
            "unique_swot",
            "unique(swot)",
            "TOWS for this SWOT analysis already exists.",
        )
    ]

    def action_export_swot_tows(self):
        wizard = self.env["upmin_iso.swot_tows_export_wizard"].create({"swot_id": self.swot.id})
        return {
            "type": "ir.actions.act_window",
            "name": "Export SWOT / TOWS",
            "res_model": "upmin_iso.swot_tows_export_wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }
