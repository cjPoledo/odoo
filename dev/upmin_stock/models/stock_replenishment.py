from odoo import models, fields


class StockReplenishment(models.Model):
    _name = "upmin_stock.replenishment"
    _description = "Stock Replenishment Log"

    stock_id = fields.Many2one(
        "upmin_stock.stock", string="Stock", required=True, ondelete="cascade"
    )
    procurement_import_id = fields.Many2one(
        "upmin_stock.procurement", string="Procurement", ondelete="cascade"
    )
    quantity = fields.Integer(string="Replenished Quantity", required=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    notes = fields.Text(string="Notes")
