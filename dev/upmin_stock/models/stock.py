from odoo import models, fields


class Stock(models.Model):
    _name = "upmin_stock.stock"
    _description = "Stock"

    stock_no = fields.Char(string="Stock No", required=True)
    description = fields.Text(string="Description")
    unit = fields.Char(string="Unit")
    initial_balance = fields.Integer(string="Initial Balance", default=0)
    price = fields.Float(string="Price", default=0.0)
    psdbm_price = fields.Float(string="PSDBM Price", default=0.0)
    category = fields.Char(string="Category")
