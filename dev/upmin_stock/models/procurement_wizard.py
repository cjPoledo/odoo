from odoo import models, fields, _
from odoo.exceptions import UserError
import base64
import xlrd


class ProcurementWizard(models.Model):
    _name = "upmin_stock.procurement_wizard"
    _description = "Procurement Wizard"
    _rec_name = "date_time"

    date_time = fields.Datetime(
        string="Date and Time", default=fields.Datetime.now, readonly=True
    )
    procurement_data = fields.One2many(
        "upmin_stock.procurement", "parent_id", string="Procurement Data", readonly=True
    )
    excel_file = fields.Binary(string="Upload Excel", store=False)  # Temporary storage
    file_name = fields.Char(string="File Name", store=False)  # Temporary storage

    def _create(self, data_list):
        self.import_excel()
        return super()._create(data_list)

    def import_excel(self):
        if not self.excel_file:
            return

        try:
            excel_data = base64.b64decode(self.excel_file)
            workbook = xlrd.open_workbook(file_contents=excel_data)
            sheet = workbook.sheet_by_index(0)

            # Clear existing lines
            self.procurement_data.unlink()

            # Process Excel rows
            for row in range(1, sheet.nrows):
                vals = {
                    "parent_id": self.id,
                    "no": sheet.cell(row, 0).value,
                    "remarks": sheet.cell(row, 1).value,
                    "end_user": sheet.cell(row, 2).value,
                    "rc_code": sheet.cell(row, 3).value,
                    "ris_no": sheet.cell(row, 4).value,
                    "iar_no": sheet.cell(row, 5).value,
                    "date": sheet.cell(row, 6).value,
                    "fund_cluster": sheet.cell(row, 7).value,
                    "ics": sheet.cell(row, 8).value,
                    "hv_lv": sheet.cell(row, 9).value,
                    "stock_no": sheet.cell(row, 10).value,
                    "description": sheet.cell(row, 11).value,
                    "unit": sheet.cell(row, 12).value,
                    "quantity": sheet.cell(row, 13).value,
                    "unit_cost": sheet.cell(row, 14).value,
                    "amount": sheet.cell(row, 15).value,
                    "PO_no": sheet.cell(row, 16).value,
                    "date_signed": sheet.cell(row, 17).value,
                    "supplier": sheet.cell(row, 18).value,
                    "invoice_date": sheet.cell(row, 19).value,
                    "invoice_no": sheet.cell(row, 20).value,
                    "dr_no": sheet.cell(row, 21).value,
                    "invoice_remarks": sheet.cell(row, 22).value,
                    "delivery_schedule": sheet.cell(row, 23).value,
                    "no_days_delayed": sheet.cell(row, 24).value,
                    "with_extension": sheet.cell(row, 25).value,
                    "partial": sheet.cell(row, 26).value,
                    "waiver": sheet.cell(row, 27).value,
                }
                self.env["upmin_stock.procurement"].create(vals)

            # Clear the temporary file data
            self.excel_file = False
            self.file_name = False

        except Exception as e:
            raise UserError(_("Error processing Excel file: %s" % str(e)))
