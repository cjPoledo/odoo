from odoo import models, fields


class CCARCorrectionEffectiveness(models.Model):
    _name = "upmin_iso.ccar_correction_effectiveness"
    _description = "CCAR Correction Effectiveness"
    _rec_name = "ccar"
    _order = "ccar"

    ccar = fields.Many2one(
        comodel_name="upmin_iso.ccar",
        string="CCAR",
        required=True,
        readonly=True,
    )
    correction = fields.Text(string="Correction")
    verification = fields.Text(string="How was verification performed?")
    verified_by = fields.Char(string="Who verified?")
    verified_date = fields.Date(string="Verified Date")
    approval = fields.Selection(
        selection=[
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approved/Rejected",
    )
