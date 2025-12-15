from odoo import models, fields, api


class SWOTLine(models.Model):
    _name = "upmin_iso.swot_line"
    _description = "SWOT Line"
    _rec_name = "label"
    _order = "swot_id"

    swot_id = fields.Many2one(
        comodel_name="upmin_iso.swot", string="SWOT", required=True
    )
    description = fields.Text(string="Description", required=True)
    swot_type = fields.Selection(
        string="Type",
        selection=[
            ("S", "Strength"),
            ("W", "Weakness"),
            ("O", "Opportunity"),
            ("T", "Threat"),
        ],
        required=True,
        readonly=True,
    )
    label = fields.Char(
        string="Label", compute="_compute_label", store=True, readonly=True
    )

    # ROR stuff
    interested_parties = fields.Char(
        string="Interested Parties", help="Who are those affected by the issue?"
    )
    needs_and_exp = fields.Text(
        string="Needs and Expectations",
        help="What are the needs and expectations of the identified interested parties?",
    )
    compliance = fields.Html(
        string="Compliance Obligations",
        help='Is there any law, directive, issuance, statute, ordinance or regulation that\'s related to the issue?\nIf yes, then kindly indicate.\nIf none, kindly indicate "None".',
    )
    risks = fields.Text(
        string="Risks (R)", help="Identify the risk/s that may surface from the issue."
    )
    opportunities = fields.Text(
        string="Opportunities (O)",
        help="Indicate an opportunity that may be taken advantage of or capitalize, in relation to the issue.",
    )
    consequence = fields.Text(
        string="Consequence (C)", help="What's the effect if the risk is not addressed?"
    )
    benefit = fields.Text(
        string="Benefit (B)", help="What's the benefit if opportunity is availed of?"
    )
    risk_existing_control = fields.Text(
        string="Existing Control (Risks)",
        help='What is currently being done to address the risk?\nIf none, kindly indicate "None".',
    )
    opportunities_existing_control = fields.Text(
        string="Existing Control (Opportunities)",
        help='What is currently being done to avail of the opportunity?\nIf none, kindly indicate "None".',
    )

    @api.depends("swot_type", "swot_id")
    def _compute_label(self):
        for rec in self:

            # Always empty if missing type or parent
            if not rec.swot_type or not rec.swot_id:
                rec.label = False
                continue

            # If record is not saved yet → leave label empty
            if not isinstance(rec.id, int):
                rec.label = False
                continue

            field_by_type = {
                "S": "strengths",
                "W": "weaknesses",
                "O": "opportunities",
                "T": "threats",
            }

            siblings = rec.swot_id[field_by_type[rec.swot_type]]

            # Sort siblings reliably
            sibling_lines = siblings.sorted(key=lambda r: r.id or 0)

            # Find index (now always valid because rec.id is real)
            index = sibling_lines.ids.index(rec.id) + 1

            rec.label = f"{rec.swot_type}{index}"

    def unlink(self):
        # Group records by type so we process per type only once
        type_groups = {}
        for rec in self:
            type_groups.setdefault(rec.swot_type, self.env[self._name].browse())
            type_groups[rec.swot_type] |= rec

        for swot_type, recs_to_delete in type_groups.items():
            if swot_type not in ["S", "W", "O", "T"]:
                continue

            # Get the correct One2many list
            field = {
                "S": "strengths",
                "W": "weaknesses",
                "O": "opportunities",
                "T": "threats",
            }[swot_type]

            all_related = recs_to_delete[0].swot_id[field]

            # Exclude ALL records being deleted at once
            remaining = (all_related - recs_to_delete).sorted("id")

            # Recompute labels once
            for idx, line in enumerate(remaining, start=1):
                line.label = f"{swot_type}{idx}"

        return super().unlink()
