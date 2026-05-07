from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AuditInfo(models.Model):
    _name = "upmin_iso.audit_info"
    _description = "ISO Internal Audit Information"
    _rec_name = "office_to_audit"
    _order = "office_to_audit"

    office_to_audit = fields.Many2one(
        comodel_name="hr.department", string="Office to Audit", required=True
    )
    audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period", string="Audit Period", required=True
    )
    internal_auditors = fields.Many2many(
        comodel_name="upmin_iso.internal_auditor",
        string="Internal Auditors",
    )
    audit_date = fields.Date(string="Audit Date")
    audit_time_start = fields.Float(
        string="Audit Time Start",
        help="Enter time in HH:MM format (24-hour). Examples: 8:00 AM = 8:00, 1:30 PM = 13:30, 5:00 PM = 17:00.",
        group_operator=False,
    )
    audit_time_end = fields.Float(
        string="Audit Time End",
        help="Enter time in HH:MM format (24-hour). Examples: 8:00 AM = 8:00, 1:30 PM = 13:30, 5:00 PM = 17:00.",
        group_operator=False,
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
        string="Is Staff?", default=True, compute="_compute_is_staff", store=False
    )
    is_office_auditor = fields.Boolean(
        string="Is Office Auditor?",
        default=False,
        compute="_compute_is_office_auditor",
        store=False,
    )

    is_finalized = fields.Boolean(
        string="Finalized?", related="audit_period.is_finalized", store=True
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

    def _compute_is_staff(self):
        for record in self:
            record.is_staff = self.env.user.has_group("upmin_iso.group_iso_staff")

    def _compute_is_office_auditor(self):
        current_user = self.env.user
        for record in self:
            record.is_office_auditor = bool(
                record.internal_auditors.sudo().filtered(
                    lambda a: a.name.user_id == current_user
                )
            )

    @api.depends("audit_findings", "audit_findings.rating", "audit_findings.is_duplicate")
    def _compute_ratings(self):
        for record in self:
            record.c = sum(
                1 for finding in record.audit_findings if finding.rating == "c"
            )
            record.nc = sum(
                1 for finding in record.audit_findings
                if finding.rating == "nc" and not finding.is_duplicate
            )
            record.ofi = sum(
                1 for finding in record.audit_findings if finding.rating == "ofi"
            )

    def unlink(self):
        if any(record.is_finalized for record in self):
            raise UserError("Cannot delete a finalized audit schedule.")
        self.mapped("audit_findings").sudo().unlink()
        return super().unlink()

    @api.constrains("internal_auditors", "office_to_audit")
    def _check_auditor_office_conflict(self):
        group_ids = set(
            self.env["upmin_iso.iso_access_group"].sudo().search([]).mapped("department_id").ids
        )

        def college_ancestors(ia_rec):
            result, seen = [], set()
            for dept in ia_rec.office:
                d = dept
                while d:
                    if d.id in group_ids and d.id not in seen:
                        result.append(d)
                        seen.add(d.id)
                    d = d.parent_id
            return result

        for rec in self:
            if not rec.office_to_audit or not rec.internal_auditors:
                continue

            conflicted_auditors = rec.internal_auditors.filtered(
                lambda a: rec.office_to_audit in a.office
                or rec.office_to_audit in college_ancestors(a)
            )

            if conflicted_auditors:
                raise ValidationError(
                    (
                        "An internal auditor cannot audit their own office or college.\n\n"
                        "Conflicted auditor(s): %s"
                    )
                    % ", ".join(conflicted_auditors.mapped("name.name"))
                )
