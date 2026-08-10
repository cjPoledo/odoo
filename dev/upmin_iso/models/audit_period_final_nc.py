from odoo import models, fields, tools


class AuditPeriodFinalNC(models.Model):
    """Read-only projection of an audit period's *final* nonconformity count.

    Each row is either one Institutional Finding (spanning multiple offices,
    counted once) or one ungrouped individual audit finding (counted as
    before). Together they represent the true final NC list for the period,
    since grouped findings must not be double-counted with their
    institutional finding.
    """

    _name = "upmin_iso.audit_period_final_nc"
    _description = "ISO Audit Period Final Nonconformity"
    _auto = False
    _order = "kind desc, id"

    audit_period_id = fields.Many2one(
        comodel_name="upmin_iso.audit_period", string="Audit Period", readonly=True
    )
    kind = fields.Selection(
        selection=[("institutional", "Institutional"), ("individual", "Individual")],
        string="Kind",
        readonly=True,
    )
    display_name = fields.Char(string="Reference", readonly=True)
    clause_display = fields.Html(string="Clause Details", readonly=True)
    office_display = fields.Char(string="Office(s)", readonly=True)
    institutional_finding_id = fields.Many2one(
        comodel_name="upmin_iso.institutional_finding",
        string="Institutional Finding",
        readonly=True,
    )
    audit_finding_id = fields.Many2one(
        comodel_name="upmin_iso.audit_finding", string="Audit Finding", readonly=True
    )

    def action_open_record(self):
        self.ensure_one()
        if self.kind == "institutional":
            return {
                "type": "ir.actions.act_window",
                "res_model": "upmin_iso.institutional_finding",
                "res_id": self.institutional_finding_id.id,
                "view_mode": "form",
                "views": [[False, "form"]],
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "res_model": "upmin_iso.audit_finding",
            "res_id": self.audit_finding_id.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    -1000000 - inc.id AS id,
                    inc.audit_period AS audit_period_id,
                    'institutional' AS kind,
                    NULL AS display_name,
                    (
                        SELECT string_agg(
                            '<strong>' || COALESCE(c.clause_number, '') || '</strong> '
                                || COALESCE(c.clause_title, ''),
                            '<br/>'
                        )
                        FROM (
                            SELECT cl.clause_number, cl.clause_title
                            FROM upmin_iso_iso_clause cl WHERE cl.id = inc.clause
                            UNION ALL
                            SELECT cl.clause_number, cl.clause_title
                            FROM upmin_iso_institutional_finding_supporting_clause_rel rel
                            JOIN upmin_iso_iso_clause cl ON cl.id = rel.upmin_iso_iso_clause_id
                            WHERE rel.upmin_iso_institutional_finding_id = inc.id
                        ) c
                    ) AS clause_display,
                    (
                        SELECT string_agg(DISTINCT dept.name, ', ')
                        FROM upmin_iso_audit_finding af2
                        JOIN upmin_iso_audit_info ai2 ON ai2.id = af2.audit_info
                        JOIN hr_department dept ON dept.id = ai2.office_to_audit
                        WHERE af2.institutional_finding_id = inc.id
                    ) AS office_display,
                    inc.id AS institutional_finding_id,
                    NULL::integer AS audit_finding_id
                FROM upmin_iso_institutional_finding inc

                UNION ALL

                SELECT
                    af.id AS id,
                    ai.audit_period AS audit_period_id,
                    'individual' AS kind,
                    NULL AS display_name,
                    (
                        SELECT string_agg(
                            '<strong>' || COALESCE(c.clause_number, '') || '</strong> '
                                || COALESCE(c.clause_title, ''),
                            '<br/>'
                        )
                        FROM (
                            SELECT cl.clause_number, cl.clause_title
                            FROM upmin_iso_iso_clause cl WHERE cl.id = af.clause
                            UNION ALL
                            SELECT cl.clause_number, cl.clause_title
                            FROM upmin_iso_audit_finding_supporting_clause_rel rel
                            JOIN upmin_iso_iso_clause cl ON cl.id = rel.upmin_iso_iso_clause_id
                            WHERE rel.upmin_iso_audit_finding_id = af.id
                        ) c
                    ) AS clause_display,
                    dept.name AS office_display,
                    NULL::integer AS institutional_finding_id,
                    af.id AS audit_finding_id
                FROM upmin_iso_audit_finding af
                JOIN upmin_iso_audit_info ai ON ai.id = af.audit_info
                JOIN hr_department dept ON dept.id = ai.office_to_audit
                WHERE af.rating = 'nc'
                    AND af.is_duplicate IS NOT TRUE
                    AND af.institutional_finding_id IS NULL
            )
        """)
