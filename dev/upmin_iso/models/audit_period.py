from odoo import models, fields


class AuditPeriod(models.Model):
    _name = "upmin_iso.audit_period"
    _description = "ISO Internal Audit Period"
    _rec_name = "audit_start_date"
    _order = "audit_start_date"

    audit_start_date = fields.Date(string="Audit Start Date", required=True)
    audit_end_date = fields.Date(string="Audit End Date", required=True)

    _sql_constraints = [
        (
            "audit_start_date_unique",
            "unique(audit_start_date)",
            "Audit start date must be unique.",
        ),
        (
            "audit_end_date_after_start_date",
            "CHECK(audit_end_date >= audit_start_date)",
            "Audit end date must be same or after the start date.",
        ),
    ]
