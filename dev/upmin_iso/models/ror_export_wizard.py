from odoo import models, fields
import io, base64
import xlsxwriter


class RORExportWizard(models.TransientModel):
    _name = "upmin_iso.ror_export_wizard"
    _description = "Export ROR"

    office = fields.Many2one(
        comodel_name="upmin_iso.office",
        string="Office",
        required=True,
        domain=lambda self: [("doc_controllers", "in", self.env.user.partner_id.id)],
    )
    export_file = fields.Binary("Export File", readonly=True)
    export_filename = fields.Char("File Name")

    def action_export_ror(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("ROR")

        sheet.write(0, 0, self.office.name)

        workbook.close()
        data_bytes = output.getvalue()
        output.close()
        file_b64 = base64.b64encode(data_bytes)
        self.write(
            {
                "export_file": file_b64,
                "export_filename": f"{self.office.name} - ror_export.xlsx",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}&field=export_file&filename_field=export_filename&download=true",
            "target": "self",
        }
