from odoo import models, fields

class RC(models.Model):
    _name = 'upmin_stock.rc'
    _description = 'Responsibility Center'
    
    rc_code = fields.Char(string="RC Code", required=True)
    rc_name = fields.Char(string="RC Name", required=True)
    
    def name_get(self):
        result = []
        for record in self:
            name = f"{record.rc_name}"
            result.append((record.id, name))
        return result