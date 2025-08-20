from odoo import api, models, fields


class PPMPBalance(models.Model):
    _name = "upmin_stock.ppmp_balance"
    _description = "PPMP Balance"
    _rec_name = "stock_id"

    ppmp = fields.Many2one("upmin_stock.ppmp", string="PPMP", required=True)
    stock_id = fields.Many2one("upmin_stock.stock", string="Stock", required=True)
    spmo_balance = fields.Integer(
        string="SPMO Balance",
        default=0,
        compute="_compute_spmo_balance",
        readonly=True,
        store=True,
    )
    ppmp_balance = fields.Integer(string="PPMP Balance", default=0)

    @api.depends("stock_id", "stock_id.balance", "ppmp.fund_cluster_id")
    def _compute_spmo_balance(self):
        for line in self:
            # Find stock_fund_balance with matching stock_id and fund_cluster
            fund_cluster = line.ppmp.fund_cluster_id
            stock_fund_balance = self.env["upmin_stock.stock_fund_balance"].search(
                [
                    ("stock_id", "=", line.stock_id.id),
                    ("fund_cluster_id", "=", fund_cluster.id),
                ],
                limit=1,
            )
            line.spmo_balance = stock_fund_balance.balance if stock_fund_balance else 0
