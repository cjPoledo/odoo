from odoo import models, fields, api
from odoo.exceptions import ValidationError
from collections import Counter


class ROR(models.Model):
    _name = "upmin_iso.ror"
    _description = "Risk and Opportunities Register"
    _rec_name = "issue"
    _order = "create_date"

    office = fields.Many2one(
        comodel_name="upmin_iso.office",
        string="Department",
        required=True,
        domain=lambda self: [("doc_controllers", "in", self.env.user.partner_id.id)],
    )
    issue_type = fields.Selection(
        selection=([("internal", "Internal Issue"), ("external", "External Issue")]),
        string="Issue Type",
        required=True,
        default="internal",
    )
    issue = fields.Char(
        string="Requirement/Issue",
        required=True,
        help="What could affect the attainment of goals?\n- Internal issues are Weaknesses in your SWOT\n- External issues are Threats in your SWOT",
    )
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
        comodel_name="upmin_iso.ror_rating", inverse_name="issue", string="Ratings"
    )
    ratings_status = fields.Char(
        string="Ratings Status", compute="_compute_ratings_status", store=False
    )

    # @api.depends("ratings", "ratings.review_date")
    def _compute_ratings_status(self):
        for rec in self:
            ratings = rec.env["upmin_iso.ror_rating"].search(
                domain=[("issue", "=", rec.id)]
            )
            if len(ratings) == 0:
                ratings_status_text = "Empty"
            else:
                mapped_ratings = ratings.mapped("review_date.review_date")
                required_ratings = (
                    rec.env["upmin_iso.review_period"]
                    .search([("review_date", ">=", mapped_ratings[0])])
                    .mapped("review_date")
                )
                for rating in mapped_ratings:
                    required_ratings.remove(rating)
                missing_ratings = ", ".join(
                    str(required_rating) for required_rating in required_ratings
                )
                if missing_ratings == "":
                    ratings_status_text = "Complete"
                else:
                    ratings_status_text = f"Missing: {missing_ratings}"

                ratings_progress = ratings.mapped("progress")
                for progress in ratings_progress:
                    if progress < 100:
                        ratings_status_text += " | Unfinished Reviews"
                        break
            rec.ratings_status = ratings_status_text

    @api.constrains("ratings")
    def _unique_ratings_constrain(self):
        for rec in self:
            review_dates = [
                str(rating.review_date.review_date) for rating in rec.ratings
            ]
            review_date_counts = Counter(review_dates)
            duplicates = [
                date for date, count in review_date_counts.items() if count > 1
            ]
            if duplicates:
                dup_str = ", ".join(duplicates)
                raise ValidationError(
                    f"The following review dates are duplicated: {dup_str}"
                )
