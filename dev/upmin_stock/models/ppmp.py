from odoo import models, fields, api
from collections import Counter
from odoo.exceptions import ValidationError


class PPMP(models.Model):
    _name = "upmin_stock.ppmp"
    _description = "Project Procurement Management Plan"
    _rec_name = "rc"
    _order = "rc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    rc = fields.Many2one(
        "upmin_stock.rc", string="Responsibility Center", required=True
    )
    fund_cluster_id = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", required=True
    )
    ppmp_balance_lines = fields.One2many(
        "upmin_stock.ppmp_balance", "ppmp", string="PPMP Balances"
    )
    related_issuances = fields.One2many(
        "upmin_stock.issuance", "ppmp_id", string="Related Issuances"
    )

    _sql_constraints = [
        (
            "rc_fc_uniq",
            "unique(rc,fund_cluster_id)",
            "The combination of Responsibility Center and Fund Cluster must be unique!",
        ),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.rc.rc_code} - {record.fund_cluster_id.name}"
            result.append((record.id, name))
        return result

    @api.constrains("ppmp_balance_lines")
    def _check_unique_stock_id(self):
        for rec in self:
            stock_ids = [
                line.stock_id for line in rec.ppmp_balance_lines if line.stock_id
            ]
            counts = Counter(stock_ids)
            duplicates = [
                stock.display_name for stock, count in counts.items() if count > 1
            ]

            if duplicates:
                dup_str = ", ".join(duplicates)
                raise ValidationError(
                    f"The following stock(s) are duplicated: {dup_str}"
                )
