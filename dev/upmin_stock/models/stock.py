from odoo import models, fields, api
import io, base64
import xlsxwriter


class Stock(models.Model):
    _name = "upmin_stock.stock"
    _description = "Stock"
    _rec_name = "description"
    _order = "description"

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
    issued = fields.Integer(string="Issued", compute="_compute_issued", store=True)
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

    @api.depends(
        "replenishment_ids.quantity",
        "issuance_ids.ris_line.quantity_issued",
        "per_fund_balance.balance",
    )
    def _compute_balance(self):
        for stock in self:
            total_balance = sum(
                replenishment.quantity for replenishment in stock.replenishment_ids
            )
            total_issued = sum(
                issuance.ris_line.quantity_issued for issuance in stock.issuance_ids
            )
            stock.balance = total_balance - total_issued

    @api.depends("issuance_ids.ris_line.quantity_issued")
    def _compute_issued(self):
        for stock in self:
            total_issued = sum(
                issuance.ris_line.quantity_issued for issuance in stock.issuance_ids
            )
            stock.issued = total_issued

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

    def action_download_report_global(self):
        active_ids = self.env.context.get("active_ids", [])
        selected_items = self.browse(active_ids)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Stocks")

        fund_clusters = self.env["upmin_stock.fund_cluster"].search([])

        headers = ["Stock No", "Description", "Unit"]
        for fc in fund_clusters:
            headers.append(f"Initial Balance ({fc.name})")
            headers.append(f"Issued ({fc.name})")
            headers.append(f"Balance ({fc.name})")
        headers.extend(["Price", "PSDBM Price", "Category"])

        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for row, data in enumerate(selected_items):
            worksheet.write(row + 1, 0, data.stock_no)
            worksheet.write(row + 1, 1, data.description)
            worksheet.write(row + 1, 2, data.unit.measure_unit)
            col = 2
            for fc in fund_clusters:
                col += 1
                init_balance = sum(
                    r.quantity
                    for r in data.replenishment_ids
                    if r.fund_cluster_id.id == fc.id
                )
                worksheet.write(row + 1, col, init_balance)
                col += 1
                issued = sum(
                    i.quantity_issued
                    for i in data.issuance_ids
                    if i.fund_cluster == fc.name
                )
                worksheet.write(row + 1, col, issued)
                col += 1
                balance = (
                    data.per_fund_balance.filtered(
                        lambda l: l.fund_cluster_id.id == fc.id
                    )[:1].balance
                    or 0
                )
                worksheet.write(row + 1, col, balance)
            worksheet.write(row + 1, col + 1, data.price)
            worksheet.write(row + 1, col + 2, data.psdbm_price)
            worksheet.write(row + 1, col + 3, data.category.category or "")

        workbook.close()
        output.seek(0)

        file_content = base64.b64encode(output.read())
        attachment = self.env["ir.attachment"].create(
            {
                "name": "stocks_report.xlsx",
                "type": "binary",
                "datas": file_content,
                "res_model": "upmin_stock.stock",
                "res_id": 0,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.stock_no} - {record.description}"
            result.append((record.id, name))
        return result

    def _name_search(self, name="", args=None, operator="ilike", limit=100):
        args = list(args or [])
        domain = ["|", ("stock_no", operator, name), ("description", operator, name)]
        if not (name == "" and operator == "ilike"):
            args += domain
        return self._search(args, limit=limit)

    def unlink(self):
        for stock in self:
            self.env["upmin_stock.stock_fund_balance"].search(
                [("stock_id", "=", stock.id)]
            ).unlink()
        return super().unlink()
