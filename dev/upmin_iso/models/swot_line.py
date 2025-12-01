from odoo import models, fields, api


class SWOTLine(models.Model):
    _name = "upmin_iso.swot_line"
    _description = "SWOT Line"
    _rec_name = "label"
    _order = "swot_id"

    swot_id = fields.Many2one(
        comodel_name="upmin_iso.swot", string="SWOT", required=True
    )
    description = fields.Text(string="Description", required=True)
    swot_type = fields.Selection(
        string="Type",
        selection=[
            ("S", "Strength"),
            ("W", "Weakness"),
            ("O", "Opportunity"),
            ("T", "Threat"),
        ],
        required=True,
        readonly=True,
    )
    label = fields.Char(
        string="Label", compute="_compute_label", store=True, readonly=True
    )

    @api.depends("swot_type", "swot_id")
    def _compute_label(self):
        for rec in self:
            if rec.swot_type and rec.swot_id:
                lines = (
                    rec.swot_id.strengths
                    if rec.swot_type == "S"
                    else (
                        rec.swot_id.weaknesses
                        if rec.swot_type == "W"
                        else (
                            rec.swot_id.opportunities
                            if rec.swot_type == "O"
                            else rec.swot_id.threats
                        )
                    )
                )

                index = lines.sorted("id").ids.index(rec.id) + 1
                rec.label = f"{rec.swot_type}{index}"
            else:
                rec.label = False

    def unlink(self):
        # Group records by type so we process per type only once
        type_groups = {}
        for rec in self:
            type_groups.setdefault(rec.swot_type, self.env[self._name].browse())
            type_groups[rec.swot_type] |= rec

        for swot_type, recs_to_delete in type_groups.items():
            if swot_type not in ["S", "W", "O", "T"]:
                continue

            # Get the correct One2many list
            field = {
                "S": "strengths",
                "W": "weaknesses",
                "O": "opportunities",
                "T": "threats",
            }[swot_type]

            all_related = recs_to_delete[0].swot_id[field]

            # Exclude ALL records being deleted at once
            remaining = (all_related - recs_to_delete).sorted("id")

            # Recompute labels once
            for idx, line in enumerate(remaining, start=1):
                line.label = f"{swot_type}{idx}"

        return super().unlink()
