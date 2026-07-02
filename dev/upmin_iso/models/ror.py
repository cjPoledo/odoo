from datetime import date as _date

from odoo import models, fields, api

_COPY_FIELDS = [
    "description",
    "interested_parties",
    "needs_and_exp",
    "compliance",
    "risks",
    "opportunities",
    "consequence",
    "benefit",
    "risk_existing_control",
    "opportunities_existing_control",
]


class ROR(models.Model):
    _name = "upmin_iso.ror"
    _description = "Risk and Opportunities Register"
    _rec_name = "office"
    _order = "create_date"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    office = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        required=True,
        domain=lambda self: (
            []
            if self.env.user.has_group("upmin_iso.group_iso_staff")
            else (
                [("id", "in", self.env.user.employee_id.iso_office_ids.ids
                    + self.env.user.employee_id.iso_ancestor_ids.ids)]
                if self.env.user.employee_id
                else []
            )
        ),
    )
    related_swot = fields.Many2one(
        comodel_name="upmin_iso.swot",
        string="Related SWOT",
        help="Optionally link a SWOT to import issues from it.",
        domain=lambda self: (
            []
            if self.env.user.has_group("upmin_iso.group_iso_staff")
            else (
                [("office", "in", self.env.user.employee_id.iso_office_ids.ids
                    + self.env.user.employee_id.iso_ancestor_ids.ids)]
                if self.env.user.employee_id
                else []
            )
        ),
    )
    bypass_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="upmin_iso_ror_bypass_user_rel",
        column1="ror_id",
        column2="user_id",
        string="Additional Viewers",
        domain=lambda self: [("groups_id", "in", [self.env.ref("upmin_iso.group_iso_doc_controller").id])],
    )

    pending_this_quarter = fields.Integer(
        string="Pending This Quarter",
        compute="_compute_pending_this_quarter",
    )

    internal_issues = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="ror_id",
        string="Internal Issues",
        domain=[("swot_type", "=", "W")],
        context={"default_swot_type": "W"},
        help="What could affect the attainment of goals?\nInternal issues are weaknesses.",
    )
    external_issues = fields.One2many(
        comodel_name="upmin_iso.swot_line",
        inverse_name="ror_id",
        string="External Issues",
        domain=[("swot_type", "=", "T")],
        context={"default_swot_type": "T"},
        help="What could affect the attainment of goals?\nExternal issues are threats.",
    )


    def _current_quarter_end(self):
        today = fields.Date.context_today(self)
        year = today.year
        for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
            q = _date(year, month, day)
            if q >= today:
                return q
        return _date(year + 1, 3, 31)

    def _compute_pending_this_quarter(self):
        RORRating = self.env["upmin_iso.ror_rating"]
        for rec in self:
            q_end = rec._current_quarter_end()
            issues = rec.internal_issues + rec.external_issues
            if not issues:
                rec.pending_this_quarter = 0
                continue
            completed_ids = set(
                RORRating.search([
                    ("issue", "in", issues.ids),
                    ("review_date", "=", q_end),
                    ("progress", "=", 100),
                ]).mapped("issue").ids
            )
            rec.pending_this_quarter = sum(1 for i in issues if i.id not in completed_ids)

    def action_generate_quarter_ratings(self):
        RORRating = self.env["upmin_iso.ror_rating"]
        for rec in self:
            q_end = rec._current_quarter_end()
            issues = rec.internal_issues + rec.external_issues
            if not issues:
                continue
            existing_ids = set(
                RORRating.search([
                    ("issue", "in", issues.ids),
                    ("review_date", "=", q_end),
                ]).mapped("issue").ids
            )
            to_create = [
                {"issue": issue.id, "review_date": q_end}
                for issue in issues if issue.id not in existing_ids
            ]
            if to_create:
                RORRating.create(to_create)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._subscribe_default_followers()
        return records

    def _subscribe_default_followers(self):
        partner_ids = set()

        # Document controllers and unit heads for this office (direct or college-level)
        all_dcs = self.env["upmin_iso.document_controller"].sudo().search([])
        for dc in all_dcs.filtered(
            lambda dc: self.office in dc.office or self.office in dc.name.iso_ancestor_ids
        ):
            if dc.name.user_id and dc.name.user_id.partner_id:
                partner_ids.add(dc.name.user_id.partner_id.id)

        all_uhs = self.env["upmin_iso.unit_head"].sudo().search([])
        for uh in all_uhs.filtered(
            lambda uh: self.office in uh.office or self.office in uh.name.iso_ancestor_ids
        ):
            if uh.name.user_id and uh.name.user_id.partner_id:
                partner_ids.add(uh.name.user_id.partner_id.id)

        # All ISO Staff
        staff_group = self.env.ref("upmin_iso.group_iso_staff")
        for user in staff_group.users:
            if user.partner_id:
                partner_ids.add(user.partner_id.id)

        if partner_ids:
            self.message_subscribe(partner_ids=list(partner_ids))

    def action_export_xlsx(self):
        wizard = self.env["upmin_iso.ror_export_wizard"].create({"ror_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "name": "Export ROR",
            "res_model": "upmin_iso.ror_export_wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_import_xlsx(self):
        wizard = self.env["upmin_iso.ror_import_wizard"].create({"ror_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "name": "Import ROR",
            "res_model": "upmin_iso.ror_import_wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_import_from_swot(self):
        for rec in self:
            if not rec.related_swot:
                continue

            existing_descriptions = set(
                (rec.internal_issues + rec.external_issues).mapped("description")
            )

            swot_lines = rec.related_swot.weaknesses + rec.related_swot.threats
            to_create = []
            for line in swot_lines:
                if line.description in existing_descriptions:
                    continue
                vals = {f: line[f] for f in _COPY_FIELDS}
                vals["swot_type"] = line.swot_type
                vals["ror_id"] = rec.id
                to_create.append(vals)
            if to_create:
                self.env["upmin_iso.swot_line"].create(to_create)
