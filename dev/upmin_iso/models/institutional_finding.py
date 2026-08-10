from odoo import models, fields, api


class InstitutionalFinding(models.Model):
    _name = "upmin_iso.institutional_finding"
    _description = "ISO Institutional Finding"
    _order = "id"

    audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period",
        string="Audit Period",
        required=True,
        readonly=True,
    )
    clause = fields.Many2one(
        comodel_name="upmin_iso.iso_clause",
        string="Clause",
        required=True,
    )
    supporting_clause_ids = fields.Many2many(
        comodel_name="upmin_iso.iso_clause",
        relation="upmin_iso_institutional_finding_supporting_clause_rel",
        string="Supporting Clauses",
    )
    description = fields.Text(
        string="Description",
        help="Summary of the shared root cause or nonconformity pattern across offices.",
    )
    finding_ids = fields.One2many(
        comodel_name="upmin_iso.audit_finding",
        inverse_name="institutional_finding_id",
        string="Member Findings",
    )
    office_ids = fields.Many2many(
        comodel_name="hr.department",
        string="Offices",
        compute="_compute_office_ids",
    )
    office_display = fields.Char(
        string="Office(s)",
        compute="_compute_office_ids",
    )
    finding_count = fields.Integer(
        string="Finding Count",
        compute="_compute_office_ids",
    )

    @api.depends("finding_ids", "finding_ids.audit_info.office_to_audit")
    def _compute_office_ids(self):
        for record in self:
            offices = record.finding_ids.mapped("audit_info.office_to_audit")
            record.office_ids = offices
            record.office_display = ", ".join(offices.mapped("name"))
            record.finding_count = len(record.finding_ids)

    def name_get(self):
        result = []
        for record in self:
            clause = (
                f"{record.clause.clause_number} {record.clause.clause_title}".strip()
                if record.clause
                else str(record.id)
            )
            result.append((record.id, clause))
        return result
