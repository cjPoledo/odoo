from odoo import models, fields


class RC(models.Model):
    _name = "upmin_stock.rc"
    _description = "Responsibility Center"
    _rec_name = "rc_code"
    _order = "rc_code"

    rc_code = fields.Char(string="RC Code", required=True)
    rc_name = fields.Char(string="RC Name", required=True)

    _sql_constraints = [
        ("rc_code_unique", "unique(rc_code)", "RC Code must be unique."),
        ("rc_name_unique", "unique(rc_name)", "RC Name must be unique."),
    ]
