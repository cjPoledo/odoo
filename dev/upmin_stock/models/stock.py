from odoo import models, fields


class Stock(models.Model):
    _name = "upmin_stock.stock"
    _description = "Stock"

    stock_no = fields.Char(string="Stock No", required=True)
    description = fields.Char(string="Description", required=True)
    unit = fields.Many2one("upmin_stock.measure_units", string="Unit", required=True)
    initial_balance = fields.Integer(string="Initial Balance", default=0)
    price = fields.Float(string="Price", default=0.0)
    psdbm_price = fields.Float(string="PSDBM Price", default=0.0)
    category = fields.Many2one("upmin_stock.category", string="Category")

    balance = fields.Integer(string="Balance", compute="_compute_balance", store=False)

    _sql_constraints = [
        ("stock_no_unique", "unique(stock_no)", "Stock No must be unique."),
    ]

    def _compute_balance(self):
        for stock in self:
            total_issued = sum(
                issuance.quantity_issued
                for issuance in self.env["upmin_stock.issuance"].search(
                    [("stock_no", "=", stock.id)]
                )
            )
            stock.balance = stock.initial_balance - total_issued

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.stock_no} - {record.description}"
            result.append((record.id, name))
        return result
