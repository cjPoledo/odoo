from odoo import models, fields

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
            [("id", "=", self.env.user.employee_id.department_id.id)]
            if self.env.user.employee_id and self.env.user.employee_id.department_id
            else []
        ),
    )
    related_swot = fields.Many2one(
        comodel_name="upmin_iso.swot",
        string="Related SWOT",
        help="Optionally link a SWOT to import issues from it.",
        domain=lambda self: (
            [("office", "=", self.env.user.employee_id.department_id.id)]
            if self.env.user.employee_id and self.env.user.employee_id.department_id
            else []
        ),
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
