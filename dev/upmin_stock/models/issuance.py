from odoo import models, fields


class Issuance(models.Model):
    _name = "upmin_stock.issuance"
    _description = "Issuance"

    seq_no = fields.Char(string="Sequence Number", required=True)
    date_issued = fields.Date(string="Date Issued", required=True)
    requested_by = fields.Many2one(
        "res.partner", string="Requested By", required=True
    )  # Assuming 'People' is linked to 'res.partner'
    ris_no = fields.Char(string="RIS Number", required=True)
    # replace with the office model
    # rc_code = fields.Many2one(
    #     "some.model", string="RC Code", required=True
    # )
    rc_code = fields.Char(string="RC Code", required=True)
    remarks = fields.Text(string="Remarks")
    stock_no = fields.Many2one(
        "upmin_stock.stock", string="Stock Number", required=True
    )
    quantity_requested = fields.Float(string="Quantity Requested", required=True)
    quantity_issued = fields.Float(string="Quantity Issued", required=True)
