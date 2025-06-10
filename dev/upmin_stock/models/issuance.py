from odoo import models, fields


class Issuance(models.Model):
    _name = "upmin_stock.issuance"
    _description = "Issuance"
    _rec_name = "seq_no"

    seq_no = fields.Char(string="Sequence Number", required=True)
    date_issued = fields.Date(string="Date Issued", required=True)
    requested_by = fields.Many2one(
        "res.partner", string="Requested By", required=True
    )  # Assuming 'People' is linked to 'res.partner'
    ris_no = fields.Char(string="RIS Number", required=True)
    rc_code = fields.Many2one("upmin_stock.rc", string="RC Code", required=True)
    remarks = fields.Text(string="Remarks")
    stock_no = fields.Many2one(
        "upmin_stock.stock", string="Stock Number", required=True
    )
    quantity_requested = fields.Integer(string="Quantity Requested", required=True)
    quantity_issued = fields.Integer(string="Quantity Issued", required=True)

    _sql_constraints = [
        (
            "seq_no_unique",
            "unique(seq_no)",
            "Sequence Number must be unique.",
        ),
        (
            "stock_no_quantity_check",
            "CHECK (quantity_issued <= quantity_requested)",
            "Quantity Issued cannot exceed Quantity Requested.",
        ),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.seq_no} - {record.rc_code.rc_code} - {record.stock_no.description}"
            result.append((record.id, name))
        return result
