from odoo import api, models, fields
from odoo.exceptions import UserError


class InstitutionalFindingWizard(models.TransientModel):
    _name = "upmin_iso.institutional_finding_wizard"
    _description = "Group Findings into an Institutional Finding"

    audit_period_id = fields.Many2one(
        comodel_name="upmin_iso.audit_period",
        string="Audit Period",
        required=True,
        readonly=True,
    )
    institutional_finding_id = fields.Many2one(
        comodel_name="upmin_iso.institutional_finding",
        string="Existing Institutional Finding",
        domain="[('audit_period', '=', audit_period_id)]",
        help="Leave empty to create a new Institutional Finding.",
    )
    finding_ids = fields.Many2many(
        comodel_name="upmin_iso.audit_finding",
        relation="upmin_iso_institutional_finding_wizard_rel",
        string="Findings to Group",
        domain="[('related_audit_period', '=', audit_period_id), "
        "('rating', '=', 'nc'), ('is_duplicate', '=', False), "
        "('institutional_finding_id', '=', False)]",
    )
    clause_id = fields.Many2one(
        comodel_name="upmin_iso.iso_clause",
        string="Clause",
        required=True,
    )
    supporting_clause_ids = fields.Many2many(
        comodel_name="upmin_iso.iso_clause",
        relation="upmin_iso_institutional_finding_wizard_supporting_clause_rel",
        string="Supporting Clauses",
    )
    description = fields.Text(string="Description")

    @api.onchange("institutional_finding_id")
    def _onchange_institutional_finding_id(self):
        if self.institutional_finding_id:
            self.clause_id = self.institutional_finding_id.clause
            self.supporting_clause_ids = self.institutional_finding_id.supporting_clause_ids
            self.description = self.institutional_finding_id.description

    def action_group(self):
        self.ensure_one()
        if len(self.finding_ids) < 2:
            raise UserError(
                "Select at least two findings to group into an institutional finding."
            )
        if not self.clause_id:
            raise UserError("Please select a clause for the institutional finding.")
        if self.audit_period_id.is_finalized:
            raise UserError("Cannot group findings in a finalized audit period.")

        if self.institutional_finding_id:
            institutional_finding = self.institutional_finding_id
            institutional_finding.write({
                "clause": self.clause_id.id,
                "supporting_clause_ids": [(6, 0, self.supporting_clause_ids.ids)],
                "description": self.description,
            })
        else:
            institutional_finding = self.env["upmin_iso.institutional_finding"].create({
                "audit_period": self.audit_period_id.id,
                "clause": self.clause_id.id,
                "supporting_clause_ids": [(6, 0, self.supporting_clause_ids.ids)],
                "description": self.description,
            })

        self.finding_ids.write({"institutional_finding_id": institutional_finding.id})

        return {"type": "ir.actions.act_window_close"}
