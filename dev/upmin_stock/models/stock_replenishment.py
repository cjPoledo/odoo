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
    fund_cluster_id = fields.Many2one(
        "upmin_stock.fund_cluster",
        string="Fund Cluster",
        required=True,
        ondelete="cascade",
    )
    quantity = fields.Integer(string="Replenished Quantity", required=True)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    notes = fields.Text(string="Notes")

    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            rec.stock_id.update_fund_cluster_balance()
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec.stock_id.update_fund_cluster_balance()
        return res

    def unlink(self):
        stocks = self.mapped("stock_id")
        res = super().unlink()
        for stock in stocks:
            stock.update_fund_cluster_balance()
        return res
