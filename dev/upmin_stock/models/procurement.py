from odoo import models, fields


class Procurement(models.Model):
    _name = "upmin_stock.procurement"
    _description = "Procurement"
    _rec_name = "no"

    parent_id = fields.Many2one(
        "upmin_stock.procurement_wizard",
        string="Parent Wizard",
        required=True,
    )
    no = fields.Integer(string="No.")
    remarks = fields.Text(string="Remarks")
    end_user = fields.Char(string="End User")
    rc_code = fields.Char(string="Responsibility Center Code")
    ris_no = fields.Char(string="RIS No.")
    iar_no = fields.Char(string="IAR No.")
    date = fields.Date(string="Date")
    fund_cluster = fields.Char(string="Fund Cluster")
    ics = fields.Char(string="ICS")
    hv_lv = fields.Char(string="HV/LV")
    stock_no = fields.Char(string="Stock No.")
    description = fields.Char(string="Description")
    unit = fields.Char(string="Unit")
    quantity = fields.Integer(string="Quantity")
    unit_cost = fields.Float(string="Unit Cost")
    amount = fields.Float(string="Amount", store=True)
    PO_no = fields.Char(string="PO No.")
    date_signed = fields.Date(string="Date Signed by Supplier")
    supplier = fields.Char(string="Supplier")
    invoice_date = fields.Date(string="Date (invoice)")
    invoice_no = fields.Char(string="Invoice No.")
    dr_no = fields.Char(string="DR No.")
    invoice_remarks = fields.Text(string="Remarks (invoice)")
    delivery_schedule = fields.Date(string="Delivery Schedule")
    no_days_delayed = fields.Integer(string="No. of Days Delayed")
    with_extension = fields.Boolean(string="With Extension", default=False)
    partial = fields.Boolean(string="Partial", default=False)
    waiver = fields.Boolean(string="Waiver", default=False)

    replenishment_ids = fields.One2many(
        "upmin_stock.replenishment",
        "procurement_import_id",
        string="Replenishment Logs",
    )

    def unlink(self):
        for item in self.replenishment_ids:
            item.unlink()

        return super().unlink()
