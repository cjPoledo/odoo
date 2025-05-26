from odoo import models, fields

class MeasureUnits(models.Model):
    _name = 'upmin_stock.measure_units'
    _description = 'Units of Measure'

    measure_unit = fields.Char(string="Unit of Measure", required=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.measure_unit}"
            result.append((record.id, name))
        return result
    