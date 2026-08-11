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

    audit_infos = fields.One2many(
        comodel_name="upmin_iso.audit_info",
        inverse_name="audit_period",
        string="Offices Audited",
        readonly=True,
    )
    office_count = fields.Integer(
        string="Offices Audited",
        compute="_compute_office_counts",
    )
    offices_without_nc_ids = fields.Many2many(
        comodel_name="hr.department",
        string="Offices Without NC",
        compute="_compute_office_counts",
    )
    offices_without_nc_count = fields.Integer(
        string="Offices Without NC",
        compute="_compute_office_counts",
    )

    def _compute_office_counts(self):
        for record in self:
            record.office_count = len(record.audit_infos)
            without_nc = record.audit_infos.filtered(lambda ai: ai.nc == 0)
            record.offices_without_nc_ids = without_nc.mapped("office_to_audit")
            record.offices_without_nc_count = len(without_nc)

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
    institutional_findings = fields.One2many(
        comodel_name="upmin_iso.institutional_finding",
        inverse_name="audit_period",
        string="Institutional Findings",
        readonly=True,
    )
    final_nc_ids = fields.One2many(
        comodel_name="upmin_iso.audit_period_final_nc",
        inverse_name="audit_period_id",
        string="Final NCs",
        readonly=True,
    )
    final_nc_count = fields.Integer(
        string="Final NC Count",
        compute="_compute_final_nc_count",
    )
    c_count = fields.Integer(
        string="Conformities",
        compute="_compute_final_nc_count",
    )
    ofi_count = fields.Integer(
        string="Opportunities for Improvement",
        compute="_compute_final_nc_count",
    )

    def _compute_final_nc_count(self):
        for record in self:
            record.final_nc_count = len(record.final_nc_ids)
            record.c_count = len(record.related_c)
            record.ofi_count = len(record.related_ofi)

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

    def action_open_institutional_finding_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Group into Institutional Finding",
            "res_model": "upmin_iso.institutional_finding_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_audit_period_id": self.id},
        }

    def action_view_offices_audited(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Offices Audited",
            "res_model": "upmin_iso.audit_info",
            "view_mode": "tree,form",
            "domain": [("audit_period", "=", self.id)],
            "context": {"upmin_iso_dept_short": True},
        }

    def _dashboard_finding_views(self):
        tree_id = self.env.ref("upmin_iso.audit_finding_view_tree_dashboard").id
        form_id = self.env.ref("upmin_iso.audit_finding_view_form_dashboard").id
        return [(tree_id, "tree"), (form_id, "form")]

    def action_view_c(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Conformities",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "views": self._dashboard_finding_views(),
            "domain": [("id", "in", self.related_c.ids)],
            "context": {"upmin_iso_dept_short": True, "search_default_group_by_office": 1},
        }

    def action_view_final_nc(self):
        self.ensure_one()
        tree_id = self.env.ref("upmin_iso.audit_period_final_nc_view_tree").id
        return {
            "type": "ir.actions.act_window",
            "name": "Final Nonconformities",
            "res_model": "upmin_iso.audit_period_final_nc",
            "view_mode": "tree",
            "views": [(tree_id, "tree")],
            "domain": [("id", "in", self.final_nc_ids.ids)],
        }

    def action_view_ofi(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Opportunities for Improvement",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "views": self._dashboard_finding_views(),
            "domain": [("id", "in", self.related_ofi.ids)],
            "context": {"upmin_iso_dept_short": True, "search_default_group_by_office": 1},
        }

    def action_view_offices_without_nc(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Offices Without NC",
            "res_model": "upmin_iso.audit_info",
            "view_mode": "tree,form",
            "domain": [
                ("audit_period", "=", self.id),
                ("office_to_audit", "in", self.offices_without_nc_ids.ids),
            ],
            "context": {"upmin_iso_dept_short": True},
        }

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.audit_start_date} to {record.audit_end_date}"
            result.append((record.id, name))
        return result
