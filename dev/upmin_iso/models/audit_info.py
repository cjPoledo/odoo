from odoo import models, fields, api


class AuditInfo(models.Model):
    _name = "upmin_iso.audit_info"
    _description = "ISO Internal Audit Information"
    _rec_name = "audit_start_datetime"
    _order = "audit_start_datetime"

    office_to_audit = fields.Many2one(
        comodel_name="upmin_iso.office", string="Office to Audit", required=True
    )
    audit_period = fields.Many2one(
        comodel_name="upmin_iso.audit_period", string="Audit Period", required=True
    )
    internal_auditors = fields.Many2many(
        comodel_name="res.partner",
        string="Internal Auditors",
        domain=lambda self: self._get_internal_auditor_domain(),
    )
    audit_start_datetime = fields.Datetime(string="Audit Start Date", required=True)
    audit_end_datetime = fields.Datetime(string="Audit End Date", required=True)

    @api.model
    def _get_internal_auditor_domain(self):
        group = self.env.ref("upmin_iso.group_iso_internal_auditor")
        users = self.env["res.users"].search([("groups_id", "in", group.id)])
        partners = users.mapped("partner_id")
        return [("id", "in", partners.ids)]
