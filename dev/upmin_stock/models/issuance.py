from odoo import models, fields


class Issuance(models.Model):
    _name = "upmin_stock.issuance"
    _description = "Issuance"
    _rec_name = "seq_no"
    _order = "seq_no asc"

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
    ris_line = fields.Many2one(
        "upmin_stock.ris_line", string="RIS Line", required=True, ondelete="cascade"
    )

    date_issued = fields.Date(
        string="Date Issued", related="ris_line.ris_id.issue_date", store=False
    )
    requested_by = fields.Many2one(
        "res.partner",
        string="Requested By",
        related="ris_line.ris_id.requested_by",
        store=False,
    )
    ris_no = fields.Many2one(
        "upmin_stock.ris", string="RIS No.", related="ris_line.ris_id", store=False
    )
    office = fields.Char(related="ris_line.ris_id.rc_code.rc_name", store=False)
    rc_code = fields.Many2one(
        "upmin_stock.rc",
        string="RC Code",
        related="ris_line.ris_id.rc_code",
        store=False,
    )
    stock_no = fields.Many2one(
        "upmin_stock.stock",
        string="Stock No. ",
        related="ris_line.ppmp_balance_id.stock_id",
        store=False,
    )
    stock_no_id = fields.Char(
        string="Stock No.",
        related="ris_line.ppmp_balance_id.stock_id.stock_no",
        store=False,
    )
    stock_desc = fields.Char(
        string="Stock Description",
        related="ris_line.ppmp_balance_id.stock_id.description",
        store=False,
    )
    unit = fields.Char(
        string="Unit",
        related="ris_line.ppmp_balance_id.stock_id.unit.measure_unit",
        store=False,
    )
    quantity_requested = fields.Integer(
        string="Quantity Requested", related="ris_line.quantity_req", store=False
    )
    balance = fields.Integer(
        string="Balance", related="ris_line.stock_balance", store=False
    )
    quantity_issued = fields.Integer(
        string="Quantity Issued", related="ris_line.quantity_issued", store=True
    )
    remarks = fields.Text(string="Remarks", related="ris_line.remarks", store=False)
    fund_cluster = fields.Char(
        string="Fund Cluster", related="ris_line.ris_id.fund_cluster.name", store=True
    )
    ppmp_id = fields.Many2one(
        "upmin_stock.ppmp",
        string="PPMP",
        related="ris_line.ppmp",
        store=False,
    )

    _sql_constraints = [
        (
            "seq_no_unique",
            "unique(seq_no)",
            "Sequence Number must be unique.",
        )
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.seq_no} - {record.ris_line.ris_id.ris_no} - {record.ris_line.ppmp_balance_id.stock_id.description}"
            result.append((record.id, name))
        return result

    def create(self, vals):
        res = super().create(vals)
        for rec in res:
            rec.ris_line.ppmp_balance_id.stock_id.update_fund_cluster_balance()
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec.ris_line.ppmp_balance_id.stock_id.update_fund_cluster_balance()
        return res

    def unlink(self):
        stocks = self.mapped("ris_line.ppmp_balance_id.stock_id")
        res = super().unlink()
        for stock in stocks:
            stock.update_fund_cluster_balance()
        return res

    def wizard_unlink(self):
        ppmp_balance_line = self.mapped("ris_line.ppmp_balance_id")
        quantity_issued = self.quantity_issued
        res = super().unlink()
        for line in ppmp_balance_line:
            initial_balance = line.initial_balance or 0
            line.initial_balance -= quantity_issued
            line.ppmp.message_post(
                body=f"[RESET DATA] Adjusted initial balance of {line.stock_id.stock_no} from {initial_balance} to {line.initial_balance}"
            )
            line.stock_id.update_fund_cluster_balance()
            ppmp_balance_line._compute_total_issued()
        return res
