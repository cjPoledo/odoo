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
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("ROR")

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

        # column width
        sheet.set_column("A:A", 3.56, format_default)
        sheet.set_column("B:B", 54.33, format_default)
        sheet.set_column("C:E", 23.22, format_default)
        sheet.set_column("F:H", 21.89, format_default)

        sheet.write("B1", "RISKS and OPPORTUNITIES REGISTER (ROR)", format_main_title)
        sheet.write("B2", f"Department: {self.office.name}", format_sub_title)

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
