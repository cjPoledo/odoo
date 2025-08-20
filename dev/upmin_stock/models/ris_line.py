from odoo import models, fields, api


class RISLine(models.Model):
    _name = "upmin_stock.ris_line"
    _description = "RIS Line"
    _rec_name = "ppmp_balance_id"

    ris_id = fields.Many2one(
        "upmin_stock.ris", string="RIS", required=True, ondelete="cascade"
    )
    ppmp = fields.Many2one("upmin_stock.ppmp", string="PPMP", related="ris_id.ppmp_id")
    ppmp_balance_id = fields.Many2one(
        "upmin_stock.ppmp_balance",
        string="Stock",
        required=True,
        domain="[('ppmp', '=', ppmp)]",
    )
    stock_balance = fields.Integer(
        string="SPMO Balance", related="ppmp_balance_id.spmo_balance", readonly=True
    )
    ppmp_balance = fields.Integer(
        string="PPMP Balance", related="ppmp_balance_id.ppmp_balance", readonly=True
    )
    quantity_req = fields.Integer(string="Quantity Requested", required=True)
    stock_avail = fields.Boolean(string="Stock Available?", default=False)
    quantity_issued = fields.Integer(string="Quantity Issued", default=0)
    remarks = fields.Text(string="Remarks")
    user_has_permission = fields.Boolean(
        string="User Has Special Permission",
        related="ris_id.user_has_permission",
        store=False,
    )

    status = fields.Selection(
        string="Status",
        related="ris_id.status",
        readonly=True,
    )

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
            min_balance = min(record.stock_balance, record.ppmp_balance)
            if record.status == "draft" and min_balance < record.quantity_req:
                raise models.ValidationError(
                    f"({record.ppmp_balance_id.stock_id.stock_no}) Quantity requested cannot exceed the stock and PPMP balance."
                )
            elif record.status == "issuance" and min_balance < record.quantity_issued:
                raise models.ValidationError(
                    f"({record.ppmp_balance_id.stock_id.stock_no}) Quantity issued cannot exceed the stock and PPMP balance."
                )

    @api.onchange("stock_avail")
    def _onchange_stock_avail(self):
        if not self.stock_avail:
            self.quantity_issued = 0

    def name_get(self):
        result = []
        for record in self:
            name = (
                f"{record.ris_id.ris_no} - {record.ppmp_balance_id.stock_id.stock_no}"
            )
            result.append((record.id, name))
        return result

    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            rec.ppmp_balance_id.stock_id.update_fund_cluster_balance()
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec.ppmp_balance_id.stock_id.update_fund_cluster_balance()
        return res

    def unlink(self):
        stocks = self.mapped("ppmp_balance_id.stock_id")
        res = super().unlink()
        for stock in stocks:
            stock.update_fund_cluster_balance()
        return res
