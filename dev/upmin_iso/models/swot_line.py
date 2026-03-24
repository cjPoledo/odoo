from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SWOTLine(models.Model):
    _name = "upmin_iso.swot_line"
    _description = "SWOT Line"
    _rec_name = "label"
    _order = "swot_id,ror_id,label"

    swot_id = fields.Many2one(
        comodel_name="upmin_iso.swot", string="SWOT"
    )
    ror_id = fields.Many2one(
        comodel_name="upmin_iso.ror", string="ROR", ondelete="cascade"
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

    # Risk and Opportunity fields (filled in ROR context)
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
    ratings = fields.One2many(
        comodel_name="upmin_iso.ror_rating",
        inverse_name="issue",
        string="Ratings",
    )

    # remarks
    fields_status = fields.Text(
        string="Fields Status", compute="_compute_fields_status",
    )
    ratings_status = fields.Text(
        string="Ratings Status", compute="_compute_ratings_status",
    )

    @api.depends(
        "interested_parties", "needs_and_exp", "compliance", "risks",
        "opportunities", "consequence", "benefit",
        "risk_existing_control", "opportunities_existing_control",
    )
    def _compute_fields_status(self):
        for rec in self:
            status_list = []
            field_names = [
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
            for field_name in field_names:
                if not rec[field_name]:
                    field_label = rec._fields[field_name].string
                    status_list.append(field_label)

            if not status_list:
                rec.fields_status = "All fields are filled."
            else:
                rec.fields_status = "Missing: " + ", ".join(status_list)

    @api.depends("ratings", "ratings.progress", "ratings.review_date", "ratings.risk_conclusion")
    def _compute_ratings_status(self):
        for rec in self:
            completed_ratings = rec.ratings.filtered(lambda r: r.progress == 100)
            incomplete_ratings = rec.ratings - completed_ratings
            status = ""
            if len(completed_ratings) > 0:
                status = "Latest review completed: "
                last_date = max(completed_ratings.mapped("review_date"))
                status += last_date.strftime("%Y-%m-%d")
                latest_rating = completed_ratings.filtered(
                    lambda r: r.review_date == last_date
                )[:1]
                status += f"\n(Risk is {latest_rating.risk_conclusion})"
            else:
                status = "Risk not yet rated."
            if len(incomplete_ratings) > 0:
                status += f"\n{len(incomplete_ratings)} rating(s) incomplete."
            rec.ratings_status = status

    @api.constrains("swot_id", "ror_id")
    def _check_parent(self):
        for rec in self:
            if not rec.swot_id and not rec.ror_id:
                raise ValidationError("A SWOT line must belong to either a SWOT or a ROR.")

    @api.depends("swot_type", "swot_id")
    def _compute_label(self):
        for rec in self:

            # Always empty if missing type or parent (standalone ROR lines have no swot_id)
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
        # Only recompute labels for lines that belong to a SWOT
        type_groups = {}
        for rec in self:
            if not rec.swot_id:
                continue
            type_groups.setdefault(rec.swot_type, self.env[self._name].browse())
            type_groups[rec.swot_type] |= rec

        for swot_type, recs_to_delete in type_groups.items():
            if swot_type not in ["S", "W", "O", "T"]:
                continue

            field = {
                "S": "strengths",
                "W": "weaknesses",
                "O": "opportunities",
                "T": "threats",
            }[swot_type]

            all_related = recs_to_delete[0].swot_id[field]
            remaining = (all_related - recs_to_delete).sorted("id")

            for idx, line in enumerate(remaining, start=1):
                line.label = f"{swot_type}{idx}"

        return super().unlink()
