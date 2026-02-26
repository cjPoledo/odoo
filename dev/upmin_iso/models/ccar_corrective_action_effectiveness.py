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
    verification = fields.Text(string="How was verification performed?")
    allowed_verifiers = fields.Many2many(
        comodel_name="hr.employee",
        compute="_compute_allowed_verifiers",
        store=False,
    )
    verified_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Who verified?",
        domain="[('id', 'in', allowed_verifiers)]",
    )
    verified_date = fields.Date(string="Verified Date")
    approval = fields.Text(string="Approved/Rejected")

    def _compute_allowed_verifiers(self):
        for rec in self:
            if rec.ccar.related_nc and rec.ccar.related_nc.audit_info:
                rec.allowed_verifiers = (
                    rec.ccar.related_nc.audit_info.internal_auditors.mapped("name")
                )
            else:
                rec.allowed_verifiers = False
