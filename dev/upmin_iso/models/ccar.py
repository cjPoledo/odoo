from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class CCAR(models.Model):
    _name = "upmin_iso.ccar"
    _description = "Correction and Corrective Action Report"
    _rec_name = "ccar_no"
    _order = "ccar_no"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _mail_post_access = "read"

    ccar_no = fields.Char(
        string="CCAR No.",
        required=True,
        readonly=True,
    )
    audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period",
        string="Audit Period",
        required=True,
        readonly=True,
    )
    date = fields.Date(string="Date", required=True, readonly=True)
    related_nc = fields.Many2one(
        comodel_name="upmin_iso.audit_finding",
        string="Related Nonconformity",
        domain=[("rating", "=", "nc"), ("is_duplicate", "=", False)],
        required=True,
    )
    status = fields.Selection(
        selection=[
            ("creation", "CCAR Creation"),
            ("office", "Office (1)"),
            ("checking2", "QAO Checking (1)"),
            ("verification", "IA Verification"),
            ("checking3", "QAO Checking (2)"),
            ("office2", "Office (2)"),
            ("completed", "Completed"),
        ],
        string="Status",
        default="creation",
        tracking=True,
    )

    # Nature
    audit_nature = fields.Selection(
        selection=[
            ("internal", "Internal Audit"),
            ("external", "External Audit"),
        ],
        string="Audit Nature",
        default="internal",
    )
    conformity_nature = fields.Selection(
        selection=[
            ("nc", "Nonconformity (NC)"),
            ("observation", "Observation/Potential NC"),
            ("unmet", "Unmet Target/Activity"),
            ("nonconforming", "Nonconforming Product/Services"),
        ],
        string="Conformity Nature",
        default="nc",
    )
    complaint_nature_a = fields.Selection(
        selection=[
            ("external", "External Complaint"),
            ("internal", "Internal Complaint"),
        ],
        string="Complaint Type",
    )
    internal_complaint_dept = fields.Many2one(
        comodel_name="hr.department", string="Internal Department"
    )
    complaint_nature_b = fields.Selection(
        selection=[
            ("incidents", "Incidents"),
            ("customer", "Customer Complaint"),
        ],
        string="Incident/Complaint",
    )
    customer_complaint_customer = fields.Char(string="Customer Name")
    complaint_nature_c = fields.Selection(
        selection=[
            ("laws", "Laws/Regulations"),
            ("supplier", "Supplier Nonconformity"),
        ],
        string="Regulatory/Supplier",
    )
    supplier_nonconformity_supplier = fields.Char(string="Supplier Name")

    # Details

    clause = fields.Many2one(
        comodel_name="upmin_iso.iso_clause",
        string="Clause/Source of Report",
        related="related_nc.clause",
        readonly=True,
    )
    supporting_clause_ids = fields.Many2many(
        comodel_name="upmin_iso.iso_clause",
        string="Supporting Clauses",
        related="related_nc.supporting_clause_ids",
        readonly=True,
    )
    details_scenario = fields.Text(
        string="Details (Scenario/Evidence)",
        related="related_nc.evidence",
        readonly=True,
    )
    details_statement = fields.Text(
        string="Details (Statement)",
        related="related_nc.statement",
        readonly=True,
    )
    auditors = fields.Many2many(
        comodel_name="upmin_iso.internal_auditor",
        string="Auditors",
        related="related_nc.audit_info.internal_auditors",
        readonly=True,
    )
    audit_date = fields.Date(
        string="Audit Date", related="related_nc.audit_info.audit_date", readonly=True
    )
    responsible_person = fields.Many2one(
        comodel_name="hr.employee",
        string="Responsible Person",
    )
    date_received = fields.Date(string="Date Received")
    office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        readonly=True,
        related="related_nc.audit_info.office_to_audit",
        store=True,
    )
    bypass_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="upmin_iso_ccar_bypass_user_rel",
        column1="ccar_id",
        column2="user_id",
        string="Additional Viewers",
        domain=lambda self: [("groups_id", "in", [self.env.ref("upmin_iso.group_iso_doc_controller").id])],
    )
    can_submit = fields.Boolean(compute="_compute_can_submit", store=False)

    # Immediate Action/Correction Taken
    description = fields.Text(string="Description")
    results = fields.Text(string="Results")
    responsibility = fields.Char(string="Responsibility")
    completed_date = fields.Date(string="Completed Date")

    # Investigation of Root Cause
    tree_diagram_link = fields.Char(string="Tree Diagram")
    investigated_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Investigated By",
    )
    date_investigated = fields.Date(string="Date Investigated")
    investigator_dept = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        readonly=True,
        related="related_nc.audit_info.office_to_audit",
    )

    # agreed corrective action plan
    corrective_action_plan = fields.One2many(
        comodel_name="upmin_iso.ccar_corrective_action",
        inverse_name="ccar",
        string="Agreed Corrective Action Plan",
    )
    proposed_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Proposed By",
    )
    target_date = fields.Date(string="Implementation/Target Date")
    approved_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Approved By",
    )

    # impact analysis
    affected_areas = fields.Text(
        string="What other areas may benefit or be affected by the implemented actions?"
    )
    initiated_date = fields.Date(string="Initiated Date")
    effective_date = fields.Date(string="Effective Date")

    # verification of Effectiveness
    correction_effectiveness = fields.One2many(
        comodel_name="upmin_iso.ccar_correction_effectiveness",
        inverse_name="ccar",
        string="Correction",
    )
    corrective_action_effectiveness = fields.One2many(
        comodel_name="upmin_iso.ccar_corrective_action_effectiveness",
        inverse_name="ccar",
        string="Corrective Action",
    )

    # details on affected related risk and opportunities
    affected_related_risks_opportunities = fields.Text(
        string="Details on affected related risks and opportunities (if necessary)"
    )
    updated_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Updated By",
    )
    updated_date = fields.Date(string="Updated Date")

    # changes to the qms
    changes_to_qms = fields.Text(
        string="Changes to the Quality Management System If Necessary (policy, procedures, job descriptions, etc.)"
    )
    changes_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Changes Made Completed By",
    )
    changes_date = fields.Date(string="Changes Date")

    _sql_constraints = [
        (
            "ccar_no_unique",
            "unique(ccar_no)",
            "CCAR No. must be unique.",
        ),
        (
            "related_nc_unique",
            "unique(related_nc)",
            "This Nonconformity is already linked to another CCAR.",
        ),
    ]

    @api.onchange("related_nc")
    def _onchange_related_nc_responsible(self):
        if not self.related_nc or not self.related_nc.audit_info:
            return
        office = self.related_nc.audit_info.office_to_audit
        if not office:
            return
        unit_head = self.env["upmin_iso.unit_head"].sudo().search(
            [("office", "in", [office.id])], limit=1
        )
        if unit_head:
            self.responsible_person = unit_head.name

    def _validate_next_step(self):
        if self.status == "creation":
            missing = []
            if not self.responsible_person:
                missing.append("Responsible Person")
            if missing:
                raise ValidationError(
                    "Please fill in the following before submitting:\n• "
                    + "\n• ".join(missing)
                )

        elif self.status == "office":
            missing = []
            if not self.date_received:
                missing.append("[1] Date Received")
            # Page 2
            if not self.description:
                missing.append("[2] Description")
            if not self.results:
                missing.append("[2] Results")
            if not self.responsibility:
                missing.append("[2] Responsibility")
            if not self.completed_date:
                missing.append("[2] Completed Date")
            # Page 3
            if not self.tree_diagram_link:
                missing.append("[3] Tree Diagram Link")
            if not self.investigated_by:
                missing.append("[3] Investigated By")
            if not self.date_investigated:
                missing.append("[3] Date Investigated")
            # Page 4
            if not self.corrective_action_plan:
                missing.append("[4] At least one Corrective Action entry")
            if not self.proposed_by:
                missing.append("[4] Proposed By")
            if not self.target_date:
                missing.append("[4] Implementation/Target Date")
            if not self.approved_by:
                missing.append("[4] Approved By")
            if missing:
                raise ValidationError(
                    "Please fill in the following required fields before submitting:\n• "
                    + "\n• ".join(missing)
                    + "\n\nNote: Page 5 (Impact Analysis) is if applicable and not required."
                )

        elif self.status == "verification":
            missing = []
            if not self.correction_effectiveness:
                missing.append("Correction Effectiveness (at least one entry)")
            if not self.corrective_action_effectiveness:
                missing.append("Corrective Action Effectiveness (at least one entry)")
            if missing:
                raise ValidationError(
                    "Please fill in the following before submitting:\n• "
                    + "\n• ".join(missing)
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._subscribe_default_followers()
        return records

    def _subscribe_default_followers(self):
        partner_ids = set()

        # Resolve office and auditors directly through the relation chain
        # (avoids relying on stored related fields that may not be flushed yet)
        audit_info = self.related_nc.audit_info if self.related_nc else False
        office = audit_info.office_to_audit if audit_info else False
        auditors = audit_info.internal_auditors if audit_info else []

        # Document controllers and unit heads for this office (direct or college-level)
        if office:
            all_dcs = self.env["upmin_iso.document_controller"].sudo().search([])
            for dc in all_dcs.filtered(
                lambda dc: office in dc.office or office in dc.name.iso_ancestor_ids
            ):
                if dc.name.user_id and dc.name.user_id.partner_id:
                    partner_ids.add(dc.name.user_id.partner_id.id)

            all_uhs = self.env["upmin_iso.unit_head"].sudo().search([])
            for uh in all_uhs.filtered(
                lambda uh: office in uh.office or office in uh.name.iso_ancestor_ids
            ):
                if uh.name.user_id and uh.name.user_id.partner_id:
                    partner_ids.add(uh.name.user_id.partner_id.id)

        # All ISO Staff
        staff_group = self.env.ref("upmin_iso.group_iso_staff")
        for user in staff_group.users:
            if user.partner_id:
                partner_ids.add(user.partner_id.id)

        # Assigned internal auditors
        for auditor in auditors:
            if auditor.name.user_id and auditor.name.user_id.partner_id:
                partner_ids.add(auditor.name.user_id.partner_id.id)

        if partner_ids:
            self.message_subscribe(partner_ids=list(partner_ids))

    def _compute_can_submit(self):
        user = self.env.user
        is_staff = user.has_group("upmin_iso.group_iso_staff")
        for record in self:
            if record.status in {"checking2", "checking3"}:
                record.can_submit = is_staff
            elif record.status in record._DC_STATUSES:
                record.can_submit = is_staff or record._is_dc_of_record(user)
            elif record.status in record._IA_STATUSES:
                record.can_submit = is_staff or record._is_ia_of_record(user)
            else:
                record.can_submit = False

    def next_step(self):
        flow = [
            "creation",
            "office",
            "checking2",
            "verification",
            "checking3",
            "office2",
            "completed",
        ]

        user = self.env.user
        is_staff = user.has_group("upmin_iso.group_iso_staff")

        staff_statuses = {"checking2", "checking3"}

        for record in self:
            if record.status in staff_statuses and not is_staff:
                raise ValidationError("Only ISO Staff can submit at this stage.")
            if record.status in record._DC_STATUSES and not (is_staff or record._is_dc_of_record(user)):
                raise ValidationError("Only the office DC or ISO Staff can submit at this stage.")
            if record.status in record._IA_STATUSES and not (is_staff or record._is_ia_of_record(user)):
                raise ValidationError("Only an Internal Auditor or ISO Staff can submit at this stage.")
            record._validate_next_step()
            if record.status in flow:
                idx = flow.index(record.status)
                if idx < len(flow) - 1:
                    record.status = flow[idx + 1]

    def previous_step(self):
        if not self.env.user.has_group("upmin_iso.group_iso_staff"):
            raise ValidationError("Only ISO Staff can return a CCAR to a previous step.")

        flow = [
            "creation",
            "office",
            "checking2",
            "verification",
            "checking3",
            "office2",
            "completed",
        ]

        for record in self:
            if record.status in flow:
                idx = flow.index(record.status)
                if idx > 0:
                    record.status = flow[idx - 1]

    # ── Status-based write gating ─────────────────────────────────────────────
    # Record rules only scope which CCARs a Doc Controller / Internal Auditor
    # can see and (at the ORM access-check level) write. Which *statuses*
    # they're allowed to edit at is enforced here instead of via status-based
    # rule domains, so that write access on the record is never conditionally
    # revoked — chatter (post, log note, schedule activity, follow) requires
    # write access on the record itself and must keep working regardless of
    # status.
    _DC_STATUSES = {"office", "office2"}
    _IA_STATUSES = {"creation", "verification"}
    # Fields chatter/mail internals may touch directly via write(); never
    # part of a user-facing form submission, so they're exempt from the
    # status check.
    _CHATTER_FIELDS = {"message_follower_ids", "message_ids", "activity_ids"}

    def _is_dc_of_record(self, user):
        """Whether user is a Document Controller of THIS record's office
        specifically, not merely a member of the DC group somewhere else.
        A user granted bypass access (Additional Viewers) is treated as the
        DC of record too, mirroring the row-visibility ir.rule domains."""
        self.ensure_one()
        if user in self.sudo().bypass_user_ids:
            return True
        employee = user.sudo().employee_id
        office = self.sudo().office
        return bool(
            office
            and (
                office in employee.iso_office_ids
                or office in employee.iso_ancestor_ids
            )
        )

    def _is_ia_of_record(self, user):
        """Whether user is the Internal Auditor assigned to THIS record,
        not merely a member of the IA group generally."""
        self.ensure_one()
        return user in self.sudo().auditors.name.user_id

    def write(self, vals):
        restricted_vals = set(vals) - self._CHATTER_FIELDS
        if restricted_vals and not self.env.su:
            user = self.env.user
            is_staff = user.has_group("upmin_iso.group_iso_staff")
            if not is_staff:
                for record in self:
                    if record._is_dc_of_record(user) and record.status in self._DC_STATUSES:
                        continue
                    if record._is_ia_of_record(user) and record.status in self._IA_STATUSES:
                        continue
                    raise AccessError(
                        "You cannot edit this CCAR at its current status "
                        f"({record.status})."
                    )
        return super().write(vals)

