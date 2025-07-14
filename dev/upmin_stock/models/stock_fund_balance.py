from odoo import models, fields


class StockFundBalance(models.Model):
    _name = "upmin_stock.stock_fund_balance"
    _description = "Stock Balance per Fund Cluster"

    stock_id = fields.Many2one(
        "upmin_stock.stock", string="Stock", required=True, ondelete="cascade"
    )
    fund_cluster_id = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", required=True
    )
    balance = fields.Integer(string="Balance", default=0)

    _sql_constraints = [
        (
            "unique_stock_fund",
            "unique(stock_id, fund_cluster_id)",
            "Each stock-fund cluster combo must be unique!",
        )
    ]
