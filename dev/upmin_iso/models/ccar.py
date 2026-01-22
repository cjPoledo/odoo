from odoo import models, fields, api


class CCAR(models.Model):
    _name = "upmin_iso.ccar"
    _description = "Correction and Corrective Action Report"
    _rec_name = "ccar_no"
    _order = "ccar_no"

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
        domain=[("rating", "=", "nc")],
        required=True,
    )
    status = fields.Selection(
        selection=[
            ("creation", "CCAR Creation"),
            ("office", "For Office Accomplishment"),
            ("verification", "For IA Verification"),
            ("completed", "Completed"),
        ],
        string="Status",
        default="creation",
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
            ("clear", "[Clear Selection]"),
            ("external", "External Complaint"),
            ("internal", "Internal Complaint"),
        ],
        string="Complaint Nature A",
    )
    internal_complaint_dept = fields.Many2one(
        comodel_name="hr.department", string="Department"
    )
    complaint_nature_b = fields.Selection(
        selection=[
            ("clear", "[Clear Selection]"),
            ("incidents", "Incidents"),
            ("customer", "Customer Complaint"),
        ],
        string="Complaint Nature B",
    )
    customer_complaint_customer = fields.Char(string="Customer Name")
    complaint_nature_c = fields.Selection(
        selection=[
            ("clear", "[Clear Selection]"),
            ("laws", "Laws/Regulations"),
            ("supplier", "Supplier Nonconformity"),
        ],
        string="Complaint Nature C",
    )
    supplier_nonconformity_supplier = fields.Char(string="Supplier Name")

    # Details

    clause = fields.Many2one(
        comodel_name="upmin_iso.iso_clause",
        string="Clause/Source of Report",
        related="related_nc.clause",
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
        domain="[('department_id', '=', office)]",
    )
    date_received = fields.Date(string="Date Received")
    office = fields.Many2one(
        comodel_name="hr.department",
        string="Office",
        readonly=True,
        related="related_nc.audit_info.office_to_audit",
    )

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
        domain="[('department_id', '=', investigator_dept)]",
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
        domain="[('department_id', '=', office)]",
    )
    target_date = fields.Date(string="Implementation/Target Date")
    approved_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Approved By",
        domain="[('department_id', '=', office)]",
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
    updated_by = fields.Many2one(comodel_name="hr.employee", string="Updated By")
    updated_date = fields.Date(string="Date")

    # changes to the qms
    changes_to_qms = fields.Text(
        string="Changes to the Quality Management System If Necessary (policy, procedures, job descriptions, etc.)"
    )
    changes_by = fields.Many2one(
        comodel_name="hr.employee", string="Changes Made Completed By"
    )
    changes_date = fields.Date(string="Date")

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

    def next_step(self):
        for record in self:
            if record.status == "creation":
                record.status = "office"
            elif record.status == "office":
                record.status = "verification"
            elif record.status == "verification":
                record.status = "completed"

    def previous_step(self):
        for record in self:
            if record.status == "completed":
                record.status = "verification"
            elif record.status == "verification":
                record.status = "office"
            elif record.status == "office":
                record.status = "creation"

    @api.onchange("complaint_nature_a")
    def _onchange_complaint_nature_a(self):
        if self.complaint_nature_a == "clear":
            self.complaint_nature_a = False

    @api.onchange("complaint_nature_b")
    def _onchange_complaint_nature_b(self):
        if self.complaint_nature_b == "clear":
            self.complaint_nature_b = False

    @api.onchange("complaint_nature_c")
    def _onchange_complaint_nature_c(self):
        if self.complaint_nature_c == "clear":
            self.complaint_nature_c = False
