from odoo import models, fields


class ReviewPeriod(models.Model):
    _name = "upmin_iso.review_period"
    _description = "ISO Documents Review Period"
    _rec_name = "review_date"
    _order = "review_date"

    review_date = fields.Date(string="Review Date", required=True)
