from odoo import models, fields, api
import io, base64
import xlsxwriter


class RORExportWizard(models.TransientModel):
    _name = "upmin_iso.ror_export_wizard"
    _description = "Export ROR"

    office = fields.Many2one(
        comodel_name="upmin_iso.office",
        string="Office",
        required=True,
        domain=lambda self: self._get_office_domain(),
    )
    export_file = fields.Binary("Export File", readonly=True)
    export_filename = fields.Char("File Name")

    @api.model
    def _get_office_domain(self):
        if self.env.user.has_group("upmin_iso.group_iso_staff"):
            return []
        return [("doc_controllers", "in", self.env.user.partner_id.id)]

    def action_export_ror(self):
        # fetch review dates
        review_dates = (
            self.env["upmin_iso.review_period"].search(domain=[]).mapped("review_date")
        )
        date_dict = {}
        for date in review_dates:
            date_dict.setdefault(date.year, []).append(date)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # formats
        format_default = workbook.add_format(
            {
                "font_name": "Calibri",
                "font_size": 11,
                "valign": "vcenter",
                "text_wrap": True,
            }
        )
        format_main_title = workbook.add_format(
            {"font_name": "Calibri", "font_size": 14, "bold": True}
        )
        format_sub_title = workbook.add_format(
            {"font_name": "Calibri", "font_size": 12, "bold": True}
        )
        format_table_header = workbook.add_format(
            {
                "font_name": "Calibri",
                "font_size": 11,
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        )
        format_red_underline_text = workbook.add_format(
            {
                "font_name": "Calibri",
                "font_size": 11,
                "font_color": "red",
                "underline": True,
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        )
        format_gray_bg = workbook.add_format(
            {
                "font_name": "Calibri",
                "font_size": 11,
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
                "bg_color": "#D9D9D9",
            }
        )
        format_default_table = workbook.add_format(
            {
                "font_name": "Calibri",
                "font_size": 11,
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        )
        format_right_align_table = workbook.add_format(
            {
                "font_name": "Calibri",
                "font_size": 11,
                "align": "right",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
            }
        )

        for year in sorted(date_dict.keys(), reverse=True):
            sheet = workbook.add_worksheet(str(year))
            # column width
            sheet.set_column("A:A", 3.56, format_default)
            sheet.set_column("B:B", 54.33, format_default)
            sheet.set_column("C:E", 23.22, format_default)
            sheet.set_column("F:H", 21.89, format_default)

            sheet.write(
                "B1",
                f"RISKS and OPPORTUNITIES REGISTER (ROR) {year}",
                format_main_title,
            )
            sheet.write("B2", f"Department: {self.office.name}", format_sub_title)

            # headers
            sheet.merge_range("A4:A6", "#", format_table_header)
            sheet.merge_range("B4:B6", "Requirement/Issue", format_table_header)
            sheet.merge_range("C4:C6", "Interested Parties", format_table_header)
            sheet.merge_range("D4:D6", "Needs and Expectations", format_table_header)
            sheet.merge_range("E4:E6", "Compliance\nObligations", format_table_header)
            sheet.merge_range(
                "F4:F6", "Risks (R) /\nOpportunities (O) ", format_table_header
            )
            sheet.merge_range(
                "G4:G6", "Consequence (C) /\nBenefit (B)", format_table_header
            )
            sheet.merge_range("H4:H6", "Existing Control", format_table_header)

            start_col = 8
            for date in date_dict[year]:
                # set column size
                sheet.set_column(start_col, start_col + 2, 10.33, format_default)
                sheet.set_column(start_col + 3, start_col + 3, 4.11, format_default)
                sheet.set_column(start_col + 4, start_col + 4, 7.11, format_default)
                sheet.set_column(start_col + 5, start_col + 5, 16.89, format_default)
                sheet.set_column(start_col + 6, start_col + 6, 16.78, format_default)
                sheet.set_column(start_col + 7, start_col + 7, 18.89, format_default)
                sheet.set_column(start_col + 8, start_col + 8, 19.11, format_default)
                sheet.set_column(start_col + 9, start_col + 9, 27.89, format_default)

                # put headers
                sheet.merge_range(
                    3,
                    start_col,
                    3,
                    start_col + 4,
                    "Inherent/Residual Risks",
                    format_table_header,
                )
                sheet.merge_range(
                    4, start_col, 4, start_col + 1, "O", format_table_header
                )
                sheet.write(5, start_col, "L", format_table_header)
                sheet.write(5, start_col + 1, "F", format_table_header)
                sheet.merge_range(
                    4, start_col + 2, 5, start_col + 2, "S", format_table_header
                )
                sheet.merge_range(
                    4, start_col + 3, 5, start_col + 4, "RR/OR", format_table_header
                )
                sheet.merge_range(
                    3,
                    start_col + 5,
                    5,
                    start_col + 6,
                    "Conclusion\n(Significant /  Not Significant)",
                    format_table_header,
                )
                sheet.merge_range(
                    3,
                    start_col + 7,
                    5,
                    start_col + 7,
                    "Required Action",
                    format_table_header,
                )
                sheet.merge_range(
                    3,
                    start_col + 8,
                    5,
                    start_col + 8,
                    "Responsible/Date",
                    format_table_header,
                )
                date_str = date.strftime("%B %d, %Y")
                sheet.write(
                    3, start_col + 9, f"Review Date:\n{date_str}", format_table_header
                )
                sheet.write_rich_string(
                    3,
                    start_col + 9,
                    "Review Date:\n",
                    format_red_underline_text,
                    date_str,
                    format_table_header,
                )
                sheet.merge_range(
                    4,
                    start_col + 9,
                    5,
                    start_col + 9,
                    "Status / Results",
                    format_table_header,
                )
                start_col += 10

            # Add internal issues
            for i in range(start_col):
                if i == 1:
                    sheet.write(6, i, "Internal Issues", format_gray_bg)
                elif i >= 13 and (i - 13) % 10 == 0:
                    sheet.merge_range(6, i, 6, i + 1, None, format_gray_bg)
                elif i >= 13 and (i - 13) % 10 == 1:
                    continue
                else:
                    sheet.write(6, i, None, format_gray_bg)
            internal_issues = self.env["upmin_iso.ror"].search(
                domain=[
                    "&",
                    ("office", "=", self.office.id),
                    ("issue_type", "=", "internal"),
                ]
            )
            curr_row = 7
            for i, i_issue in enumerate(internal_issues, 1):
                sheet.merge_range(
                    curr_row, 0, curr_row + 1, 0, i, format_right_align_table
                )
                sheet.merge_range(
                    curr_row, 1, curr_row + 1, 1, i_issue.issue, format_default_table
                )
                sheet.merge_range(
                    curr_row,
                    2,
                    curr_row + 1,
                    2,
                    i_issue.interested_parties,
                    format_default_table,
                )
                sheet.merge_range(
                    curr_row,
                    3,
                    curr_row + 1,
                    3,
                    i_issue.needs_and_exp,
                    format_default_table,
                )
                sheet.merge_range(
                    curr_row,
                    4,
                    curr_row + 1,
                    4,
                    i_issue.compliance,
                    format_default_table,
                )
                sheet.write(curr_row, 5, f"Risk: {i_issue.risks}", format_default_table)
                sheet.write(
                    curr_row + 1,
                    5,
                    f"Opportunity: {i_issue.opportunities}",
                    format_default_table,
                )
                sheet.write(
                    curr_row,
                    6,
                    f"Consequence: {i_issue.consequence}",
                    format_default_table,
                )
                sheet.write(
                    curr_row + 1, 6, f"Benefit: {i_issue.benefit}", format_default_table
                )
                sheet.write(
                    curr_row, 7, i_issue.risk_existing_control, format_default_table
                )
                sheet.write(
                    curr_row + 1,
                    7,
                    i_issue.opportunities_existing_control,
                    format_default_table,
                )
                curr_row += 2

                # for date in date_dict[year]:
                #     rating = i_issue.ratings.filtered(
                #         lambda r: r.review_date.review_date == date
                #     )


            # Add external issues
            for i in range(start_col):
                if i == 1:
                    sheet.write(curr_row, i, "External Issues", format_gray_bg)
                elif i >= 13 and (i - 13) % 10 == 0:
                    sheet.merge_range(
                        curr_row, i, curr_row, i + 1, None, format_gray_bg
                    )
                elif i >= 13 and (i - 13) % 10 == 1:
                    continue
                else:
                    sheet.write(curr_row, i, None, format_gray_bg)

        workbook.close()
        data_bytes = output.getvalue()
        output.close()
        file_b64 = base64.b64encode(data_bytes)
        self.write(
            {
                "export_file": file_b64,
                "export_filename": f"Risks and Opportunities Register - {self.office.name}.xlsx",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}&field=export_file&filename_field=export_filename&download=true",
            "target": "self",
        }
