from odoo import models, fields


class RIS(models.Model):
    _name = "upmin_stock.ris"
    _description = "Requisition and Issue Slip"

    ris_no = fields.Char(string="RIS No.")
    entity_name = fields.Char(string="Entity Name", required=True)
    fund_cluster = fields.Char(string="Fund Cluster", required=True)
    division = fields.Char(string="Division", required=True)
    rc_code = fields.Char(string="Responsibility Center Code", required=True)
    office = fields.Char(string="Office", required=True)
    line_ids = fields.One2many("upmin_stock.ris_line", "ris_id", string="Stocks")
    requested_by = fields.Char(string="Requested By", required=True)
    approved_by = fields.Char(string="Approved By", required=True)
    issued_by = fields.Char(string="Issued By")
    received_by = fields.Char(string="Received By")
