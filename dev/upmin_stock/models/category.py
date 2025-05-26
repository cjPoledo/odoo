from odoo import models, fields

class Category(models.Model):
    _name = 'upmin_stock.category'
    _description = 'Category'
    
    category = fields.Char(string="Category", required=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.category}"
            result.append((record.id, name))
        return result