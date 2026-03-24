from odoo import models, fields, api
import io, base64, re
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


def _strip_html(html):
    """Strip HTML tags, preserving hyperlinks as 'text (url)'."""
    if not html:
        return ""
    # Replace <a href="url">text</a> with "text (url)"
    text = re.sub(
        r'<a\s[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        lambda m: f"{re.sub(r'<[^>]+>', '', m.group(2)).strip()} ({m.group(1)})",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


class RORExportWizard(models.TransientModel):
    _name = "upmin_iso.ror_export_wizard"
    _description = "Export ROR to XLSX"

    ror_id = fields.Many2one(
        comodel_name="upmin_iso.ror",
        string="ROR",
        required=True,
    )
    export_file = fields.Binary("Export File", readonly=True)
    export_filename = fields.Char("File Name")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if active_id and "ror_id" in fields_list:
            res["ror_id"] = active_id
        return res

    def action_export_ror(self):
        ror = self.ror_id
        all_issues = ror.internal_issues + ror.external_issues

        # Collect all review dates across all issues, group by year
        date_dict = {}
        for issue in all_issues:
            for rating in issue.ratings:
                d = rating.review_date
                date_dict.setdefault(d.year, set()).add(d)
        # Sort quarters within each year
        for year in date_dict:
            date_dict[year] = sorted(date_dict[year])

        if not date_dict:
            # No ratings yet — still export with current year, no quarters
            from datetime import date
            date_dict = {}

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # ── Formats ─────────────────────────────────────────────────────────
        def fmt(**kw):
            base = {"font_name": "Calibri", "font_size": 11, "valign": "vcenter", "text_wrap": True}
            base.update(kw)
            return workbook.add_format(base)

        f_default        = fmt()
        f_main_title     = fmt(font_size=14, bold=True)
        f_sub_title      = fmt(font_size=12, bold=True)
        f_header         = fmt(bold=True, align="center", border=1)
        f_gray_bg        = fmt(bold=True, align="center", border=1, bg_color="#D9D9D9")
        f_cell           = fmt(border=1)
        f_cell_center    = fmt(border=1, align="center")
        f_cell_right     = fmt(border=1, align="right")
        f_cell_light     = fmt(border=1, bg_color="#EFEFEF")
        f_cell_light_ctr = fmt(border=1, align="center", bg_color="#EFEFEF")
        f_cell_bold      = fmt(border=1, bold=True)
        f_red_highlight  = workbook.add_format({"bg_color": "#E6B8AF"})

        # ── One sheet per year ───────────────────────────────────────────────
        for year in sorted(date_dict.keys(), reverse=True):
            quarters = date_dict[year]
            sheet = workbook.add_worksheet(str(year))

            # Column widths
            sheet.set_column("A:A", 3.56,  f_default)
            sheet.set_column("B:B", 54.33, f_default)
            sheet.set_column("C:E", 23.22, f_default)
            sheet.set_column("F:H", 21.89, f_default)

            # Title rows
            sheet.write("B1", f"RISKS and OPPORTUNITIES REGISTER (ROR) {year}", f_main_title)
            sheet.write("B2", f"Department: {ror.office.name if ror.office else ''}", f_sub_title)

            # Static headers (rows 3-5, 0-indexed)
            sheet.merge_range("A4:A6", "#",                    f_header)
            sheet.merge_range("B4:B6", "Requirement/Issue",    f_header)
            sheet.merge_range("C4:C6", "Interested Parties",   f_header)
            sheet.merge_range("D4:D6", "Needs and Expectations", f_header)
            sheet.merge_range("E4:E6", "Compliance\nObligations", f_header)
            sheet.merge_range("F4:F6", "Risks (R) /\nOpportunities (O)", f_header)
            sheet.merge_range("G4:G6", "Consequence (C) /\nBenefit (B)",  f_header)
            sheet.merge_range("H4:H6", "Existing Control",     f_header)

            # Quarterly headers (10 cols each, starting at col 8)
            start_col = 8
            for q_date in quarters:
                sheet.set_column(start_col,     start_col + 2, 10.33, f_default)
                sheet.set_column(start_col + 3, start_col + 3, 4.11,  f_default)
                sheet.set_column(start_col + 4, start_col + 4, 7.11,  f_default)
                sheet.set_column(start_col + 5, start_col + 5, 16.89, f_default)
                sheet.set_column(start_col + 6, start_col + 6, 16.78, f_default)
                sheet.set_column(start_col + 7, start_col + 7, 18.89, f_default)
                sheet.set_column(start_col + 8, start_col + 8, 19.11, f_default)
                sheet.set_column(start_col + 9, start_col + 9, 27.89, f_default)

                sheet.merge_range(3, start_col, 3, start_col + 4, "Inherent/Residual Risks", f_header)
                sheet.merge_range(4, start_col, 4, start_col + 1, "O", f_header)
                sheet.write(5, start_col,     "L", f_header)
                sheet.write(5, start_col + 1, "F", f_header)
                sheet.merge_range(4, start_col + 2, 5, start_col + 2, "S",     f_header)
                sheet.merge_range(4, start_col + 3, 5, start_col + 4, "RR/OR", f_header)
                sheet.merge_range(3, start_col + 5, 5, start_col + 6,
                                  "Conclusion\n(Significant / Not Significant)", f_header)
                sheet.merge_range(3, start_col + 7, 5, start_col + 7, "Required Action",   f_header)
                sheet.merge_range(3, start_col + 8, 5, start_col + 8, "Responsible/Date",  f_header)
                # Review date header + status below
                date_str = q_date.strftime("%B %d, %Y")
                sheet.write(3, start_col + 9, f"Review Date:\n{date_str}", f_header)
                sheet.merge_range(4, start_col + 9, 5, start_col + 9, "Status / Results",  f_header)
                start_col += 10

            total_cols = start_col  # total number of columns used

            # ── Helper: write section label row ─────────────────────────────
            def write_section_label(row, label):
                for c in range(total_cols):
                    if c == 1:
                        sheet.write(row, c, label, f_gray_bg)
                    elif c >= 8 and (c - 8) % 10 == 5:
                        # Conclusion two-col merged in data rows — merge blank here too
                        sheet.merge_range(row, c, row, c + 1, None, f_gray_bg)
                    elif c >= 8 and (c - 8) % 10 == 6:
                        continue  # already merged above
                    else:
                        sheet.write(row, c, None, f_gray_bg)

            # ── Helper: write one issue (2 rows) ────────────────────────────
            def write_issue(row, idx, issue, quarters_for_year):
                sheet.merge_range(row, 0, row + 1, 0, idx, f_cell_right)
                sheet.merge_range(row, 1, row + 1, 1, _strip_html(issue.description), f_cell)
                sheet.merge_range(row, 2, row + 1, 2, _strip_html(issue.interested_parties), f_cell)
                sheet.merge_range(row, 3, row + 1, 3, _strip_html(issue.needs_and_exp), f_cell)
                sheet.merge_range(row, 4, row + 1, 4, _strip_html(issue.compliance), f_cell)
                sheet.write_rich_string(row,     5, f_cell_bold, "Risk: ",         f_cell, _strip_html(issue.risks) or " ",         f_cell)
                sheet.write_rich_string(row + 1, 5, f_cell_bold, "Opportunity: ",  f_cell, _strip_html(issue.opportunities) or " ", f_cell)
                sheet.write_rich_string(row,     6, f_cell_bold, "Consequence: ",  f_cell, _strip_html(issue.consequence) or " ",   f_cell)
                sheet.write_rich_string(row + 1, 6, f_cell_bold, "Benefit: ",      f_cell, _strip_html(issue.benefit) or " ",       f_cell)
                sheet.write(row,     7, _strip_html(issue.risk_existing_control), f_cell)
                sheet.write(row + 1, 7, _strip_html(issue.opportunities_existing_control), f_cell)

                col = 8
                for q_date in quarters_for_year:
                    rating = issue.ratings.filtered(lambda r, d=q_date: r.review_date == d)
                    rating = rating[:1]  # take first if somehow multiple

                    if rating:
                        r_like = int(rating.risk_likelihood)        if rating.risk_likelihood else 0
                        o_like = int(rating.opportunity_likelihood)  if rating.opportunity_likelihood else 0
                        r_freq = int(rating.risk_frequency)          if rating.risk_frequency else 0
                        o_freq = int(rating.opportunity_frequency)   if rating.opportunity_frequency else 0
                        c_sev  = int(rating.consequence_severity)    if rating.consequence_severity else 0
                        b_sev  = int(rating.benefit_severity)        if rating.benefit_severity else 0

                        sheet.write(row,     col, r_like, f_cell_center)
                        sheet.write(row + 1, col, o_like, f_cell_center)
                        col += 1
                        sheet.write(row,     col, r_freq, f_cell_center)
                        sheet.write(row + 1, col, o_freq, f_cell_center)
                        col += 1
                        sheet.write(row,     col, c_sev,  f_cell_center)
                        sheet.write(row + 1, col, b_sev,  f_cell_center)
                        col += 1
                        sheet.write(row,     col, "RR:", f_cell)
                        sheet.write(row + 1, col, "OR:", f_cell)
                        col += 1
                        # RR/OR value columns with formula
                        rr_cell = f"={xl_rowcol_to_cell(row, col-4)}*{xl_rowcol_to_cell(row, col-3)}*{xl_rowcol_to_cell(row, col-2)}"
                        or_cell = f"={xl_rowcol_to_cell(row+1, col-4)}*{xl_rowcol_to_cell(row+1, col-3)}*{xl_rowcol_to_cell(row+1, col-2)}"
                        sheet.write_formula(row,     col, rr_cell, f_cell_center, rating.risk_rating)
                        sheet.write_formula(row + 1, col, or_cell, f_cell_center, rating.opportunity_rating)
                        sheet.conditional_format(row, col, row + 1, col, {
                            "type": "cell", "criteria": ">=", "value": 27,
                            "format": f_red_highlight,
                        })
                        col += 1
                        risk_conc = "Significant" if rating.risk_conclusion == "significant" else "Not Significant"
                        opp_conc  = "Significant" if rating.opportunity_conclusion == "significant" else "Not Significant"
                        sheet.merge_range(row,     col, row,     col + 1, risk_conc, f_cell_center)
                        sheet.merge_range(row + 1, col, row + 1, col + 1, opp_conc,  f_cell_center)
                        col += 2
                        sheet.write(row,     col, rating.risk_required_action or "",        f_cell)
                        sheet.write(row + 1, col, rating.opportunity_required_action or "", f_cell)
                        col += 1
                        r_date = rating.risk_due_date.strftime("%B %d, %Y") if rating.risk_due_date else ""
                        o_date = rating.opportunity_due_date.strftime("%B %d, %Y") if rating.opportunity_due_date else ""
                        sheet.write(row,     col, f"{rating.risk_responsible or ''}/{r_date}",        f_cell_center)
                        sheet.write(row + 1, col, f"{rating.opportunity_responsible or ''}/{o_date}", f_cell_center)
                        col += 1
                        sheet.write(row,     col, _strip_html(rating.risk_status),        f_cell_light)
                        sheet.write(row + 1, col, _strip_html(rating.opportunity_status), f_cell_light)
                        col += 1
                    else:
                        # Empty quarter
                        sheet.write(row,     col, None, f_cell_center)
                        sheet.write(row + 1, col, None, f_cell_center)
                        col += 1
                        sheet.write(row,     col, None, f_cell_center)
                        sheet.write(row + 1, col, None, f_cell_center)
                        col += 1
                        sheet.write(row,     col, None, f_cell_center)
                        sheet.write(row + 1, col, None, f_cell_center)
                        col += 1
                        sheet.write(row,     col, "RR:", f_cell)
                        sheet.write(row + 1, col, "OR:", f_cell)
                        col += 1
                        sheet.write(row,     col, None, f_cell_center)
                        sheet.write(row + 1, col, None, f_cell_center)
                        col += 1
                        sheet.merge_range(row,     col, row,     col + 1, "-", f_cell_center)
                        sheet.merge_range(row + 1, col, row + 1, col + 1, "-", f_cell_center)
                        col += 2
                        sheet.write(row,     col, "-", f_cell_center)
                        sheet.write(row + 1, col, "-", f_cell_center)
                        col += 1
                        sheet.write(row,     col, "-", f_cell_center)
                        sheet.write(row + 1, col, "-", f_cell_center)
                        col += 1
                        sheet.write(row,     col, "-", f_cell_light_ctr)
                        sheet.write(row + 1, col, "-", f_cell_light_ctr)
                        col += 1

            # Internal Issues section (row index 6 = Excel row 7)
            curr_row = 6
            write_section_label(curr_row, "Internal Issues")
            curr_row += 1
            for idx, issue in enumerate(ror.internal_issues, 1):
                write_issue(curr_row, idx, issue, quarters)
                curr_row += 2

            # External Issues section
            write_section_label(curr_row, "External Issues")
            curr_row += 1
            for idx, issue in enumerate(ror.external_issues, 1):
                write_issue(curr_row, idx, issue, quarters)
                curr_row += 2

        workbook.close()
        file_b64 = base64.b64encode(output.getvalue())
        office_name = ror.office.name if ror.office else "ROR"
        self.write({
            "export_file": file_b64,
            "export_filename": f"Risks and Opportunities Register - {office_name}.xlsx",
        })

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/?model={self._name}&id={self.id}"
                f"&field=export_file&filename_field=export_filename&download=true"
            ),
            "target": "self",
        }
