from odoo import models, fields, api
import io, base64, re
import xlsxwriter


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


class SWOTTOWSExportWizard(models.TransientModel):
    _name = "upmin_iso.swot_tows_export_wizard"
    _description = "Export SWOT/TOWS to XLSX"

    swot_id = fields.Many2one(
        comodel_name="upmin_iso.swot",
        string="SWOT",
        required=True,
    )
    export_file = fields.Binary("Export File", readonly=True)
    export_filename = fields.Char("File Name")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        active_model = self.env.context.get("active_model")
        if active_id and "swot_id" in fields_list:
            if active_model == "upmin_iso.swot":
                res["swot_id"] = active_id
            elif active_model == "upmin_iso.tows":
                tows = self.env["upmin_iso.tows"].browse(active_id)
                res["swot_id"] = tows.swot.id
        return res

    def action_export(self):
        swot = self.swot_id
        tows = self.env["upmin_iso.tows"].search([("swot", "=", swot.id)], limit=1)

        s_lines = sorted(swot.strengths, key=lambda l: l.label or "")
        w_lines = sorted(swot.weaknesses, key=lambda l: l.label or "")
        o_lines = sorted(swot.opportunities, key=lambda l: l.label or "")
        t_lines = sorted(swot.threats, key=lambda l: l.label or "")

        so_lines = sorted(tows.so, key=lambda l: l.id) if tows else []
        wo_lines = sorted(tows.wo, key=lambda l: l.id) if tows else []
        st_lines = sorted(tows.st, key=lambda l: l.id) if tows else []
        wt_lines = sorted(tows.wt, key=lambda l: l.id) if tows else []

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        # ── Formats matching the template exactly ─────────────────────────────
        # Template uses Arial 11 for headers/labels, Arial Narrow 11 for data cells
        thin = {"border": 1}  # xlsxwriter border=1 → thin

        def fmt(**kw):
            return workbook.add_format(kw)

        # Title row: Arial 11 bold, no border, no bg (same as A1 in template)
        f_title = fmt(font_name="Arial", font_size=11, bold=True)

        # Subtitle (office + year): Arial 11, not bold — we add below the title
        f_subtitle = fmt(font_name="Arial", font_size=11, bold=False)

        # Section label cells — bold Arial 11, thin border all sides
        # A3 "Internal": right-aligned, border L/R/T (no bottom in template)
        f_internal = fmt(
            font_name="Arial", font_size=11, bold=True,
            border=1, align="right",
        )

        # "Strengths", "Weaknesses" headers: Arial 11 bold, thin border all sides
        f_header = fmt(font_name="Arial", font_size=11, bold=True, border=1)

        # "External": Arial 11 bold, border L/R/B (no top), all sides in our dynamic version = border=1
        f_external = fmt(font_name="Arial", font_size=11, bold=True, border=1)

        # "Opportunities", "Threats" section headers: Arial 11 bold, border=1
        f_sec_header = fmt(font_name="Arial", font_size=11, bold=True, border=1)

        # Data label cells (S1/W1/O1/T1 column A): Arial Narrow 11, border=1, no bold
        f_data_label = fmt(font_name="Arial Narrow", font_size=11, bold=False, border=1)

        # Data content cells (description text): Arial Narrow 11, border=1, no bold, wrap
        f_data = fmt(font_name="Arial Narrow", font_size=11, bold=False, border=1, text_wrap=True)

        # Empty bordered cell for column A on S/W rows (same style as A4-A8 in template)
        f_a_sw = fmt(font_name="Arial", font_size=11, bold=False, border=1)

        # Blank bordered cell for B9/C9 (row after "External" in template has thin border)
        f_blank_bordered = fmt(font_name="Arial", font_size=11, bold=False, border=1)

        # Separator blank row (A16/B16/C16): Arial 11, border=1
        f_sep = fmt(font_name="Arial", font_size=11, bold=False, border=1)

        # Steps section: Arial 11, no border, gray bg FFD9D9D9
        f_steps_bold = fmt(font_name="Arial", font_size=11, bold=True, bg_color="#D9D9D9")
        f_steps = fmt(font_name="Arial", font_size=11, bold=False, bg_color="#D9D9D9")
        f_steps_narrow = fmt(font_name="Arial Narrow", font_size=11, bold=False, bg_color="#D9D9D9")

        # ── Sheet setup ───────────────────────────────────────────────────────
        sheet = workbook.add_worksheet("SWOT TOWS")
        # Column widths from template: A=28.29, B=27, C=32.29
        sheet.set_column(0, 0, 28.29)
        sheet.set_column(1, 1, 27.0)
        sheet.set_column(2, 2, 32.29)

        office_name = swot.office.name if swot.office else ""
        year = swot.year or ""

        # ── Row 0 (A1): "SWOT ANALYSIS" — Arial 11 bold ──────────────────────
        sheet.write(0, 0, "SWOT ANALYSIS", f_title)

        # ── Row 1 (A2): Office + Year subtitle ───────────────────────────────
        sheet.write(1, 0, f"{office_name} - {year}", f_subtitle)

        # ── Row 2 (A3): blank ─────────────────────────────────────────────────

        # ── Row 3 (A3 equiv): Internal / Strengths / Weaknesses ──────────────
        # Template A3: "Internal", right-aligned, bold, border L/R/T only
        # We use border=1 (all sides) for simplicity in a dynamic layout
        row = 3
        sheet.write(row, 0, "Internal", f_internal)
        sheet.write(row, 1, "Strengths", f_header)
        sheet.write(row, 2, "Weaknesses", f_header)
        row += 1

        # ── S/W data rows ─────────────────────────────────────────────────────
        # Template: col A has left+right border, no value (A4-A8)
        #           col B: "S1", "S2"... Arial Narrow 11
        #           col C: "W1", "W2"... Arial Narrow 11
        # We split: label cell (SN/WN) + description in same cell, matching the
        # template's "S1" label — but in the template the label IS the content.
        # Since we have actual descriptions, we prefix with the label: "S1  <desc>"
        max_sw = max(len(s_lines), len(w_lines), 1)
        for i in range(max_sw):
            if i < len(s_lines):
                s_label = s_lines[i].label or f"S{i+1}"
                s_desc = _strip_html(s_lines[i].description)
                s_val = f"{s_label}  {s_desc}" if s_desc else s_label
            else:
                s_val = ""

            if i < len(w_lines):
                w_label = w_lines[i].label or f"W{i+1}"
                w_desc = _strip_html(w_lines[i].description)
                w_val = f"{w_label}  {w_desc}" if w_desc else w_label
            else:
                w_val = ""

            sheet.write(row, 0, None, f_a_sw)   # col A: empty, bordered (matches A4-A8)
            sheet.write(row, 1, s_val, f_data)
            sheet.write(row, 2, w_val, f_data)
            row += 1

        # ── "External" row ────────────────────────────────────────────────────
        # Template A9: "External", bold, border L/R/B (no top)
        # B9/C9: empty, bordered
        sheet.write(row, 0, "External", f_external)
        sheet.write(row, 1, None, f_blank_bordered)
        sheet.write(row, 2, None, f_blank_bordered)
        row += 1

        # ── Opportunities header row ──────────────────────────────────────────
        sheet.write(row, 0, "Opportunities", f_sec_header)
        sheet.write(row, 1, "Strengths-Opportunities", f_sec_header)
        sheet.write(row, 2, "Weaknesses-Opportunities", f_sec_header)
        row += 1

        # ── O/SO/WO data rows ─────────────────────────────────────────────────
        # Template col A: "O1"..."O5" — Arial Narrow 11, border=1
        #           col B: "SO1"..."SO5" — Arial Narrow 11, border=1
        #           col C: "WO1"..."WO5" — Arial Narrow 11, border=1
        max_o_block = max(len(o_lines), len(so_lines), len(wo_lines), 1)
        for i in range(max_o_block):
            if i < len(o_lines):
                o_label = o_lines[i].label or f"O{i+1}"
                o_desc = _strip_html(o_lines[i].description)
                o_val = f"{o_label}  {o_desc}" if o_desc else o_label
            else:
                o_val = ""

            if i < len(so_lines):
                so_label = f"SO{i+1}"
                so_desc = _strip_html(so_lines[i].description)
                so_val = f"{so_label}  {so_desc}" if so_desc else so_label
            else:
                so_val = ""

            if i < len(wo_lines):
                wo_label = f"WO{i+1}"
                wo_desc = _strip_html(wo_lines[i].description)
                wo_val = f"{wo_label}  {wo_desc}" if wo_desc else wo_label
            else:
                wo_val = ""

            sheet.write(row, 0, o_val, f_data)
            sheet.write(row, 1, so_val, f_data)
            sheet.write(row, 2, wo_val, f_data)
            row += 1

        # ── Separator blank row (template row 16: A16/B16/C16 empty, bordered) ─
        sheet.write(row, 0, None, f_sep)
        sheet.write(row, 1, None, f_sep)
        sheet.write(row, 2, None, f_sep)
        row += 1

        # ── Threats header row ────────────────────────────────────────────────
        sheet.write(row, 0, "Threats", f_sec_header)
        sheet.write(row, 1, "Strengths-Threats", f_sec_header)
        sheet.write(row, 2, "Weaknesses-Threats", f_sec_header)
        row += 1

        # ── T/ST/WT data rows ─────────────────────────────────────────────────
        max_t_block = max(len(t_lines), len(st_lines), len(wt_lines), 1)
        for i in range(max_t_block):
            if i < len(t_lines):
                t_label = t_lines[i].label or f"T{i+1}"
                t_desc = _strip_html(t_lines[i].description)
                t_val = f"{t_label}  {t_desc}" if t_desc else t_label
            else:
                t_val = ""

            if i < len(st_lines):
                st_label = f"ST{i+1}"
                st_desc = _strip_html(st_lines[i].description)
                st_val = f"{st_label}  {st_desc}" if st_desc else st_label
            else:
                st_val = ""

            if i < len(wt_lines):
                wt_label = f"WT{i+1}"
                wt_desc = _strip_html(wt_lines[i].description)
                wt_val = f"{wt_label}  {wt_desc}" if wt_desc else wt_label
            else:
                wt_val = ""

            sheet.write(row, 0, t_val, f_data)
            sheet.write(row, 1, st_val, f_data)
            sheet.write(row, 2, wt_val, f_data)
            row += 1

        # ── Steps section (gray bg, no border — matches template rows 25-45) ──
        row += 1  # one blank row gap before steps
        steps = [
            ("Steps: ", True, "Arial"),
            ("1. Assess your department/unit of your internal issues (strengths and weaknesses).", False, "Arial"),
            ("2. Assess your department/unit of your external issues (opportunities and threats).", False, "Arial"),
            ("3. Identify actionable strategies.", False, "Arial"),
            ("3.1 Match strengths and opportunities (SO).", False, "Arial"),
            ("How can you use your strengths to take advantage of opportunities?", False, "Arial"),
            (None, False, "Arial"),
            ("3.2 Match strengths and threats (ST).", False, "Arial"),
            ("How can you use your strengths to minimize threats?", False, "Arial"),
            (None, False, "Arial"),
            ("3.3 Match opportunities and weaknesses (OW).", False, "Arial"),
            ("How can you take advantage of opportunities to reduce your weaknesses?", False, "Arial"),
            (None, False, "Arial"),
            ("4. Match weaknesses and threats (WT).", False, "Arial"),
            ("   How can you reduce your weaknesses to avoid threats?", False, "Arial"),
            (None, False, "Arial"),
            ("5. In identifying external issues, you may look at issues related to political, economic, social, ", False, "Arial"),
            ("technological, legal and environmental.", False, "Arial"),
            (None, False, "Arial Narrow"),
            ("Note: It's not necessary to match all first or second..e.g. S1 with O1 or S1 with T1. It can be between S1 and O2 or S2 with T3.", False, "Arial Narrow"),
            ("Also, the number of actionable strategies is dependent on the number of matches that can be made between two quadrants.", False, "Arial Narrow"),
        ]
        for text, bold, font in steps:
            if bold:
                f = f_steps_bold
            elif font == "Arial Narrow":
                f = f_steps_narrow
            else:
                f = f_steps
            sheet.write(row, 0, text, f)
            sheet.write(row, 1, None, f_steps)
            sheet.write(row, 2, None, f_steps)
            row += 1

        workbook.close()
        file_b64 = base64.b64encode(output.getvalue())
        filename = f"SWOT TOWS Analysis - {office_name} {year}.xlsx"
        self.write({
            "export_file": file_b64,
            "export_filename": filename,
        })

        return {
            "type": "ir.actions.act_url",
            "url": (
                f"/web/content/?model={self._name}&id={self.id}"
                f"&field=export_file&filename_field=export_filename&download=true"
            ),
            "target": "self",
        }
