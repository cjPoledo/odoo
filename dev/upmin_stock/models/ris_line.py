from odoo import models, fields, api


class RISLine(models.Model):
    _name = "upmin_stock.ris_line"
    _description = "RIS Line"

    ris_id = fields.Many2one(
        "upmin_stock.ris", string="RIS", required=True, ondelete="cascade"
    )
    stock_id = fields.Many2one("upmin_stock.stock", string="Stock", required=True)
    stock_balance = fields.Integer(
        string="Balance", compute="_compute_stock_balance", readonly=True, store=False
    )
    quantity_req = fields.Integer(string="Quantity Requested", required=True)
    stock_avail = fields.Boolean(string="Stock Available?", default=False)
    quantity_issued = fields.Integer(string="Quantity Issued", default=0)
    remarks = fields.Text(string="Remarks")

    @api.depends("stock_id", "ris_id.fund_cluster")
    def _compute_stock_balance(self):
        for line in self:
            # Find stock_fund_balance with matching stock_id and fund_cluster
            fund_cluster = line.ris_id.fund_cluster
            stock_fund_balance = self.env["upmin_stock.stock_fund_balance"].search(
                [
                    ("stock_id", "=", line.stock_id.id),
                    ("fund_cluster_id", "=", fund_cluster.id),
                ],
                limit=1,
            )
            line.stock_balance = stock_fund_balance.balance if stock_fund_balance else 0
