from odoo import models, fields


class PPMPBalance(models.Model):
    _name = "upmin_stock.ppmp_balance"
    _description = "PPMP Balance"
    _rec_name = "ppmp"

    ppmp = fields.Many2one("upmin_stock.ppmp", string="PPMP", required=True)
    stock_id = fields.Many2one("upmin_stock.stock", string="Stock", required=True)
    balance = fields.Integer(string="Balance", default=0)
