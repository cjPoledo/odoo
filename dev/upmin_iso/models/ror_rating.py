from odoo import models, fields, api


class RORRating(models.Model):
    _name = "upmin_iso.ror_rating"
    _description = "Risk and Opportunities Register Rating"
    _rec_name = "issue"
    _order = "create_date"

    issue = fields.Many2one(
        comodel_name="upmin_iso.ror", string="Issue", required=True, readonly=True
    )
    prev_rating = fields.Many2one(
        comodel_name="upmin_iso.ror_rating", string="Previous Rating", readonly=True
    )
    next_rating = fields.Many2one(
        comodel_name="upmin_iso.ror_rating", string="Next Rating", readonly=True
    )
    risk_likelihood = fields.Selection(
        selection=[
            ("4", "4 - Most Likely (No operational control in place)"),
            ("3", "3 - Possible (Ineffective controls)"),
            (
                "2",
                "2 - Remote (Effective control, Substitution and/or elimination is possible)",
            ),
            (
                "1",
                "1 - Improbable (Fully effective and adequate control; impact is substituted or eliminated)",
            ),
        ],
        string="Risk Likelihood",
        default="4",
    )
    opportunity_likelihood = fields.Selection(
        selection=[
            ("4", "4 - Most Likely (Highly certain that it will happen)"),
            ("3", "3 - Possible (May possibly happen)"),
            ("2", "2 - Remote (May happen in isolated circumstances)"),
            ("1", "1 - Improbable (Unlikely to happen)"),
        ],
        string="Opportunity Likelihood",
        default="4",
    )
    risk_frequency = fields.Selection(
        selection=[
            (
                "4",
                "4 - Continuous (Exposure occurs on daily basis; happened more than 5 times in the last 5 years)",
            ),
            (
                "3",
                "3 - Frequent (Routine exposure for a specific project; happened 3-5 times in the last 5 years)",
            ),
            (
                "2",
                "2 - Infrequent (Non-routine exposure; happened twice in the last 5 years)",
            ),
            (
                "1",
                "1 - Rare (Exposure occurs once or twice a year; happened once in the last 5 years)",
            ),
        ],
        string="Risk Frequency",
        default="4",
    )
    opportunity_frequency = fields.Selection(
        selection=[
            (
                "4",
                "4 - Continuous (Exposure occurs on daily basis; happened more than 5 times in the last 5 years)",
            ),
            (
                "3",
                "3 - Frequent (Routine exposure for a specific project; happened 3-5 times in the last 5 years)",
            ),
            (
                "2",
                "2 - Infrequent (Non-routine exposure; happened twice in the last 5 years)",
            ),
            (
                "1",
                "1 - Rare (Exposure occurs once or twice a year; happened once in the last 5 years)",
            ),
        ],
        string="Opportunity Frequency",
        default="4",
    )
    consequence_severity = fields.Selection(
        selection=[
            (
                "4",
                "4 - Severe/Catastrophic (May result to stoppage of operations, dissolution of program, or irreparable damage to public image or reputation)",
            ),
            (
                "3",
                "3 - Serious/Major (May result to major disallowances/government/regulatory findings or nonavailment of government benefits, considerable damage to public image or reputation, or major delays in the delivery of outputs)",
            ),
            (
                "2",
                "2 - Moderate (May result to minor government/regulatory findings or minor delays in the delivery of outputs)",
            ),
            (
                "1",
                "1 - Low/Insignificant (Not likely to result in client (internal or external) complaints or government/regulatory findings)",
            ),
        ],
        string="Consequence Severity",
        default="4",
    )
    benefit_severity = fields.Selection(
        selection=[
            (
                "4",
                "4 - Highly Advantageous (Significant contribution in meeting at least 75% of objectives/KRAs/KPIs or OPCR)",
            ),
            (
                "3",
                "3 - Major (Can contribute in meeting 50% of objectives/KRAs/KPIs or OPCR)",
            ),
            (
                "2",
                "2 - Minor (Can contribute in meeting 25% of objectives/KRAs/KPIs or OPCR)",
            ),
            (
                "1",
                "1 - Little or No Advantage (Contribution to meeting any objective is not significant)",
            ),
        ],
        string="Benefit Severity",
        default="4",
    )
    risk_rating = fields.Integer(
        string="Risk Rating", readonly=True, compute="_compute_risk_rating", store=True
    )
    opportunity_rating = fields.Integer(
        string="Opportunity Rating",
        readonly=True,
        compute="_compute_opportunity_rating",
        store=True,
    )
    risk_conclusion = fields.Selection(
        string="Risk Conclusion",
        selection=[
            ("significant", "Significant"),
            ("not significant", "Not Significant"),
        ],
        readonly=True,
        compute="_compute_risk_conclusion",
        store=True,
        default="significant",
        help="For significant risks, additional required action is a must.\nFor not significant risks, additional required action is not a must. However, the process owner may undertake an additional action to further lower down the risk rating.",
    )
    opportunity_conclusion = fields.Selection(
        string="Opportunity Conclusion",
        selection=[
            ("significant", "Significant"),
            ("not significant", "Not Significant"),
        ],
        readonly=True,
        compute="_compute_opportunity_conclusion",
        store=True,
        default="significant",
    )
    risk_required_action = fields.Text(
        string="Required Action (Risk)",
        help="What should be done to reduce the risk?",
    )
    opportunity_required_action = fields.Text(
        string="Required Action (Opportunity)",
        help="What should be done to maximize the opportunity?",
    )
    risk_responsible = fields.Char(
        string="Responsible (Risk)",
        help="Kindly indicate who's responsible to do the required action.",
    )
    opportunity_responsible = fields.Char(
        string="Responsible (Opportunity)",
        help="Kindly indicate who's responsible to do the required action.",
    )
    risk_due_date = fields.Date(
        string="Due Date (Risk)",
        help="Kindly indicate the due date to do the required action.",
    )
    opportunity_due_date = fields.Date(
        string="Due Date (Opportunity)",
        help="Kindly indicate the due date to do the required action.",
    )
    review_date = fields.Date(
        string="Review Date",
        help="Review is done every quarter to determine if action/s is/are effective or not.",
    )
    risk_status = fields.Text(string="Status/Results (Risk)")
    opportunity_status = fields.Text(string="Status/Results (Opportunity)")

    @api.depends("risk_likelihood", "risk_frequency", "consequence_severity")
    def _compute_risk_rating(self):
        for rating in self:
            rating.risk_rating = (
                int(rating.risk_frequency)
                * int(rating.risk_likelihood)
                * int(rating.consequence_severity)
            )

    @api.depends("opportunity_likelihood", "opportunity_frequency", "benefit_severity")
    def _compute_opportunity_rating(self):
        for rating in self:
            rating.opportunity_rating = (
                int(rating.opportunity_likelihood)
                * int(rating.opportunity_frequency)
                * int(rating.benefit_severity)
            )

    @api.depends("risk_rating")
    def _compute_risk_conclusion(self):
        for rating in self:
            if rating.risk_rating >= 27:
                rating.risk_conclusion = "significant"
            else:
                rating.risk_conclusion = "not significant"

    @api.depends("opportunity_rating")
    def _compute_opportunity_conclusion(self):
        for rating in self:
            if rating.opportunity_rating >= 27:
                rating.opportunity_conclusion = "significant"
            else:
                rating.opportunity_conclusion = "not significant"
