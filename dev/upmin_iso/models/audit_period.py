from odoo import models, fields


class AuditPeriod(models.Model):
    _name = "upmin_iso.audit_period"
    _description = "ISO Internal Audit Period"
    _rec_name = "audit_start_date"
    _order = "audit_start_date"

    audit_start_date = fields.Date(string="Audit Start Date", required=True)
    audit_end_date = fields.Date(string="Audit End Date", required=True)
    is_finalized = fields.Boolean(
        string="Finalized?",
        default=False,
        help="Mark as finalized to prevent further editing and enable report generation.",
    )

    related_c = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="related_audit_period",
        string="Conformities",
        domain=[("rating", "=", "c")],
        readonly=True,
    )
    related_nc = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="related_audit_period",
        string="Nonconformities",
        domain=[("rating", "=", "nc")],
        readonly=True,
    )
    related_ofi = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="related_audit_period",
        string="Opportunities for Improvement",
        domain=[("rating", "=", "ofi")],
        readonly=True,
    )

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

    def action_finalize(self):
        for record in self:
            record.is_finalized = True

    def action_unfinalize(self):
        for record in self:
            record.is_finalized = False

    def action_generate_ccar(self):
        CCAR = self.env["upmin_iso.ccar"]
        for record in self:
            for nc in record.related_nc:
                year = fields.Date.today().year
                count = (
                    self.env["upmin_iso.ccar"].search_count(
                        [("ccar_no", "like", f"{year}-%")]
                    )
                    + 1
                )
                ccar_no = f"{year}-{count:02d}"
                CCAR.create(
                    {
                        "ccar_no": ccar_no,
                        "date": fields.Date.today(),
                        "audit_period": record.id,
                        "related_nc": nc.id,
                    }
                )

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.audit_start_date} to {record.audit_end_date}"
            result.append((record.id, name))
        return result
