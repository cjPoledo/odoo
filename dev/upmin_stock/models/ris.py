from odoo import models, fields, api
from datetime import datetime


class RIS(models.Model):
    _name = "upmin_stock.ris"
    _description = "Requisition and Issue Slip"
    _rec_name = "ris_no"

    ris_no = fields.Char(
        string="RIS No.",
        required=True,
        readonly=True,
    )
    entity_name = fields.Char(
        string="Entity Name",
        required=True,
        default="UNIVERSITY OF THE PHILIPPINES MINDANAO",
    )
    fund_cluster = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", required=True
    )
    division = fields.Char(string="Division", required=True)
    rc_code = fields.Many2one(
        "upmin_stock.rc", string="Responsibility Center Code", required=True
    )
    line_ids = fields.One2many("upmin_stock.ris_line", "ris_id", string="Stocks")
    purpose = fields.Text(string="Purpose")
    requested_by = fields.Char(string="Requested By", required=True)
    approved_by = fields.Char(string="Approved By")
    issued_by = fields.Char(string="Issued By")
    received_by = fields.Char(string="Received By")

    _sql_constraints = [
        ("ris_no_uniq", "unique(ris_no)", "The RIS No. must be unique!"),
    ]

    @api.model
    def create(self, vals):
        if not vals.get("ris_no"):
            today = fields.Date.context_today(self)
            year = today.strftime("%Y")
            month = today.strftime("%m")
            code = f"stock.ref.sr.{year}.{month}"

            # find or create sequence
            sequence = (
                self.env["ir.sequence"].sudo().search([("code", "=", code)], limit=1)
            )
            if not sequence:
                sequence = (
                    self.env["ir.sequence"]
                    .sudo()
                    .create(
                        {
                            "name": f"Stock Reference SR {year}-{month}",
                            "code": code,
                            "prefix": f"SR{year}-{month}-",
                            "padding": 3,
                            "number_next": 1,
                            "number_increment": 1,
                        }
                    )
                )

            vals["ris_no"] = sequence.sudo().next_by_code(code)

        return super().create(vals)
