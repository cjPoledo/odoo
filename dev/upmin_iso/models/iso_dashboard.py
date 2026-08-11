from datetime import date as _date

from odoo import models, fields, api


def _current_quarter_end():
    today = _date.today()
    for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
        q = _date(today.year, month, day)
        if q >= today:
            return q
    return _date(today.year + 1, 3, 31)


class IsoDashboard(models.TransientModel):
    _name = "upmin_iso.iso_dashboard"
    _description = "ISO Dashboard"
    _rec_name = "name"

    name = fields.Char(default="ISO Dashboard")

    # ── CCAR ──────────────────────────────────────────────────────────────
    ccar_open = fields.Integer(compute="_compute_all")
    ccar_creation = fields.Integer(compute="_compute_all")
    ccar_awaiting_qao = fields.Integer(compute="_compute_all")
    ccar_awaiting_office = fields.Integer(compute="_compute_all")
    ccar_in_verification = fields.Integer(compute="_compute_all")
    ccar_completed_year = fields.Integer(compute="_compute_all")

    # ── Audit (current period) ─────────────────────────────────────────────
    current_period = fields.Many2one("upmin_iso.audit_period", compute="_compute_all")
    has_period = fields.Boolean(compute="_compute_all")
    audit_offices = fields.Integer(compute="_compute_all")
    year_offices = fields.Integer(compute="_compute_all")
    audit_c = fields.Integer(compute="_compute_all")
    audit_nc = fields.Integer(compute="_compute_all")
    audit_ofi = fields.Integer(compute="_compute_all")
    nc_without_ccar = fields.Integer(compute="_compute_all")
    ia_not_assigned = fields.Integer(compute="_compute_all")
    year_c = fields.Integer(compute="_compute_all")
    year_nc = fields.Integer(compute="_compute_all")
    year_ofi = fields.Integer(compute="_compute_all")

    # ── ROR ───────────────────────────────────────────────────────────────
    ror_pending_offices = fields.Integer(compute="_compute_all")
    significant_risks = fields.Integer(compute="_compute_all")
    ror_with_skipped = fields.Integer(compute="_compute_all")
    ror_with_incomplete_past = fields.Integer(compute="_compute_all")

    # ── Directory ─────────────────────────────────────────────────────────
    ia_trained_certified = fields.Integer(compute="_compute_all")
    ia_trained_not_certified = fields.Integer(compute="_compute_all")
    dc_trained = fields.Integer(compute="_compute_all")

    @api.depends()
    def _compute_all(self):
        CCAR = self.env["upmin_iso.ccar"]
        Finding = self.env["upmin_iso.audit_finding"]
        Period = self.env["upmin_iso.audit_period"]
        FinalNC = self.env["upmin_iso.audit_period_final_nc"]
        ROR = self.env["upmin_iso.ror"]
        Rating = self.env["upmin_iso.ror_rating"]
        Line = self.env["upmin_iso.swot_line"]
        IA = self.env["upmin_iso.internal_auditor"]
        DC = self.env["upmin_iso.document_controller"]

        today = _date.today()
        q_end = _current_quarter_end()

        # CCAR counts
        ccar_open = CCAR.search([("status", "!=", "completed")])
        ccar_creation = ccar_open.filtered(lambda c: c.status == "creation")
        ccar_awaiting_qao = ccar_open.filtered(
            lambda c: c.status in ("checking2", "checking3")
        )
        ccar_awaiting_office = ccar_open.filtered(
            lambda c: c.status in ("office", "office2")
        )
        ccar_in_verification = ccar_open.filtered(lambda c: c.status == "verification")
        ccar_completed_year = CCAR.search_count([
            ("status", "=", "completed"),
            ("date", ">=", _date(today.year, 1, 1).strftime("%Y-%m-%d")),
        ])

        # Current audit period (latest)
        period = Period.search([], order="audit_start_date desc", limit=1)

        audit_offices = 0
        audit_c = audit_nc = audit_ofi = 0
        if period:
            audit_offices = self.env["upmin_iso.audit_info"].search_count(
                [("audit_period", "=", period.id)]
            )
            findings = Finding.search([("audit_info.audit_period", "=", period.id)])
            audit_c = sum(1 for f in findings if f.rating == "c")
            audit_nc = FinalNC.search_count([("audit_period_id", "=", period.id)])
            audit_ofi = sum(1 for f in findings if f.rating == "ofi")

        # IAs not assigned to any office in the latest period
        ia_not_assigned = 0
        if period:
            assigned_ia_ids = set(
                self.env["upmin_iso.audit_info"]
                .search([("audit_period", "=", period.id)])
                .mapped("internal_auditors")
                .ids
            )
            all_ia_ids = set(IA.search([]).ids)
            ia_not_assigned = len(all_ia_ids - assigned_ia_ids)

        # Yearly stats (all periods starting in the current calendar year)
        year_start = _date(today.year, 1, 1).strftime("%Y-%m-%d")
        year_periods = Period.search([("audit_start_date", ">=", year_start)])
        year_findings = Finding.search([("audit_info.audit_period", "in", year_periods.ids)])
        year_c = sum(1 for f in year_findings if f.rating == "c")
        year_nc = FinalNC.search_count([("audit_period_id", "in", year_periods.ids)])
        year_ofi = sum(1 for f in year_findings if f.rating == "ofi")
        year_offices = self.env["upmin_iso.audit_info"].search_count(
            [("audit_period", "in", year_periods.ids)]
        ) if year_periods else 0

        # NCs without a CCAR
        all_nc = Finding.search([("rating", "=", "nc"), ("is_duplicate", "=", False)])
        linked_nc_ids = set(CCAR.search([]).mapped("related_nc").ids)
        nc_without_ccar = len(all_nc.filtered(lambda f: f.id not in linked_nc_ids))

        # ROR: offices with pending ratings this quarter
        rors = ROR.search([])
        ror_pending_offices = sum(1 for r in rors if r.pending_this_quarter > 0)

        # Significant risks this quarter
        significant_risks = Rating.search_count([
            ("risk_conclusion", "=", "significant"),
            ("review_date", "=", q_end),
        ])

        # RORs with at least one issue that has skipped quarters
        ror_with_skipped = 0
        issues = Line.search([("ror_id", "!=", False)])
        skipped_ror_ids = set()
        for issue in issues:
            create_dt = issue.create_date.date() if issue.create_date else today
            entry_dates = set(issue.ratings.mapped("review_date"))
            for year in range(create_dt.year, today.year + 1):
                for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
                    q = _date(year, month, day)
                    if q >= create_dt and q < today and q not in entry_dates:
                        skipped_ror_ids.add(issue.ror_id.id)
                        break
        ror_with_skipped = len(skipped_ror_ids)

        # RORs with at least one incomplete past rating (progress < 100, review_date < current quarter)
        incomplete_past_ror_ids = set(
            Rating.search([
                ("review_date", "<", q_end),
                ("progress", "<", 100),
                ("issue.ror_id", "!=", False),
            ]).mapped("issue.ror_id.id")
        )
        ror_with_incomplete_past = len(incomplete_past_ror_ids)

        # Directory counts
        ia_trained_certified = IA.search_count([("trained", "=", True), ("certified", "=", True)])
        ia_trained_not_certified = IA.search_count([("trained", "=", True), ("certified", "=", False)])
        dc_trained = DC.search_count([("trained", "=", True)])

        for rec in self:
            rec.ccar_open = len(ccar_open)
            rec.ccar_creation = len(ccar_creation)
            rec.ccar_awaiting_qao = len(ccar_awaiting_qao)
            rec.ccar_awaiting_office = len(ccar_awaiting_office)
            rec.ccar_in_verification = len(ccar_in_verification)
            rec.ccar_completed_year = ccar_completed_year
            rec.current_period = period.id if period else False
            rec.has_period = bool(period)
            rec.audit_offices = audit_offices
            rec.audit_c = audit_c
            rec.audit_nc = audit_nc
            rec.audit_ofi = audit_ofi
            rec.nc_without_ccar = nc_without_ccar
            rec.ia_not_assigned = ia_not_assigned
            rec.year_c = year_c
            rec.year_nc = year_nc
            rec.year_ofi = year_ofi
            rec.year_offices = year_offices
            rec.ror_pending_offices = ror_pending_offices
            rec.significant_risks = significant_risks
            rec.ror_with_skipped = ror_with_skipped
            rec.ror_with_incomplete_past = ror_with_incomplete_past
            rec.ia_trained_certified = ia_trained_certified
            rec.ia_trained_not_certified = ia_trained_not_certified
            rec.dc_trained = dc_trained

    # ── Action helpers ─────────────────────────────────────────────────────

    @api.model
    def action_open(self):
        rec = self.create({})
        return {
            "type": "ir.actions.act_window",
            "name": "ISO Dashboard",
            "res_model": "upmin_iso.iso_dashboard",
            "res_id": rec.id,
            "view_mode": "form",
            "target": "main",
        }

    def action_ccar_creation(self):
        return {
            "type": "ir.actions.act_window",
            "name": "CCARs Pending Submission",
            "res_model": "upmin_iso.ccar",
            "view_mode": "tree,form",
            "domain": [("status", "=", "creation")],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ccar_open(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Open CCARs",
            "res_model": "upmin_iso.ccar",
            "view_mode": "tree,form",
            "domain": [("status", "!=", "completed")],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ccar_awaiting_qao(self):
        return {
            "type": "ir.actions.act_window",
            "name": "CCARs Awaiting QAO",
            "res_model": "upmin_iso.ccar",
            "view_mode": "tree,form",
            "domain": [("status", "in", ["checking2", "checking3"])],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ccar_awaiting_office(self):
        return {
            "type": "ir.actions.act_window",
            "name": "CCARs Awaiting Office",
            "res_model": "upmin_iso.ccar",
            "view_mode": "tree,form",
            "domain": [("status", "in", ["office", "office2"])],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ccar_in_verification(self):
        return {
            "type": "ir.actions.act_window",
            "name": "CCARs In Verification",
            "res_model": "upmin_iso.ccar",
            "view_mode": "tree,form",
            "domain": [("status", "=", "verification")],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ccar_completed_year(self):
        today = _date.today()
        return {
            "type": "ir.actions.act_window",
            "name": "Completed CCARs This Year",
            "res_model": "upmin_iso.ccar",
            "view_mode": "tree,form",
            "domain": [
                ("status", "=", "completed"),
                ("date", ">=", _date(today.year, 1, 1).strftime("%Y-%m-%d")),
            ],
            "context": {"upmin_iso_dept_short": True},
        }

    def _dashboard_finding_views(self):
        tree_id = self.env.ref("upmin_iso.audit_finding_view_tree_dashboard").id
        form_id = self.env.ref("upmin_iso.audit_finding_view_form_dashboard").id
        return [(tree_id, "tree"), (form_id, "form")]

    def _final_nc_tree_view(self):
        tree_id = self.env.ref("upmin_iso.audit_period_final_nc_view_tree").id
        return [(tree_id, "tree")]

    def action_audit_c(self):
        period = self.env["upmin_iso.audit_period"].search(
            [], order="audit_start_date desc", limit=1
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Conformities This Period",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "views": self._dashboard_finding_views(),
            "domain": [("audit_info.audit_period", "=", period.id), ("rating", "=", "c")] if period else [("id", "=", False)],
            "context": {"upmin_iso_dept_short": True, "search_default_group_by_office": 1},
        }

    def action_audit_nc(self):
        period = self.env["upmin_iso.audit_period"].search(
            [], order="audit_start_date desc", limit=1
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Nonconformities This Period",
            "res_model": "upmin_iso.audit_period_final_nc",
            "view_mode": "tree",
            "views": self._final_nc_tree_view(),
            "domain": [("audit_period_id", "=", period.id)] if period else [("id", "=", False)],
        }

    def action_audit_ofi(self):
        period = self.env["upmin_iso.audit_period"].search(
            [], order="audit_start_date desc", limit=1
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Opportunities This Period",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "views": self._dashboard_finding_views(),
            "domain": [("audit_info.audit_period", "=", period.id), ("rating", "=", "ofi")] if period else [("id", "=", False)],
            "context": {"upmin_iso_dept_short": True, "search_default_group_by_office": 1},
        }

    def action_audit_offices(self):
        period = self.env["upmin_iso.audit_period"].search(
            [], order="audit_start_date desc", limit=1
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Offices Audited This Period",
            "res_model": "upmin_iso.audit_info",
            "view_mode": "tree,form",
            "domain": [("audit_period", "=", period.id)] if period else [("id", "=", False)],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ia_not_assigned(self):
        period = self.env["upmin_iso.audit_period"].search(
            [], order="audit_start_date desc", limit=1
        )
        if period:
            assigned_ids = (
                self.env["upmin_iso.audit_info"]
                .search([("audit_period", "=", period.id)])
                .mapped("internal_auditors")
                .ids
            )
        else:
            assigned_ids = []
        all_ids = self.env["upmin_iso.internal_auditor"].search([]).ids
        unassigned_ids = [i for i in all_ids if i not in assigned_ids]
        return {
            "type": "ir.actions.act_window",
            "name": "IAs Not Assigned This Period",
            "res_model": "upmin_iso.internal_auditor",
            "view_mode": "tree,form",
            "domain": [("id", "in", unassigned_ids)],
            "context": {"upmin_iso_dept_short": True},
        }

    def _year_period_ids(self):
        today = _date.today()
        year_start = _date(today.year, 1, 1).strftime("%Y-%m-%d")
        return self.env["upmin_iso.audit_period"].search(
            [("audit_start_date", ">=", year_start)]
        ).ids

    def action_year_c(self):
        return {
            "type": "ir.actions.act_window",
            "name": f"Conformities {_date.today().year}",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "views": self._dashboard_finding_views(),
            "domain": [("audit_info.audit_period", "in", self._year_period_ids()), ("rating", "=", "c")],
            "context": {"upmin_iso_dept_short": True, "search_default_group_by_office": 1},
        }

    def action_year_nc(self):
        return {
            "type": "ir.actions.act_window",
            "name": f"Nonconformities {_date.today().year}",
            "res_model": "upmin_iso.audit_period_final_nc",
            "view_mode": "tree",
            "views": self._final_nc_tree_view(),
            "domain": [("audit_period_id", "in", self._year_period_ids())],
        }

    def action_year_ofi(self):
        return {
            "type": "ir.actions.act_window",
            "name": f"Opportunities {_date.today().year}",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "views": self._dashboard_finding_views(),
            "domain": [("audit_info.audit_period", "in", self._year_period_ids()), ("rating", "=", "ofi")],
            "context": {"upmin_iso_dept_short": True, "search_default_group_by_office": 1},
        }

    def action_year_offices(self):
        return {
            "type": "ir.actions.act_window",
            "name": f"Offices Audited {_date.today().year}",
            "res_model": "upmin_iso.audit_info",
            "view_mode": "tree,form",
            "domain": [("audit_period", "in", self._year_period_ids())],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_nc_without_ccar(self):
        all_nc = self.env["upmin_iso.audit_finding"].search([("rating", "=", "nc"), ("is_duplicate", "=", False)])
        linked_nc_ids = set(self.env["upmin_iso.ccar"].search([]).mapped("related_nc").ids)
        unlinked_ids = all_nc.filtered(lambda f: f.id not in linked_nc_ids).ids
        return {
            "type": "ir.actions.act_window",
            "name": "NCs Without CCAR",
            "res_model": "upmin_iso.audit_finding",
            "view_mode": "tree,form",
            "domain": [("id", "in", unlinked_ids)],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ror_pending(self):
        rors = self.env["upmin_iso.ror"].search([])
        pending_ids = [r.id for r in rors if r.pending_this_quarter > 0]
        return {
            "type": "ir.actions.act_window",
            "name": "Offices With Pending Ratings",
            "res_model": "upmin_iso.ror",
            "view_mode": "tree,form",
            "domain": [("id", "in", pending_ids)],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_significant_risks(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Significant Risks This Quarter",
            "res_model": "upmin_iso.ror_rating",
            "view_mode": "tree,form",
            "domain": [
                ("risk_conclusion", "=", "significant"),
                ("review_date", "=", _current_quarter_end()),
            ],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ia_trained_certified(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Trained & Certified Internal Auditors",
            "res_model": "upmin_iso.internal_auditor",
            "view_mode": "tree,form",
            "domain": [("trained", "=", True), ("certified", "=", True)],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ia_trained_not_certified(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Trained (Not Yet Certified) Internal Auditors",
            "res_model": "upmin_iso.internal_auditor",
            "view_mode": "tree,form",
            "domain": [("trained", "=", True), ("certified", "=", False)],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_dc_trained(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Trained Document Controllers",
            "res_model": "upmin_iso.document_controller",
            "view_mode": "tree,form",
            "domain": [("trained", "=", True)],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ror_skipped(self):
        today = _date.today()
        issues = self.env["upmin_iso.swot_line"].search([("ror_id", "!=", False)])
        skipped_ror_ids = set()
        for issue in issues:
            create_dt = issue.create_date.date() if issue.create_date else today
            entry_dates = set(issue.ratings.mapped("review_date"))
            for year in range(create_dt.year, today.year + 1):
                for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
                    q = _date(year, month, day)
                    if q >= create_dt and q < today and q not in entry_dates:
                        skipped_ror_ids.add(issue.ror_id.id)
                        break
        return {
            "type": "ir.actions.act_window",
            "name": "RORs With Skipped Quarters",
            "res_model": "upmin_iso.ror",
            "view_mode": "tree,form",
            "domain": [("id", "in", list(skipped_ror_ids))],
            "context": {"upmin_iso_dept_short": True},
        }

    def action_ror_incomplete_past(self):
        q_end = _current_quarter_end()
        ror_ids = set(
            self.env["upmin_iso.ror_rating"].search([
                ("review_date", "<", q_end),
                ("progress", "<", 100),
                ("issue.ror_id", "!=", False),
            ]).mapped("issue.ror_id.id")
        )
        return {
            "type": "ir.actions.act_window",
            "name": "RORs With Incomplete Past Ratings",
            "res_model": "upmin_iso.ror",
            "view_mode": "tree,form",
            "domain": [("id", "in", list(ror_ids))],
            "context": {"upmin_iso_dept_short": True},
        }
