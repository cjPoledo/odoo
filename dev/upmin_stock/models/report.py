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
                    COALESCE(SUM(s.initial_balance), 0) AS total_quantity,
                    COALESCE(SUM(i.quantity_issued), 0) AS total_issued,
                    COALESCE(SUM(s.initial_balance), 0) - COALESCE(SUM(i.quantity_issued), 0) AS total_balance
                FROM
                    upmin_stock_stock s
                    LEFT JOIN upmin_stock_issuance i ON TRUE
            )
            """
        )
