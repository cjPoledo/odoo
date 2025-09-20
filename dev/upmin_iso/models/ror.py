from odoo import models, fields, api


class ROR(models.Model):
    _name = "upmin_iso.ror"
    _description = "Risk and Opportunities Register"
    _rec_name = "office"
    _order = "office"

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
    compliance = fields.Char(
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
    existing_control = fields.Text(
        string="Existing Control",
        help='What is currently being done to address the risk or avail of the opportunity?\nIf none, kindly indicate "None".',
    )
    ratings = fields.One2many(
        comodel_name="upmin_iso.ror_rating", inverse_name="issue", string="Ratings"
    )
