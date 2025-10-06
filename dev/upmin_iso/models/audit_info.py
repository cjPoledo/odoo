from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AuditInfo(models.Model):
    _name = "upmin_iso.audit_info"
    _description = "ISO Internal Audit Information"
    _rec_name = "audit_start_datetime"
    _order = "audit_start_datetime"

    office_to_audit = fields.Many2one(
        comodel_name="upmin_iso.office", string="Office to Audit", required=True
    )
    audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period", string="Audit Period", required=True
    )
    internal_auditors = fields.Many2many(
        comodel_name="res.partner",
        string="Internal Auditors",
        domain=lambda self: self._get_internal_auditor_domain(),
    )
    audit_start_datetime = fields.Datetime(string="Audit Start Date", required=True)
    audit_end_datetime = fields.Datetime(string="Audit End Date", required=True)
    audit_findings = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="audit_info",
        string="Audit Findings",
    )

    _sql_constraints = [
        (
            "unique_audit_schedule",
            "unique(office_to_audit, audit_period)",
            "An audit for this office in the selected period already exists.",
        ),
        (
            "check_audit_dates",
            "CHECK(audit_end_datetime >= audit_start_datetime)",
            "Audit end date must be same or after start date.",
        ),
    ]

    @api.model
    def _get_internal_auditor_domain(self):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")
        users = self.env["res.users"].search([("groups_id", "in", group.id)])
        partners = users.mapped("partner_id")
        return [("id", "in", partners.ids)]

    @api.constrains("internal_auditors", "office_to_audit")
    def _check_internal_auditors_not_in_office(self):
        for record in self:
            if record.internal_auditors and record.office_to_audit:
                office_auditors = record.office_to_audit.internal_auditors
                conflicting_auditors = record.internal_auditors & office_auditors
                if conflicting_auditors:
                    raise ValidationError(
                        "Internal auditors must not be assigned if they are internal auditors of the office being audited."
                        "\nConflicting auditors: %s"
                        % ", ".join(conflicting_auditors.mapped("name"))
                    )
