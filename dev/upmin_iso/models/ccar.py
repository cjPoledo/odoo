from odoo import models, fields


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

    # Nature
    audit_nature = fields.Selection(
        selection=[
            ("internal", "Internal Audit"),
            ("external", "External Audit"),
        ],
        string="Audit Nature",
    )
    conformity_nature = fields.Selection(
        selection=[
            ("nc", "Nonconformity (NC)"),
            ("observation", "Observation/Potential NC"),
            ("unmet", "Unmet Target/Activity"),
            ("nonconforming", "Nonconforming Product/Services"),
        ],
        string="Conformity Nature",
    )
    complaint_nature_a = fields.Selection(
        selection=[
            ("external", "External Complaint"),
            ("internal", "Internal Complaint"),
        ],
        string="Complaint Nature A",
    )
    internal_complaint_dept = fields.Many2one(
        comodel_name="upmin_iso.office", string="Department"
    )
    complaint_nature_b = fields.Selection(
        selection=[
            ("incidents", "Incidents"),
            ("customer", "Customer Complaint"),
        ],
        string="Complaint Nature B",
    )
    customer_complaint_customer = fields.Char(string="Customer Name")
    complaint_nature_c = fields.Selection(
        selection=[
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
        comodel_name="res.partner",
        string="Auditors",
        related="related_nc.audit_info.internal_auditors",
        readonly=True,
    )
    audit_date = fields.Date(
        string="Audit Date", related="related_nc.audit_info.audit_date", readonly=True
    )
    responsible_person = fields.Many2one(
        comodel_name="res.partner", string="Responsible Person"
    )
    date_received = fields.Date(string="Date Received")
    office = fields.Many2one(
        comodel_name="upmin_iso.office",
        string="Office",
        readonly=True,
        related="related_nc.audit_info.office_to_audit",
    )

    # Immediate Action/Correction Taken
    description = fields.Text(string="Description", required=True)
    results = fields.Text(string="Results", required=True)
    responsibility = fields.Char(string="Responsibility", required=True)
    completed_date = fields.Date(string="Completed Date", required=True)

    # Investigation of Root Cause
    tree_diagram_link = fields.Char(string="Tree Diagram")
    investigated_by = fields.Many2one(
        comodel_name="res.partner", string="Investigated By"
    )
    date_investigated = fields.Date(string="Date Investigated")

    # agreed corrective action plan
    corrective_action_plan = fields.One2many(
        comodel_name="upmin_iso.ccar_corrective_action",
        inverse_name="ccar",
        string="Agreed Corrective Action Plan",
    )
    proposed_by = fields.Many2one(comodel_name="res.partner", string="Proposed By")
    target_date = fields.Date(string="Implementation/Target Date")
    approved_by = fields.Many2one(comodel_name="res.partner", string="Approved By")

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
    updated_by = fields.Many2one(comodel_name="res.partner", string="Updated By")
    updated_date = fields.Date(string="Date")

    # changes to the qms
    changes_to_qms = fields.Text(
        string="Changes to the Quality Management System If Necessary (policy, procedures, job descriptions, etc.)"
    )
    changes_by = fields.Many2one(
        comodel_name="res.partner", string="Changes Made Completed By"
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
