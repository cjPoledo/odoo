from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv import expression


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
    line_ids_no_add_delete = fields.One2many(
        "upmin_stock.ris_line", "ris_id", string="Stocks"
    )
    purpose = fields.Text(string="Purpose")
    requested_by = fields.Many2one("res.partner", string="Requested By", required=True)
    requester_designation = fields.Char(string="Designation", required=True)
    request_date = fields.Date(
        string="Date", required=True, default=fields.Date.context_today
    )
    approved_by = fields.Char(string="Approved By", required=True)
    approver_designation = fields.Char(string="Designation", required=True)
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

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group("upmin_stock.group_spmo_stock_custodian"):
            domain = [
                "|",
                ("create_uid", "=", self.env.user.id),
                ("status", "!=", "draft"),
            ]
        else:
            domain = [("create_uid", "=", self.env.user.id)]
        args = expression.AND([args, domain])
        return super().search(
            args, offset=offset, limit=limit, order=order, count=count
        )

    @api.constrains("status")
    def _check_approval_fields(self):
        for record in self:
            if record.status == "receiving":
                if (
                    not record.issued_by
                    or not record.issuer_designation
                    or not record.issue_date
                ):
                    raise ValidationError(
                        "All issuance fields must be filled when the status is 'For Issuance'."
                    )
            elif record.status == "received":
                if (
                    not record.received_by
                    or not record.receiver_designation
                    or not record.receive_date
                ):
                    raise ValidationError(
                        "All receiving fields must be filled when the status is 'For Receiving'."
                    )

    def action_proceed_next_step(self):
        if self.status == "draft":
            self.status = "issuance"
        elif self.status == "issuance":
            self.status = "receiving"
            for line in self.line_ids:
                self.env["upmin_stock.issuance"].create(
                    {
                        "ris_line": line.id,
                    }
                )
        elif self.status == "receiving":
            self.status = "received"

    def action_return_last_step(self):
        if self.status == "issuance":
            self.issued_by = False
            self.issue_date = False
            self.issuer_designation = False
            self.line_ids.stock_avail = False
            self.line_ids.quantity_issued = 0
            self.status = "draft"
        elif self.status == "receiving":
            self.received_by = False
            self.receive_date = False
            self.receiver_designation = False
            self.status = "issuance"
        elif self.status == "received":
            self.status = "receiving"

    def _compute_user_permission(self):
        special_group = self.env.ref("upmin_stock.group_spmo_stock_custodian")
        for record in self:
            record.user_has_permission = special_group in self.env.user.groups_id
