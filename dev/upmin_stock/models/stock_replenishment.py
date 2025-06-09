from odoo import models, fields


class StockReplenishment(models.Model):
    _name = "upmin_stock.replenishment"
    _description = "Stock Replenishment Log"

    stock_id = fields.Many2one(
        "upmin_stock.stock", string="Stock", required=True, ondelete="cascade"
    )
    quantity = fields.Integer(string="Replenished Quantity", required=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    notes = fields.Text(string="Notes")

    def _create(self, vals):
        record = super()._create(vals)

        # Automatic initial_balance update
        if record.stock_id and record.quantity:
            record.stock_id.initial_balance += record.quantity

        return record
