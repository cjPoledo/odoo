from odoo import models, fields


class CCARCorrectiveAction(models.Model):
    _name = "upmin_iso.ccar_corrective_action"
    _description = "CCAR Corrective Action"
    _rec_name = "ccar"
    _order = "ccar"

    ccar = fields.Many2one(
        comodel_name="upmin_iso.ccar",
        string="CCAR",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    corrective_action = fields.Text(string="Corrective Action (what was implemented)")
    effectiveness = fields.Text(
        string="Measure of Effectiveness and Monitoring Period for Corrective Action"
    )
    responsible = fields.Char(string="Responsible (who implemented)")
    start_date = fields.Date(string="Start Date")
    effective_date = fields.Date(string="Completion or Effective Date")
