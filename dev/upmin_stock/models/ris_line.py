from odoo import models, fields


class RISLine(models.Model):
    _name = "upmin_stock.ris_line"
    _description = "RIS Line"

    ris_id = fields.Many2one(
        "upmin_stock.ris", string="RIS", required=True, ondelete="cascade"
    )
    stock_id = fields.Many2one("upmin_stock.stock", string="Stock", required=True)
    quantity = fields.Integer(string="Quantity", required=True)
