from odoo import models, fields, api


class ISOClause(models.Model):
    _name = "upmin_iso.iso_clause"
    _description = "ISO Clause"
    _rec_name = "clause_number"
    _order = "clause_number_sortkey"

    clause_number = fields.Char(string="Clause Number", required=True)
    clause_number_sortkey = fields.Char(
        compute="_compute_clause_number_sortkey", store=True
    )
    clause_title = fields.Char(string="Clause Title", required=True)
    clause_description = fields.Text(string="Clause Description")

    @api.depends("clause_number")
    def _compute_clause_number_sortkey(self):
        for rec in self:
            if rec.clause_number:
                parts = rec.clause_number.split(".")
                rec.clause_number_sortkey = ".".join(p.zfill(3) for p in parts)
            else:
                rec.clause_number_sortkey = ""

    _sql_constraints = [
        (
            "clause_number_unique",
            "unique(clause_number)",
            "Clause number must be unique.",
        ),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.clause_number} - {record.clause_title}"
            result.append((record.id, name))
        return result
