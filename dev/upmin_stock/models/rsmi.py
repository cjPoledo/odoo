from odoo import models, fields, api


class RSMI(models.Model):
    _name = "upmin_stock.rsmi"
    _description = "Report of Supplies and Materials Issued"
    _rec_name = "serial_no"

    serial_no = fields.Char(string="Serial No.", required=True)
    entity_name = fields.Char(
        string="Entity Name",
        required=True,
        default="University of the Philippines Mindanao",
    )
    fund_cluster = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", required=True
    )
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    issuances = fields.Many2many("upmin_stock.issuance", string="Issuances")
    supply_custodian = fields.Many2one(
        "res.partner",
        string="Supply and/or Property Custodian",
        required=True,
        default=lambda self: self.env.user.partner_id.id,
    )
    accounting_staff = fields.Char(string="Designated Accounting Staff", required=True)

    @api.onchange("fund_cluster")
    def _onchange_fund_cluster(self):
        self.issuances = False
        return {
            "domain": {"issuances": [("fund_cluster", "=", self.fund_cluster.name)]}
        }
