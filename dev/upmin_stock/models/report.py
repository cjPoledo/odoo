from odoo import models, fields, tools


class Report(models.Model):
    _name = "upmin_stock.report"
    _description = "Stock Report"
    _auto = False  # Don't auto create a table
    _rec_name = "id"

    id = fields.Integer(string="ID", readonly=True)
    total_quantity = fields.Integer(string="Total Quantity", readonly=True)
    total_issued = fields.Integer(string="Total Issued", readonly=True)
    total_balance = fields.Integer(string="Total Balance", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
                CREATE or REPLACE VIEW upmin_stock_report AS (
                    SELECT
                        1 AS id,
                        (SELECT COALESCE(SUM(quantity), 0) FROM upmin_stock_replenishment) AS total_quantity,
                        (SELECT COALESCE(SUM(quantity_issued), 0) FROM upmin_stock_issuance) AS total_issued,
                        (SELECT COALESCE(SUM(quantity), 0) FROM upmin_stock_replenishment) -
                        (SELECT COALESCE(SUM(quantity_issued), 0) FROM upmin_stock_issuance) AS total_balance
                )
            """
        )
