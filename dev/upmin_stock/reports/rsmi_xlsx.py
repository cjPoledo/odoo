from odoo import models


class RsmiXlsx(models.AbstractModel):
    _name = "report.upmin_stock.report_rsmi"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, partners):
        font = "Times New Roman"
        sheet = workbook.add_worksheet("RSMI.2")
        # Set page layout: A4, 60% scale, hide gridlines
        sheet.set_paper(9)  # 9 = A4
        sheet.set_print_scale(60)
        sheet.hide_gridlines(2)
        # Set margins: top/bottom=0.75, left/right=0.25
        sheet.set_margins(left=0.25, right=0.25, top=0.75, bottom=0.75)

        # Define formats
        workbook.formats[0].set_font_name(font)
        workbook.formats[0].set_font_size(12)
        workbook.formats[0].set_text_wrap()
        appendix = workbook.add_format(
            {"italic": True, "font_size": 18, "font_name": font, "align": "right"}
        )
        main_title = workbook.add_format(
            {"bold": True, "font_size": 14, "font_name": font, "align": "center"}
        )
        default = workbook.add_format(
            {"font_size": 11, "font_name": font, "align": "left"}
        )
        bold = workbook.add_format(
            {"bold": True, "font_size": 11, "font_name": font, "align": "left"}
        )
        center_bold = workbook.add_format(
            {
                "bold": True,
                "font_size": 11,
                "font_name": font,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 2,
            }
        )
        center_italic = workbook.add_format(
            {
                "italic": True,
                "font_size": 11,
                "font_name": font,
                "align": "center",
                "valign": "vcenter",
                "border": 2,
            }
        )
        entry = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "left",
                "valign": "vtop",
                "text_wrap": True,
                "left": 2,
                "right": 2,
            }
        )
        entry_center = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "center",
                "valign": "vtop",
                "text_wrap": True,
                "left": 2,
                "right": 2,
            }
        )
        entry_center_underline_caps = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "center",
                "valign": "vtop",
                "text_wrap": True,
                "left": 2,
                "right": 2,
                "underline": 1,
            }
        )
        entry_center_underline_caps_left_border = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "center",
                "valign": "vtop",
                "text_wrap": True,
                "left": 2,
                "underline": 1,
            }
        )
        entry_top_border = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "left",
                "valign": "vtop",
                "text_wrap": True,
                "top": 2,
                "left": 2,
                "right": 2,
            }
        )
        entry_bottom_border = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "left",
                "valign": "vtop",
                "text_wrap": True,
                "bottom": 2,
                "left": 2,
                "right": 2,
            }
        )
        entry_left_border_only = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "center",
                "valign": "vtop",
                "text_wrap": True,
                "left": 2,
            }
        )
        entry_right_border_only = workbook.add_format(
            {
                "font_size": 12,
                "font_name": font,
                "align": "center",
                "valign": "vtop",
                "text_wrap": True,
                "right": 2,
            }
        )
        date_format = workbook.add_format(
            {
                "num_format": "mmmm d, yyyy",
                "bold": True,
                "align": "left",
                "valign": "vbottom",
                "font_name": font,
            }
        )

        # Set column widths
        sheet.set_column("A:A", 14.3)
        sheet.set_column("B:B", 16.7)
        sheet.set_column("C:C", 15.4)
        sheet.set_column("D:D", 45.3)
        sheet.set_column("E:E", 8.2)
        sheet.set_column("F:F", 11.7)
        sheet.set_column("G:G", 13.2)
        sheet.set_column("H:H", 20)

        # Appendix
        sheet.write("H1", "Appendix 64", appendix)
        # Title
        sheet.merge_range(
            "A3:H3", "REPORT OF SUPPLIES AND MATERIALS ISSUED", main_title
        )
        # Top Data
        sheet.write("A6", "Entity Name:", bold)
        sheet.merge_range("B6:E6", partners.entity_name, default)
        sheet.write("G6", "Serial No.:", bold)
        sheet.write("H6", partners.serial_no, bold)
        sheet.write("A7", "Fund Cluster:", bold)
        sheet.merge_range("B7:E7", partners.fund_cluster.name, bold)
        sheet.write("G7", "Date:", bold)
        sheet.write("H7", partners.date, date_format)

        # Headers
        sheet.merge_range(
            "A9:F9",
            "To be filled up by the Supply and/or Property Division/Unit",
            center_italic,
        )
        sheet.merge_range(
            "G9:H9", "To be filled up by the Receiving Division/Unit", center_italic
        )
        sheet.merge_range("A10:A11", "RIS No.", center_bold)
        sheet.merge_range("B10:B11", "Responsibility Center Code", center_bold)
        sheet.merge_range("C10:C11", "Stock No.", center_bold)
        sheet.merge_range("D10:D11", "Item", center_bold)
        sheet.merge_range("E10:E11", "Unit", center_bold)
        sheet.merge_range("F10:F11", "Quantity Issued", center_bold)
        sheet.merge_range("G10:G11", "Unit Cost", center_bold)
        sheet.merge_range("H10:H11", "Amount", center_bold)

        # Data Rows
        row = 11
        for issuance in partners.issuances:
            sheet.write(row, 0, issuance.ris_no or "-", entry_center)
            sheet.write(row, 1, issuance.rc_code.rc_code or "-", entry)
            sheet.write(row, 2, issuance.stock_no.stock_no or "-", entry)
            sheet.write(row, 3, issuance.stock_no.description or "-", entry)
            sheet.write(
                row, 4, issuance.stock_no.unit.measure_unit or "-", entry_center
            )
            sheet.write(row, 5, issuance.quantity_issued or 0, entry_center)
            sheet.write(row, 6, "", entry)
            sheet.write(row, 7, "", entry)
            row += 1

        # 5 line spaces
        for _ in range(5):
            sheet.write(row, 0, "", entry_center)
            sheet.write(row, 1, "", entry)
            sheet.write(row, 2, "", entry)
            sheet.write(row, 3, "", entry)
            sheet.write(row, 4, "", entry_center)
            sheet.write(row, 5, "", entry_center)
            sheet.write(row, 6, "", entry)
            sheet.write(row, 7, "", entry)
            row += 1

        # Recapitulation
        sheet.write(row, 0, "", entry_center)
        sheet.merge_range(f"B{row + 1}:C{row + 1}", "Recapitulation:", center_bold)
        sheet.write(row, 3, "", entry)
        sheet.write(row, 4, "", entry_center)
        sheet.merge_range(f"F{row + 1}:H{row + 1}", "Recapitulation:", center_bold)
        row += 1
        sheet.write(row, 0, "", entry_center)
        sheet.write(row, 1, "Stock No.", center_bold)
        sheet.write(row, 2, "Quantity", center_bold)
        sheet.write(row, 3, "", entry)
        sheet.write(row, 4, "", entry_center)
        sheet.write(row, 5, "Unit Cost", center_bold)
        sheet.write(row, 6, "Total Cost", center_bold)
        sheet.write(row, 7, "UACS Object Code", center_bold)
        row += 1
        for issuance in partners.issuances:
            sheet.write(row, 0, "", entry_center)
            sheet.write(row, 1, issuance.stock_no.stock_no or "-", entry)
            sheet.write(row, 2, issuance.quantity_issued or 0, entry_center)
            sheet.write(row, 3, "", entry)
            sheet.write(row, 4, "", entry_center)
            sheet.write(row, 5, "", entry)
            sheet.write(row, 6, "", entry)
            sheet.write(row, 7, "", entry)
            row += 1

        # 5 line spaces
        for _ in range(5):
            sheet.write(row, 0, "", entry_center)
            sheet.write(row, 1, "", entry)
            sheet.write(row, 2, "", entry)
            sheet.write(row, 3, "", entry)
            sheet.write(row, 4, "", entry_center)
            sheet.write(row, 5, "", entry_center)
            sheet.write(row, 6, "", entry)
            sheet.write(row, 7, "", entry)
            row += 1

        # Footer
        sheet.merge_range(f"A{row + 1}:E{row + 1}", "", entry_top_border)
        sheet.merge_range(f"F{row + 1}:H{row + 1}", "Posted by:", entry_top_border)
        sheet.merge_range(
            f"A{row + 2}:E{row + 2}",
            "         I hereby certify to the correctness of the above information.",
            entry,
        )
        sheet.merge_range(f"F{row + 2}:H{row + 2}", "", entry)
        sheet.merge_range(
            f"A{row + 3}:E{row + 3}",
            partners.supply_custodian.name,
            entry_center_underline_caps,
        )
        sheet.merge_range(
            f"F{row + 3}:G{row + 3}",
            partners.accounting_staff,
            entry_center_underline_caps_left_border,
        )
        sheet.write(f"H{row + 3}", "", entry_right_border_only)
        sheet.merge_range(
            f"A{row + 4}:E{row + 4}",
            "Signature over Printed Name of Supply and/or Property Custodian",
            entry_center,
        )
        sheet.merge_range(
            f"F{row + 4}:G{row + 4}",
            "Signature over Printed Name of Designated Accounting Staff",
            entry_left_border_only,
        )
        sheet.write(f"H{row + 4}", "Date", entry_right_border_only)
        sheet.merge_range(
            f"A{row + 5}:E{row + 5}",
            "",
            entry_bottom_border,
        )
        sheet.merge_range(
            f"F{row + 5}:H{row + 5}",
            "",
            entry_bottom_border,
        )
