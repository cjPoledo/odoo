from odoo import models, fields


class FundCluster(models.Model):
    _name = "upmin_stock.fund_cluster"
    _description = "Fund Cluster"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Fund Cluster", required=True)

    _sql_constraints = [
        (
            "fund_cluster_unique",
            "unique(name)",
            "Fund Cluster Name must be unique.",
        ),
    ]
