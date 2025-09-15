from odoo import models, fields, tools


class Report(models.Model):
    _name = "upmin_stock.report"
    _description = "Stock Report"
    _auto = False  # Don't auto create a table
    _rec_name = "fund_cluster"

    fund_cluster = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", readonly=True
    )
    total_quantity = fields.Integer(string="Total Quantity", readonly=True)
    total_issued = fields.Integer(string="Total Issued", readonly=True)
    total_balance = fields.Integer(string="Total Balance", readonly=True)

    def init(self):
        # Ensure dependent tables exist before creating the view
        self.env.cr.execute(
            """
            SELECT to_regclass('public.upmin_stock_replenishment'), to_regclass('public.upmin_stock_issuance')
        """
        )
        result = self.env.cr.fetchone()
        if not all(result):
            # Skip view creation if tables do not exist
            return

        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW upmin_stock_report AS (
                SELECT
                    fc.id AS id,
                    fc.id AS fund_cluster,
                    COALESCE(r.total_quantity, 0) AS total_quantity,
                    COALESCE(i.total_issued, 0) AS total_issued,
                    COALESCE(r.total_quantity, 0) - COALESCE(i.total_issued, 0) AS total_balance
                FROM
                    upmin_stock_fund_cluster fc
                LEFT JOIN ( 
                    SELECT fund_cluster_id, SUM(quantity) AS total_quantity
                    FROM upmin_stock_replenishment
                    GROUP BY fund_cluster_id
                ) r ON r.fund_cluster_id = fc.id
                LEFT JOIN (
                    SELECT fund_cluster, SUM(quantity_issued) AS total_issued
                    FROM upmin_stock_issuance WHERE archived = FALSE
                    GROUP BY fund_cluster
                ) i ON i.fund_cluster = fc.name
            )
            """
        )
