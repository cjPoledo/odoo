from odoo import models, fields


class AuditFinding(models.Model):
    _name = "upmin_iso.audit_finding"
    _description = "ISO Audit Finding"
    _rec_name = "audit_info"
    _order = "audit_info, auditor, clause"

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
    question = fields.Char(string="Question", help="Guide question for the audit.")
    evidence = fields.Text(
        string="Scenario/Evidence",
        help="Describe the scenario or evidence found during the audit.",
    )
    rating = fields.Selection(
        selection=[
            ("c", "Conformity"),
            ("nc", "Non-Conformity"),
            ("ofi", "Opportunity for Improvement"),
        ],
        string="Rating",
    )
    statement = fields.Text(
        string="Statement", help="Justification for the rating based on the evidence."
    )

    related_audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period",
        string="Audit Period",
        related="audit_info.audit_period",
    )
    related_office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        related="audit_info.office_to_audit",
    )

    def name_get(self):
        result = []
        for record in self:
            office = record.audit_info.office_to_audit.name or ""
            rating = record.rating or ""
            clause = (
                f"{record.clause.clause_number} {record.clause.clause_title}".strip()
                if record.clause
                else ""
            )
            name = f"{office} ({rating}) - {clause}" if clause else f"{office} ({rating})"
            result.append((record.id, name))
        return result
