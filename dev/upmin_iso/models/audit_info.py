from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AuditInfo(models.Model):
    _name = "upmin_iso.audit_info"
    _description = "ISO Internal Audit Information"
    _rec_name = "office_to_audit"
    _order = "office_to_audit"

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
    audit_date = fields.Date(string="Audit Date")
    audit_time_start = fields.Float(
        string="Audit Time Start",
        help="Please use 24-hour format\n(e.g., 1 PM = 13:00)",
    )
    audit_time_end = fields.Float(
        string="Audit Time End", help="Please use 24-hour format\n(e.g., 1 PM = 13:00)"
    )
    audit_findings = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="audit_info",
        string="Audit Findings",
    )

    c = fields.Integer(
        string="C", default=0, compute="_compute_ratings", store=True, readonly=True
    )
    nc = fields.Integer(
        string="NC", default=0, compute="_compute_ratings", store=True, readonly=True
    )
    ofi = fields.Integer(
        string="OFI", default=0, compute="_compute_ratings", store=True, readonly=True
    )

    is_staff = fields.Boolean(
        string="Is Staff?", default=False, compute="_compute_is_staff", store=False
    )
    is_office_auditor = fields.Boolean(
        string="Is Office Auditor?",
        default=False,
        compute="_compute_is_office_auditor",
        store=False,
    )

    _sql_constraints = [
        (
            "unique_audit_schedule",
            "unique(office_to_audit, audit_period)",
            "An audit for this office in the selected period already exists.",
        ),
        (
            "check_audit_times",
            "CHECK(audit_time_end >= audit_time_start)",
            "Audit end time must be same or after start time.",
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

    def _compute_is_staff(self):
        for record in self:
            record.is_staff = self.env.user.has_group("upmin_iso.group_iso_staff")

    def _compute_is_office_auditor(self):
        for record in self:
            record.is_office_auditor = (
                self.env.user.partner_id in record.internal_auditors
            )

    @api.depends("audit_findings", "audit_findings.rating")
    def _compute_ratings(self):
        for record in self:
            record.c = sum(
                1 for finding in record.audit_findings if finding.rating == "c"
            )
            record.nc = sum(
                1 for finding in record.audit_findings if finding.rating == "nc"
            )
            record.ofi = sum(
                1 for finding in record.audit_findings if finding.rating == "ofi"
            )
