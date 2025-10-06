from odoo import models, fields


class AuditFinding(models.Model):
    _name = "upmin_iso.audit_finding"
    _description = "ISO Audit Finding"
    _rec_name = "audit_info"
    _order = "audit_info"

    audit_info = fields.Many2one(
        comodel_name="upmin_iso.audit_info",
        string="Audit Information",
        required=True,
        readonly=True,
    )
    auditor = fields.Many2one(
        comodel_name="res.partner",
        string="Auditor",
        required=True,
        readonly=True,
        default=lambda self: self.env.user.partner_id,
    )
    clause = fields.Many2one(
        comodel_name="upmin_iso.iso_clause", string="Requirement/Clause"
    )
    question = fields.Char(string="Question")
    evidence = fields.Text(string="Scenario/Evidence")
    rating = fields.Selection(
        selection=[
            ("c", "Conformity"),
            ("nc", "Non-Conformity"),
            ("ofi", "Opportunity for Improvement"),
        ],
        string="Rating",
    )
    statement = fields.Text(string="Statement")
