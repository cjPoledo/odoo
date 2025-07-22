from odoo import models, fields, api


class RIS(models.Model):
    _name = "upmin_stock.ris"
    _description = "Requisition and Issue Slip"
    _rec_name = "ris_no"

    ris_no = fields.Char(
        string="RIS No.",
        required=True,
        readonly=True,
    )
    entity_name = fields.Char(
        string="Entity Name",
        required=True,
        default="UNIVERSITY OF THE PHILIPPINES MINDANAO",
    )
    fund_cluster = fields.Many2one(
        "upmin_stock.fund_cluster", string="Fund Cluster", required=True
    )
    division = fields.Char(string="Division", required=True)
    rc_code = fields.Many2one(
        "upmin_stock.rc", string="Responsibility Center Code", required=True
    )
    line_ids = fields.One2many("upmin_stock.ris_line", "ris_id", string="Stocks")
    purpose = fields.Text(string="Purpose")
    requested_by = fields.Many2one("res.partner", string="Requested By", required=True)
    requester_designation = fields.Char(string="Designation")
    request_date = fields.Date(string="Date")
    approved_by = fields.Char(string="Approved By")
    approver_designation = fields.Char(string="Designation")
    approve_date = fields.Date(string="Date")
    issued_by = fields.Many2one("res.partner", string="Issued By")
    issuer_designation = fields.Char(string="Designation")
    issue_date = fields.Date(string="Date")
    received_by = fields.Char(string="Received By")
    receiver_designation = fields.Char(string="Designation")
    receive_date = fields.Date(string="Date")
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("issuance", "For Issuance"),
            ("receiving", "For Receiving"),
            ("received", "Received"),
        ],
        string="Status",
        default="draft",
        readonly=True,
    )

    user_has_permission = fields.Boolean(
        string="User Has Special Permission",
        compute="_compute_user_permission",
        store=False,
    )

    _sql_constraints = [
        ("ris_no_uniq", "unique(ris_no)", "The RIS No. must be unique!"),
    ]

    @api.model
    def create(self, vals):
        if not vals.get("ris_no"):
            today = fields.Date.context_today(self)
            year = today.strftime("%Y")
            month = today.strftime("%m")
            code = f"stock.ref.sr.{year}.{month}"

            # find or create sequence
            sequence = (
                self.env["ir.sequence"].sudo().search([("code", "=", code)], limit=1)
            )
            if not sequence:
                sequence = (
                    self.env["ir.sequence"]
                    .sudo()
                    .create(
                        {
                            "name": f"Stock Reference SR {year}-{month}",
                            "code": code,
                            "prefix": f"SR{year}-{month}-",
                            "padding": 3,
                            "number_next": 1,
                            "number_increment": 1,
                        }
                    )
                )

            vals["ris_no"] = sequence.sudo().next_by_code(code)

        return super().create(vals)

    def action_proceed_next_step(self):
        if self.status == "draft":
            self.status = "issuance"
        elif self.status == "issuance":
            self.status = "receiving"
        elif self.status == "receiving":
            self.status = "received"

    def action_return_last_step(self):
        if self.status == "issuance":
            self.status = "draft"
        elif self.status == "receiving":
            self.status = "issuance"
        elif self.status == "received":
            self.status = "receiving"

    def _compute_user_permission(self):
        special_group = self.env.ref("upmin_stock.group_spmo_stock_custodian")
        for record in self:
            record.user_has_permission = special_group in self.env.user.groups_id
