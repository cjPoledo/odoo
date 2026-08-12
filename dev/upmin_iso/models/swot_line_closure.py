from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SWOTLineClosure(models.Model):
    _name = "upmin_iso.swot_line_closure"
    _description = "ISO SWOT Line Closure History"
    _order = "closed_date desc"

    swot_line_id = fields.Many2one(
        comodel_name="upmin_iso.swot_line",
        string="Issue",
        required=True,
        ondelete="cascade",
    )
    closed_date = fields.Date(string="Closed On", required=True, default=fields.Date.context_today)
    closed_reason = fields.Text(string="Reason for Closing", required=True)
    closed_by = fields.Many2one(comodel_name="hr.employee", string="Closed By", readonly=True)
    reopened_date = fields.Date(string="Reopened On")
    reopened_by = fields.Many2one(comodel_name="hr.employee", string="Reopened By", readonly=True)

    @api.constrains("closed_date", "reopened_date")
    def _check_dates(self):
        for rec in self:
            if rec.reopened_date and rec.reopened_date < rec.closed_date:
                raise ValidationError("The reopen date cannot be before the close date.")

    def _covers(self, a_date):
        """True if this closure was in effect on the given date."""
        if a_date < self.closed_date:
            return False
        return not self.reopened_date or a_date < self.reopened_date
