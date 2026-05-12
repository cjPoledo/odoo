from odoo import api, models, fields


class AuditFinding(models.Model):
    _name = "upmin_iso.audit_finding"
    _description = "ISO Audit Finding"
    _rec_name = "audit_info"
    _order = "audit_info, auditor, clause_sortkey"

    audit_info = fields.Many2one(
        comodel_name="upmin_iso.audit_info",
        string="Audit Information",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    auditor = fields.Many2one(
        comodel_name="res.partner",
        string="Auditor",
        required=True,
        default=lambda self: self.env.user.partner_id,
    )
    available_auditor_ids = fields.Many2many(
        comodel_name="res.partner",
        compute="_compute_available_auditor_ids",
        store=False,
    )
    clause = fields.Many2one(
        comodel_name="upmin_iso.iso_clause", string="Requirement/Clause"
    )
    supporting_clause_ids = fields.Many2many(
        comodel_name="upmin_iso.iso_clause",
        relation="upmin_iso_audit_finding_supporting_clause_rel",
        string="Supporting Clauses",
    )
    clause_display = fields.Html(
        string="Requirement/Clause",
        compute="_compute_clause_display",
        store=False,
    )
    clause_sortkey = fields.Char(related="clause.clause_number_sortkey", store=True)
    question = fields.Text(string="Question", help="Guide question for the audit.")
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
    is_duplicate = fields.Boolean(string="Duplicate?", default=False)

    is_staff = fields.Boolean(compute="_compute_is_staff", store=False)
    is_audit_auditor = fields.Boolean(compute="_compute_is_audit_auditor", store=False)

    related_audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period",
        string="Audit Period",
        related="audit_info.audit_period",
    )
    related_office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        related="audit_info.office_to_audit",
        store=True,
    )

    @api.depends("audit_info.internal_auditors")
    def _compute_available_auditor_ids(self):
        for record in self:
            record.available_auditor_ids = record.audit_info.internal_auditors.mapped(
                "name.work_contact_id"
            )

    @api.depends("audit_info")
    def _compute_is_staff(self):
        for record in self:
            record.is_staff = self.env.user.has_group("upmin_iso.group_iso_staff")

    @api.depends("audit_info.internal_auditors")
    def _compute_is_audit_auditor(self):
        current_user = self.env.user
        for record in self:
            record.is_audit_auditor = bool(
                record.audit_info.internal_auditors.filtered(
                    lambda a: a.name.user_id == current_user
                )
            )

    @api.depends("clause", "supporting_clause_ids")
    def _compute_clause_display(self):
        for record in self:
            parts = []
            if record.clause:
                num = record.clause.clause_number or ""
                title = record.clause.clause_title or ""
                parts.append(f"<strong>{num}</strong> {title}".strip())
            for sc in record.supporting_clause_ids:
                num = sc.clause_number or ""
                title = sc.clause_title or ""
                parts.append(f"<strong>{num}</strong> {title}".strip())
            record.clause_display = "<br/>".join(parts) if parts else False

    _RATING_LABEL = {"c": "C", "nc": "NC", "ofi": "OFI"}

    def name_get(self):
        result = []
        for record in self:
            rating = self._RATING_LABEL.get(record.rating, record.rating or "")
            clause = (
                f"{record.clause.clause_number} {record.clause.clause_title}".strip()
                if record.clause
                else ""
            )
            snippet_src = record.statement or record.evidence or record.auditor.name or ""
            snippet = (snippet_src[:60] + "…") if len(snippet_src) > 60 else snippet_src
            parts = [p for p in [rating, clause, snippet] if p]
            result.append((record.id, " – ".join(parts) or str(record.id)))
        return result
