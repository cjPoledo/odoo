from odoo import api, models, fields
from odoo.exceptions import UserError


class AuditFindingMergeWizard(models.TransientModel):
    _name = "upmin_iso.audit_finding_merge_wizard"
    _description = "Merge Audit Findings"

    audit_info_id = fields.Many2one(
        comodel_name="upmin_iso.audit_info",
        string="Audit Schedule",
        required=True,
        readonly=True,
    )
    finding_ids = fields.Many2many(
        comodel_name="upmin_iso.audit_finding",
        relation="upmin_iso_finding_merge_wizard_rel",
        string="Findings to Merge",
    )
    target_id = fields.Many2one(
        comodel_name="upmin_iso.audit_finding",
        string="Keep this finding",
        help="This finding's clause, auditor, and rating are preserved. The others are deleted.",
        required=True,
    )
    merged_clause_id = fields.Many2one(
        comodel_name="upmin_iso.iso_clause",
        string="Primary Clause",
        readonly=True,
    )
    merged_supporting_clause_ids = fields.Many2many(
        comodel_name="upmin_iso.iso_clause",
        relation="upmin_iso_merge_wiz_sc_rel",
        string="Supporting Clauses",
        readonly=True,
    )
    merged_question = fields.Text(string="Merged Question")
    merged_evidence = fields.Text(string="Merged Scenario/Evidence")
    merged_statement = fields.Text(string="Merged Statement")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        audit_info_id = self.env.context.get("default_audit_info_id")
        if audit_info_id and "audit_info_id" in fields_list:
            res["audit_info_id"] = audit_info_id
        return res

    @api.onchange("finding_ids")
    def _onchange_finding_ids(self):
        findings = self.finding_ids
        if self.target_id not in findings:
            self.target_id = findings[:1] or False
        self._refresh_clause_preview()
        self.merged_question = self._join_field(findings, "question")
        self.merged_evidence = self._join_field(findings, "evidence")
        self.merged_statement = self._join_field(findings, "statement")

    @api.onchange("target_id")
    def _onchange_target_id(self):
        self._refresh_clause_preview()

    def _refresh_clause_preview(self):
        target = self.target_id
        self.merged_clause_id = target.clause if target else False
        self.merged_supporting_clause_ids = (
            self._compute_merged_supporting(self.finding_ids, target)
            if target else self.env["upmin_iso.iso_clause"]
        )

    @staticmethod
    def _compute_merged_supporting(findings, target):
        all_supporting = target.supporting_clause_ids
        for f in findings - target:
            all_supporting |= f.supporting_clause_ids
            if f.clause:
                all_supporting |= f.clause
        return all_supporting - target.clause

    @staticmethod
    def _join_field(findings, fname):
        seen = []
        for f in findings:
            val = getattr(f, fname) or ""
            if val and val not in seen:
                seen.append(val)
        return "\n\n---\n\n".join(seen) or False

    def action_merge(self):
        findings = self.finding_ids
        target = self.target_id

        if len(findings) < 2:
            raise UserError("Select at least two findings to merge.")
        if target not in findings:
            raise UserError("Target finding must be one of the selected findings.")

        if self.audit_info_id.is_finalized:
            raise UserError("Cannot merge findings in a finalized audit.")

        all_supporting = self._compute_merged_supporting(findings, target)

        target.write({
            "question": self.merged_question,
            "evidence": self.merged_evidence,
            "statement": self.merged_statement,
            "supporting_clause_ids": [(6, 0, all_supporting.ids)],
        })
        (findings - target).unlink()

        return {"type": "ir.actions.act_window_close"}
