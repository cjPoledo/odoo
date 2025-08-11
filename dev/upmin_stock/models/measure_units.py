from odoo import models, fields


class MeasureUnits(models.Model):
    _name = "upmin_stock.measure_units"
    _description = "Units of Measure"
    _rec_name = "measure_unit"
    _order = "measure_unit"

    measure_unit = fields.Char(string="Unit of Measure", required=True)

    _sql_constraints = [
        (
            "measure_unit_unique",
            "unique(measure_unit)",
            "Unit of Measure must be unique.",
        ),
    ]
