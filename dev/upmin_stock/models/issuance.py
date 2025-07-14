from odoo import models, fields, api


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
            or 0.999
        )
        + 0.001,
        digits=(12, 3),
        required=True,
    )
    date_issued = fields.Date(
        string="Date Issued",
        required=True,
        default=lambda self: (
            self.env["upmin_stock.issuance"]
            .search([], order="id desc", limit=1)
            .date_issued
            or fields.Date.context_today(self)
        ),
    )
    requested_by = fields.Many2one(
        "res.partner",
        string="Requested By",
        required=True,
        default=lambda self: (
            self.env["upmin_stock.issuance"]
            .search([], order="id desc", limit=1)
            .requested_by.id
            or False
        ),
    )  # Assuming 'People' is linked to 'res.partner'
    ris_no = fields.Char(
        string="RIS Number",
        required=True,
        default=lambda self: (
            self.env["upmin_stock.issuance"].search([], order="id desc", limit=1).ris_no
            or ""
        ),
    )
    rc_code = fields.Many2one(
        "upmin_stock.rc",
        string="RC Code",
        required=True,
        default=lambda self: (
            self.env["upmin_stock.issuance"]
            .search([], order="id desc", limit=1)
            .rc_code.id
            or False
        ),
    )
    remarks = fields.Text(
        string="Remarks",
        default=lambda self: (
            self.env["upmin_stock.issuance"]
            .search([], order="id desc", limit=1)
            .remarks
            or ""
        ),
    )
    stock_no = fields.Many2one(
        "upmin_stock.stock", string="Stock Number", required=True
    )
    quantity_requested = fields.Integer(string="Quantity Requested", required=True)
    quantity_issued = fields.Integer(string="Quantity Issued", required=True)
    fund_cluster_id = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", required=True
    )

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
        (
            "quantity_issued_positive_check",
            "CHECK (quantity_issued >= 0)",
            "Quantity Issued must be positive.",
        ),
        (
            "quantity_requested_positive_check",
            "CHECK (quantity_requested >= 0)",
            "Quantity Requested must be positive.",
        ),
    ]

    @api.constrains("quantity_issued")
    def _check_quantity_issued(self):
        for record in self:
            if record.stock_no.balance < 0:
                raise models.ValidationError(
                    "Quantity Issued cannot exceed the current stock balance."
                )

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.seq_no} - {record.rc_code.rc_code} - {record.stock_no.description}"
            result.append((record.id, name))
        return result
