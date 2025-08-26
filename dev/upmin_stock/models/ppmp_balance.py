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
    initial_balance = fields.Integer(string="Initial PPMP Balance", default=0)

    related_issuances = fields.One2many(
        "upmin_stock.issuance",
        string="Related Issuances",
        related="ppmp.related_issuances",
    )
    total_issued = fields.Integer(
        string="Total Issued",
        default=0,
        compute="_compute_total_issued",
        store=True,
        readonly=True,
    )
    ppmp_balance = fields.Integer(
        string="PPMP Balance",
        default=0,
        compute="_compute_ppmp_balance",
        store=True,
        readonly=True,
    )

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

    @api.depends("related_issuances", "related_issuances.quantity_issued")
    def _compute_total_issued(self):
        for line in self:
            line.total_issued = sum(
                issuance.quantity_issued
                for issuance in line.related_issuances
                if issuance.stock_no.id == line.stock_id.id
            )

    @api.depends("initial_balance", "total_issued")
    def _compute_ppmp_balance(self):
        for line in self:
            line.ppmp_balance = line.initial_balance - line.total_issued
