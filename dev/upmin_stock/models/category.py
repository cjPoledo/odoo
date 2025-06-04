from odoo import models, fields


class Category(models.Model):
    _name = "upmin_stock.category"
    _description = "Category"
    _rec_name = "category"

    category = fields.Char(string="Category", required=True)

    _sql_constraints = [
        ("category_unique", "unique(category)", "Category must be unique."),
    ]
