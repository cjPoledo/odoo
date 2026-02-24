from odoo import models, fields


class CCARCorrectiveActionEffectiveness(models.Model):
    _name = "upmin_iso.ccar_corrective_action_effectiveness"
    _description = "CCAR Corrective Action Effectiveness"
    _rec_name = "ccar"
    _order = "ccar"

    ccar = fields.Many2one(
        comodel_name="upmin_iso.ccar",
        string="CCAR",
        required=True,
        readonly=True,
    )
    corrective_action = fields.Text(string="Corrective Action")
    verification = fields.Text(string="How was verification performed?")
    verified_by = fields.Many2one(comodel_name="hr.employee", string="Who verified?")
    verified_date = fields.Date(string="Verified Date")
    approval = fields.Text(string="Approved/Rejected")
