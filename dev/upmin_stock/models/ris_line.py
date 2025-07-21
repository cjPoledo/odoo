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

    _sql_constraints = [
        (
            "stock_no_quantity_check",
            "CHECK (quantity_issued <= quantity_req)",
            "Quantity Issued cannot exceed Quantity Requested.",
        ),
        (
            "quantity_issued_positive_check",
            "CHECK (quantity_issued >= 0)",
            "Quantity Issued must be positive.",
        ),
        (
            "quantity_requested_positive_check",
            "CHECK (quantity_req >= 0)",
            "Quantity Requested must be positive.",
        ),
    ]

    @api.constrains("quantity_req", "quantity_issued")
    def _check_quantity(self):
        for record in self:
            if record.stock_balance < record.quantity_req:
                raise models.ValidationError(
                    f"({record.stock_id.stock_no}) Quantity requested cannot exceed the current stock balance."
                )
            elif record.stock_balance < record.quantity_issued:
                raise models.ValidationError(
                    f"({record.stock_id.stock_no}) Quantity issued cannot exceed the current stock balance."
                )

    @api.onchange("stock_avail")
    def _onchange_stock_avail(self):
        if not self.stock_avail:
            self.quantity_issued = 0
