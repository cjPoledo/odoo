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
    excel_file = fields.Binary(
        string="Upload Excel",
        help="Upload an Excel file with procurement data. Use the provided template.",
    )
    file_name = fields.Char(string="File Name")
    applied = fields.Boolean(string="Applied", default=False)

    def action_import_excel(self):
        current_row = 1
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

                def get_excel_date(cell_value):
                    # xlrd returns float for Excel dates, otherwise string/empty
                    if isinstance(cell_value, float):
                        dt_tuple = xlrd.xldate_as_tuple(cell_value, workbook.datemode)
                        # Only date part
                        return "%04d-%02d-%02d" % (
                            dt_tuple[0],
                            dt_tuple[1],
                            dt_tuple[2],
                        )
                    return cell_value or False

                current_row += 1

                vals = {
                    "parent_id": self.id,
                    "no": sheet.cell(row, 0).value,
                    "remarks": sheet.cell(row, 1).value,
                    "end_user": sheet.cell(row, 2).value,
                    "rc_code": sheet.cell(row, 3).value,
                    "ris_no": sheet.cell(row, 4).value,
                    "iar_no": sheet.cell(row, 5).value,
                    "date": get_excel_date(sheet.cell(row, 6).value),
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
                    "date_signed": get_excel_date(sheet.cell(row, 17).value),
                    "supplier": sheet.cell(row, 18).value,
                    "invoice_date": get_excel_date(sheet.cell(row, 19).value),
                    "invoice_no": sheet.cell(row, 20).value,
                    "dr_no": sheet.cell(row, 21).value,
                    "invoice_remarks": sheet.cell(row, 22).value,
                    "delivery_schedule": get_excel_date(sheet.cell(row, 23).value),
                    "no_days_delayed": sheet.cell(row, 24).value,
                    "with_extension": sheet.cell(row, 25).value,
                    "partial": sheet.cell(row, 26).value,
                    "waiver": sheet.cell(row, 27).value,
                }
                self.env["upmin_stock.procurement"].create(vals)

            # # Clear the temporary file data to free up storage
            # self.write({"excel_file": False, "file_name": False})

        except Exception as e:
            raise UserError(
                _("Error processing Excel file (row %d): %s" % (current_row, str(e)))
            )

    def check_errors(self, line):
        # Ensure each required field is filled in procurement lines
        needed_fields = [
            "fund_cluster",
            "stock_no",
            "description",
            "unit",
            "unit_cost",
            "quantity",
        ]
        missing_fields = [
            field
            for field in needed_fields
            if line[field] in (None, "")  # treat 0 as valid, only None or "" is missing
        ]
        return missing_fields

    def action_validate_apply(self):
        if not self.procurement_data:
            raise UserError(
                _("No procurement data to validate. Please import data first.")
            )

        errors = ["ERRORS:"]
        warnings = ["WARNINGS:"]
        changes = ["CHANGES:"]

        for idx, line in enumerate(self.procurement_data, start=2):
            missing_fields = self.check_errors(line)
            if missing_fields:
                missing = ",".join(missing_fields)
                errors.append(
                    f"Procurement No. {line.no} (Row {idx}) is missing required fields: {missing}"
                )
                continue

            # Check for potential conflicts or inconsistencies
            stock_obj = self.env["upmin_stock.stock"]
            stock = stock_obj.search([("stock_no", "=", line.stock_no)], limit=1)
            if stock:
                inconsistent_fields = []
                if stock.description != line.description:
                    inconsistent_fields.append("description")
                if stock.unit.measure_unit != line.unit:
                    inconsistent_fields.append("unit")
                if stock.price != line.unit_cost:
                    inconsistent_fields.append("unit_cost")
                if inconsistent_fields:
                    warnings.append(
                        f"Stock No. {line.stock_no} exists but has inconsistent fields: {', '.join(inconsistent_fields)}"
                    )
                changes.append(
                    f"{line.quantity} {line.unit} ({line.fund_cluster}) will be added to {line.stock_no} - {line.description}."
                )
            else:
                changes.append(
                    f"{line.stock_no} - {line.description} will be added to the database with intial stock of {line.quantity} {line.unit} ({line.fund_cluster})."
                )

        user_error = []
        if len(errors) > 1:
            user_error.extend(errors)
            user_error.append(
                _("=====Please correct the errors above before proceeding.=====\n")
            )
        else:
            user_error.append(
                _("=====No errors found. You can proceed with the changes.=====\n")
            )
        if len(warnings) > 1:
            user_error.extend(warnings)
            user_error.append(
                _("=====Please review the warnings above before proceeding.=====\n")
            )
        if len(changes) > 1:
            user_error.extend(changes)
            user_error.append(
                _("=====The following changes will be applied to the database.=====\n")
            )
        raise UserError(_("\n".join(user_error)))

    def action_apply_changes(self):
        if not self.procurement_data:
            raise UserError(
                _("No procurement data to apply. Please import data first.")
            )

        errors = []
        for idx, line in enumerate(self.procurement_data, start=2):
            missing_fields = self.check_errors(line)
            if missing_fields:
                missing = ",".join(missing_fields)
                errors.append(
                    f"Procurement No. {line.no} (Row {idx}) is missing required fields: {missing}"
                )
        if errors:
            raise UserError(
                _("Cannot apply changes due to the following errors:\n%s")
                % "\n".join(errors)
            )

        for line in self.procurement_data:
            stock_obj = self.env["upmin_stock.stock"]
            stock = stock_obj.search([("stock_no", "=", line.stock_no)], limit=1)
            # Check if unit exists
            unit_obj = self.env["upmin_stock.measure_units"]
            unit = unit_obj.search([("measure_unit", "=", line.unit)], limit=1)
            if not unit:
                # Create new unit if it doesn't exist
                unit = unit_obj.create({"measure_unit": line.unit})
            # Check if fund cluster exists
            fund_cluster_obj = self.env["upmin_stock.fund_cluster"]
            fund_cluster = fund_cluster_obj.search(
                [("name", "=", line.fund_cluster)], limit=1
            )
            if not fund_cluster:
                # Create new fund cluster if it doesn't exist
                fund_cluster = fund_cluster_obj.create({"name": line.fund_cluster})

            if stock:
                # Update existing stock
                stock.write(
                    {
                        "description": line.description,
                        "unit": unit.id,
                        "price": line.unit_cost,
                    }
                )
                # Create replenishment log
                self.env["upmin_stock.replenishment"].create(
                    {
                        "stock_id": stock.id,
                        "procurement_import_id": line.id,
                        "fund_cluster_id": fund_cluster.id,
                        "quantity": line.quantity,
                        "notes": line.remarks,
                    }
                )
            else:
                # Create new stock record
                new_stock = stock_obj.create(
                    {
                        "stock_no": line.stock_no,
                        "description": line.description,
                        "unit": unit.id,
                        "price": line.unit_cost,
                    }
                )
                # Create replenishment log for new stock
                self.env["upmin_stock.replenishment"].create(
                    {
                        "stock_id": new_stock.id,
                        "procurement_import_id": line.id,
                        "fund_cluster_id": fund_cluster.id,
                        "quantity": line.quantity,
                        "notes": line.remarks,
                    }
                )
        # Mark the wizard as applied
        self.applied = True

    def action_download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": "/upmin_stock/static/template/procurement_data_import_template.xlsx",
            "target": "new",
        }

    def unlink(self):
        for item in self.procurement_data:
            item.unlink()

        return super().unlink()
