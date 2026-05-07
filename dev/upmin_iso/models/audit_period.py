from odoo import models, fields
from odoo.exceptions import UserError


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
        domain=[("rating", "=", "nc"), ("is_duplicate", "=", False)],
        readonly=True,
    )
    related_ofi = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="related_audit_period",
        string="Opportunities for Improvement",
        domain=[("rating", "=", "ofi")],
        readonly=True,
    )
    ccars = fields.One2many(
        comodel_name="upmin_iso.ccar",
        inverse_name="audit_period",
        string="Issued CCARs",
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
            if not record.related_nc:
                raise UserError("No Non-Conformities found in this audit period. Nothing to generate.")
            year = fields.Date.today().year
            existing = CCAR.search([("ccar_no", "like", f"{year}-%")])
            latest = max(
                (int(c.ccar_no.split("-", 1)[1]) for c in existing if c.ccar_no.split("-", 1)[1].isdigit()),
                default=0,
            )
            UnitHead = self.env["upmin_iso.unit_head"].sudo()
            for i, nc in enumerate(record.related_nc):
                ccar_no = f"{year}-{latest + i + 1:02d}"
                office = nc.audit_info.office_to_audit if nc.audit_info else False
                unit_head = False
                if office:
                    uh = UnitHead.search([("office", "in", [office.id])], limit=1)
                    if uh:
                        unit_head = uh.name.id
                CCAR.create(
                    {
                        "ccar_no": ccar_no,
                        "date": fields.Date.today(),
                        "audit_period": record.id,
                        "related_nc": nc.id,
                        "responsible_person": unit_head,
                    }
                )

    def action_undo_generate_ccar(self):
        for record in self:
            record.ccars.unlink()

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.audit_start_date} to {record.audit_end_date}"
            result.append((record.id, name))
        return result
