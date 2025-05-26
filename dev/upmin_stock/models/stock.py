from odoo import models, fields


class Stock(models.Model):
    _name = "upmin_stock.stock"
    _description = "Stock"

    stock_no = fields.Char(string="Stock No", required=True)
    description = fields.Text(string="Description")
    unit = fields.Many2one("upmin_stock.measure_units", string="Unit")
    initial_balance = fields.Integer(string="Initial Balance", default=0)
    price = fields.Float(string="Price", default=0.0)
    psdbm_price = fields.Float(string="PSDBM Price", default=0.0)
    category = fields.Many2one("upmin_stock.category", string="Category")

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.stock_no} - {record.description}"
            result.append((record.id, name))
        return result
