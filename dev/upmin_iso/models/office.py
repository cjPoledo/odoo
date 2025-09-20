from odoo import models, fields, api


class Office(models.Model):
    _name = "upmin_iso.office"
    _description = "Office"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Office Name", required=True)
    cluster = fields.Many2one(
        comodel_name="upmin_iso.office",
        string="Cluster",
        domain="['&', ('cluster_head', '=', True), ('name', '!=', name)]",
    )
    cluster_head = fields.Boolean(string="Cluster Head?", default=False)
    doc_controllers = fields.Many2many(
        comodel_name="res.partner", string="Document Controllers"
    )

    @api.onchange("cluster_head")
    def _cluster_head_onchange(self):
        if self.cluster_head:
            self.cluster = self
        else:
            self.cluster = None

    @api.model_create_multi
    def create(self, data_list):
        res = super().create(data_list)
        for office in res:
            if office.cluster_head:
                office.cluster = office
        return res

    def write(self, vals):
        for office in self:
            if "cluster_head" in vals and not vals["cluster_head"]:
                cluster_members = self.search([("cluster", "=", office.id)])
                for member in cluster_members:
                    member.cluster = None
        return super().write(vals)
