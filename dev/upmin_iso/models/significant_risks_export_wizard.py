from odoo import models, fields
import io, base64, re
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell


def _strip_html(html):
    if not html:
        return ""
    text = re.sub(
        r'<a\s[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
        lambda m: f"{re.sub(r'<[^>]+>', '', m.group(2)).strip()} ({m.group(1)})",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()


QUARTER_NAMES = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}

# Static columns: A=# B=Office C=Issue D=IntParties E=Needs F=Compliance G=Risk/Opp H=Cons/Ben I=ExistCtrl
# Quarterly block starts at col 9 (J): L F S RR: RR Conc(x2) ReqAction Responsible Status
_Q_START = 9
_Q_COLS = 10  # cols per quarter block


class SignificantRisksExportWizard(models.TransientModel):
    _name = "upmin_iso.significant_risks_export_wizard"
    _description = "Export Significant Risks to XLSX"

    export_file = fields.Binary("Export File", readonly=True)
    export_filename = fields.Char("File Name")

    def action_export(self):
        ratings = self.env["upmin_iso.ror_rating"].search(
            [("risk_conclusion", "=", "significant")],
            order="review_date, office_name",
        )

        # Group by review_date
        date_groups = {}
        for r in ratings:
            date_groups.setdefault(r.review_date, []).append(r)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        def fmt(**kw):
            base = {"font_name": "Calibri", "font_size": 11, "valign": "vcenter", "text_wrap": True}
            base.update(kw)
            return workbook.add_format(base)

        f_default     = fmt()
        f_main_title  = fmt(font_size=14, bold=True)
        f_header      = fmt(bold=True, align="center", border=1)
        f_gray_bg     = fmt(bold=True, align="center", border=1, bg_color="#D9D9D9")
        f_cell        = fmt(border=1)
        f_cell_center = fmt(border=1, align="center")
        f_cell_right  = fmt(border=1, align="right")
        f_cell_light  = fmt(border=1, bg_color="#EFEFEF")
        f_cell_lc     = fmt(border=1, align="center", bg_color="#EFEFEF")
        f_cell_bold   = fmt(border=1, bold=True)
        f_red_hl      = workbook.add_format({"bg_color": "#E6B8AF"})

        total_cols = _Q_START + _Q_COLS  # 19 columns total (one quarter per sheet)

        for q_date in sorted(date_groups.keys(), reverse=True):
            q_name = QUARTER_NAMES.get(q_date.month, "Q?")
            sheet_name = f"{q_name} {q_date.year}"
            sheet = workbook.add_worksheet(sheet_name)

            # Column widths (mirror ROR template, +1 for Office col)
            sheet.set_column(0, 0,  3.56,  f_default)   # A: #
            sheet.set_column(1, 1,  20.00, f_default)   # B: Office
            sheet.set_column(2, 2,  40.00, f_default)   # C: Issue
            sheet.set_column(3, 5,  23.22, f_default)   # D-F: Parties/Needs/Compliance
            sheet.set_column(6, 8,  21.89, f_default)   # G-I: Risk/Cons/Control
            sheet.set_column(9,  11, 10.33, f_default)  # J-L: L F S
            sheet.set_column(12, 12, 4.11,  f_default)  # M: RR: label
            sheet.set_column(13, 13, 7.11,  f_default)  # N: RR value
            sheet.set_column(14, 15, 16.89, f_default)  # O-P: Conclusion
            sheet.set_column(16, 16, 18.89, f_default)  # Q: Required Action
            sheet.set_column(17, 17, 19.11, f_default)  # R: Responsible/Date
            sheet.set_column(18, 18, 27.89, f_default)  # S: Status/Results

            # Title
            sheet.write(0, 1, f"SIGNIFICANT RISKS (QUARTERLY) — {sheet_name}", f_main_title)

            # Headers (rows 3-5, 0-indexed = Excel rows 4-6)
            sheet.merge_range("A4:A6", "#",                         f_header)
            sheet.merge_range("B4:B6", "Office",                    f_header)
            sheet.merge_range("C4:C6", "Requirement/Issue",         f_header)
            sheet.merge_range("D4:D6", "Interested Parties",        f_header)
            sheet.merge_range("E4:E6", "Needs and Expectations",    f_header)
            sheet.merge_range("F4:F6", "Compliance\nObligations",   f_header)
            sheet.merge_range("G4:G6", "Risks (R) /\nOpportunities (O)", f_header)
            sheet.merge_range("H4:H6", "Consequence (C) /\nBenefit (B)", f_header)
            sheet.merge_range("I4:I6", "Existing Control",          f_header)

            sc = _Q_START
            sheet.merge_range(3, sc, 3, sc + 4, "Inherent/Residual Risks",              f_header)
            sheet.merge_range(4, sc, 4, sc + 1, "O",                                    f_header)
            sheet.write(5, sc,     "L",                                                  f_header)
            sheet.write(5, sc + 1, "F",                                                  f_header)
            sheet.merge_range(4, sc + 2, 5, sc + 2, "S",                                f_header)
            sheet.merge_range(4, sc + 3, 5, sc + 4, "RR/OR",                            f_header)
            sheet.merge_range(3, sc + 5, 5, sc + 6,
                              "Conclusion\n(Significant / Not Significant)",             f_header)
            sheet.merge_range(3, sc + 7, 5, sc + 7, "Required Action",                  f_header)
            sheet.merge_range(3, sc + 8, 5, sc + 8, "Responsible/Date",                 f_header)
            date_str = q_date.strftime("%B %d, %Y")
            sheet.write(3, sc + 9, f"Review Date:\n{date_str}",                         f_header)
            sheet.merge_range(4, sc + 9, 5, sc + 9, "Status / Results",                 f_header)

            # Section label helper
            def write_section_label(row, label):
                for c in range(total_cols):
                    if c == 2:
                        sheet.write(row, c, label, f_gray_bg)
                    elif c >= _Q_START and (c - _Q_START) % _Q_COLS == 5:
                        sheet.merge_range(row, c, row, c + 1, None, f_gray_bg)
                    elif c >= _Q_START and (c - _Q_START) % _Q_COLS == 6:
                        continue
                    else:
                        sheet.write(row, c, None, f_gray_bg)

            # Issue row helper
            def write_issue(row, idx, rating):
                issue = rating.issue
                sheet.merge_range(row, 0, row + 1, 0, idx, f_cell_right)
                sheet.merge_range(row, 1, row + 1, 1, rating.office_name or "", f_cell)
                sheet.merge_range(row, 2, row + 1, 2, _strip_html(issue.description), f_cell)
                sheet.merge_range(row, 3, row + 1, 3, _strip_html(issue.interested_parties), f_cell)
                sheet.merge_range(row, 4, row + 1, 4, _strip_html(issue.needs_and_exp), f_cell)
                sheet.merge_range(row, 5, row + 1, 5, _strip_html(issue.compliance), f_cell)
                sheet.write_rich_string(row,     6, f_cell_bold, "Risk: ",        f_cell, _strip_html(issue.risks) or " ",        f_cell)
                sheet.write_rich_string(row + 1, 6, f_cell_bold, "Opportunity: ", f_cell, _strip_html(issue.opportunities) or " ", f_cell)
                sheet.write_rich_string(row,     7, f_cell_bold, "Consequence: ", f_cell, _strip_html(issue.consequence) or " ",   f_cell)
                sheet.write_rich_string(row + 1, 7, f_cell_bold, "Benefit: ",     f_cell, _strip_html(issue.benefit) or " ",       f_cell)
                sheet.write(row,     8, _strip_html(issue.risk_existing_control), f_cell)
                sheet.write(row + 1, 8, _strip_html(issue.opportunities_existing_control), f_cell)

                col = _Q_START
                r_like = int(rating.risk_likelihood)       if rating.risk_likelihood else 0
                o_like = int(rating.opportunity_likelihood) if rating.opportunity_likelihood else 0
                r_freq = int(rating.risk_frequency)         if rating.risk_frequency else 0
                o_freq = int(rating.opportunity_frequency)  if rating.opportunity_frequency else 0
                c_sev  = int(rating.consequence_severity)   if rating.consequence_severity else 0
                b_sev  = int(rating.benefit_severity)       if rating.benefit_severity else 0

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
                rr_f = f"={xl_rowcol_to_cell(row, col-4)}*{xl_rowcol_to_cell(row, col-3)}*{xl_rowcol_to_cell(row, col-2)}"
                or_f = f"={xl_rowcol_to_cell(row+1, col-4)}*{xl_rowcol_to_cell(row+1, col-3)}*{xl_rowcol_to_cell(row+1, col-2)}"
                sheet.write_formula(row,     col, rr_f, f_cell_center, rating.risk_rating)
                sheet.write_formula(row + 1, col, or_f, f_cell_center, rating.opportunity_rating)
                sheet.conditional_format(row, col, row + 1, col, {
                    "type": "cell", "criteria": ">=", "value": 27, "format": f_red_hl,
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

            # Split by issue type
            quarter_ratings = date_groups[q_date]
            internal = [r for r in quarter_ratings if r.issue.swot_type == "W"]
            external = [r for r in quarter_ratings if r.issue.swot_type == "T"]

            curr_row = 6
            write_section_label(curr_row, "Internal Issues")
            curr_row += 1
            for idx, rating in enumerate(internal, 1):
                write_issue(curr_row, idx, rating)
                curr_row += 2

            write_section_label(curr_row, "External Issues")
            curr_row += 1
            for idx, rating in enumerate(external, 1):
                write_issue(curr_row, idx, rating)
                curr_row += 2

        workbook.close()
        file_b64 = base64.b64encode(output.getvalue())
        self.write({
            "export_file": file_b64,
            "export_filename": "Significant Risks (Quarterly).xlsx",
        })

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/?model={self._name}&id={self.id}"
                f"&field=export_file&filename_field=export_filename&download=true"
            ),
            "target": "self",
        }
