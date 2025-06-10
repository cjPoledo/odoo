from odoo import models, fields

class RSMI(models.Model):
    _name = "upmin_stock.rsmi"
    _description = "Report of Supplies and Materials Issued"
    _rec_name = "serial_no"

    serial_no = fields.Char(string="Serial No.", required=True)
    entity_name = fields.Char(string="Entity Name", required=True)
    fund_cluster = fields.Char(string="Fund Cluster", required=True)
    date = fields.Date(string="Date", required=True)
    issuances = fields.Many2many("upmin_stock.issuance", string="Issuances")