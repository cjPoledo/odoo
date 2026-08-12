from odoo import models, fields


class SWOTLineCloseWizard(models.TransientModel):
    _name = "upmin_iso.swot_line_close_wizard"
    _description = "Close Risk/Opportunity Issue"

    swot_line_id = fields.Many2one(
        comodel_name="upmin_iso.swot_line", string="Issue", required=True,
    )
    closed_reason = fields.Text(string="Reason for Closing", required=True)

    def action_confirm(self):
        self.ensure_one()
        self.swot_line_id.action_close(self.closed_reason)
        return {"type": "ir.actions.act_window_close"}
