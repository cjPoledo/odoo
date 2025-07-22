from odoo import models, fields, api


class Stock(models.Model):
    _name = "upmin_stock.stock"
    _description = "Stock"
    _rec_name = "description"

    stock_no = fields.Char(string="Stock No", required=True)
    description = fields.Char(string="Description", required=True)
    unit = fields.Many2one("upmin_stock.measure_units", string="Unit", required=True)
    initial_balance = fields.Integer(
        string="Initial Balance", compute="_compute_total_replenished", store=True
    )
    price = fields.Float(string="Price", default=0.0)
    psdbm_price = fields.Float(string="PSDBM Price", default=0.0)
    category = fields.Many2one("upmin_stock.category", string="Category")
    replenishment_ids = fields.One2many(
        "upmin_stock.replenishment",
        "stock_id",
        string="Replenishment Logs",
    )
    issuance_ids = fields.One2many(
        "upmin_stock.issuance", "stock_no", string="Related Issuances"
    )

    balance = fields.Integer(string="Balance", compute="_compute_balance", store=True)
    per_fund_balance = fields.One2many(
        "upmin_stock.stock_fund_balance", "stock_id", string="Balance per Fund Cluster"
    )

    _sql_constraints = [
        ("stock_no_unique", "unique(stock_no)", "Stock No must be unique."),
    ]

    @api.depends("replenishment_ids.quantity")
    def _compute_total_replenished(self):
        for stock in self:
            total_replenished = sum(
                replenishment.quantity for replenishment in stock.replenishment_ids
            )
            stock.initial_balance = total_replenished

    @api.depends("replenishment_ids.quantity", "issuance_ids.ris_line.quantity_issued")
    def _compute_balance(self):
        for stock in self:
            total_balance = sum(
                replenishment.quantity for replenishment in stock.replenishment_ids
            )
            total_issued = sum(
                issuance.ris_line.quantity_issued for issuance in stock.issuance_ids
            )
            stock.balance = total_balance - total_issued

    def update_fund_cluster_balance(self):
        for stock in self:
            # clear old records
            self.env["upmin_stock.stock_fund_balance"].search(
                [("stock_id", "=", stock.id)]
            ).unlink()

            # recompute
            grouped = {}
            for r in stock.replenishment_ids:
                fc_id = r.fund_cluster_id.id
                grouped[fc_id] = grouped.get(fc_id, 0) + r.quantity

            for i in stock.issuance_ids:
                fc_id = i.ris_line.ris_id.fund_cluster.id
                grouped[fc_id] = grouped.get(fc_id, 0) - i.ris_line.quantity_issued

            for fc_id, qty in grouped.items():
                self.env["upmin_stock.stock_fund_balance"].create(
                    {
                        "stock_id": stock.id,
                        "fund_cluster_id": fc_id,
                        "balance": qty,
                    }
                )

    def action_replenish_stock(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Replenish Stock",
            "res_model": "upmin_stock.replenishment",
            "view_mode": "form",
            "view_id": self.env.ref("upmin_stock.stock_replenishment_view_form").id,
            "target": "new",
            "context": {
                "default_stock_id": self.id,
                "default_quantity": 0,
                "default_notes": "",
            },
        }

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.stock_no} - {record.description}"
            result.append((record.id, name))
        return result
