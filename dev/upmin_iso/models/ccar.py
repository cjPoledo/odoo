from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CCAR(models.Model):
    _name = "upmin_iso.ccar"
    _description = "Correction and Corrective Action Report"
    _rec_name = "ccar_no"
    _order = "ccar_no"
    _inherit = ["mail.thread", "mail.activity.mixin"]

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
            ("checking1", "QAO Checking (1)"),
            ("office", "Office (1)"),
            ("checking2", "QAO Checking (2)"),
            ("verification", "IA Verification"),
            ("checking3", "QAO Checking (3)"),
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
    updated_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Updated By",
        domain="[('department_id', '=', office)]",
    )
    updated_date = fields.Date(string="Updated Date")

    # changes to the qms
    changes_to_qms = fields.Text(
        string="Changes to the Quality Management System If Necessary (policy, procedures, job descriptions, etc.)"
    )
    changes_by = fields.Many2one(
        comodel_name="hr.employee",
        string="Changes Made Completed By",
        domain="[('department_id', '=', office)]",
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

    def _validate_next_step(self):
        if self.status == "creation":
            missing = []
            if not self.responsible_person:
                missing.append("Responsible Person")
            if not self.date_received:
                missing.append("Date Received")
            if missing:
                raise ValidationError(
                    "Please fill in the following before submitting:\n• "
                    + "\n• ".join(missing)
                )

        elif self.status == "office":
            missing = []
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

    def next_step(self):
        flow = [
            "creation",
            "checking1",
            "office",
            "checking2",
            "verification",
            "checking3",
            "office2",
            "completed",
        ]

        for record in self:
            record._validate_next_step()
            if record.status in flow:
                idx = flow.index(record.status)
                if idx < len(flow) - 1:
                    record.status = flow[idx + 1]

    def previous_step(self):
        flow = [
            "creation",
            "checking1",
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

