from odoo import models, fields


class Issuance(models.Model):
    _name = "upmin_stock.issuance"
    _description = "Issuance"
    _rec_name = "seq_no"

    seq_no = fields.Float(
        string="Sequence Number",
        default=lambda self: (
            self.env["upmin_stock.issuance"]
            .search([], order="seq_no desc", limit=1)
            .seq_no
            or 1.0
        )
        + 0.001,
        digits=(12, 3),
        required=True,
    )
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

    balance = fields.Integer(
        string="Current Balance",
        related="stock_no.balance",
        store=False,
        readonly=True,
    )
    unit = fields.Many2one(
        related="stock_no.unit",
        string="Unit",
        store=False,
        readonly=True,
    )

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
