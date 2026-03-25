from odoo import models


class HrDepartment(models.Model):
    _inherit = "hr.department"
    _rec_name = "name"
