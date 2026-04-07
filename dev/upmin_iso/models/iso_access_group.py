from odoo import models, fields, api


class IsoAccessGroup(models.Model):
    _name = "upmin_iso.iso_access_group"
    _description = "Departments that grant children access to their ISO documents"
    _rec_name = "department_id"
    _order = "department_id"

    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        required=True,
    )

    _sql_constraints = [
        (
            "department_unique",
            "unique(department_id)",
            "This department is already an access group.",
        )
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env.registry.clear_caches()
        return records

    def write(self, vals):
        result = super().write(vals)
        self.env.registry.clear_caches()
        return result

    def unlink(self):
        result = super().unlink()
        self.env.registry.clear_caches()
        return result
