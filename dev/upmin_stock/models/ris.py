from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from collections import Counter


class RIS(models.Model):
    _name = "upmin_stock.ris"
    _description = "Requisition and Issue Slip"
    _rec_name = "ris_no"
    _order = "create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

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
        "upmin_stock.rc",
        string="Responsibility Center Code",
        required=True,
        help="For missing responsibility center, please contact the SPMO custodian.",
    )
    line_ids = fields.One2many("upmin_stock.ris_line", "ris_id", string="Add Stocks")
    line_ids_no_add_delete = fields.One2many(
        "upmin_stock.ris_line", "ris_id", string="Stocks"
    )
    purpose = fields.Text(string="Purpose")
    requested_by = fields.Many2one(
        "res.partner",
        string="Requested By",
        required=True,
        default=lambda self: self.env.user.partner_id.id,
    )
    requester_designation = fields.Char(string="Requester Designation", required=True)
    request_date = fields.Date(
        string="Request Date", required=True, default=fields.Date.context_today
    )
    approved_by = fields.Many2one("res.partner", string="Approved By", required=True)
    approver_designation = fields.Char(string="Approver Designation", required=True)
    approve_date = fields.Date(string="Approve Date")
    issued_by = fields.Many2one("res.partner", string="Issued By")
    issuer_designation = fields.Char(string="Issuer Designation")
    issue_date = fields.Date(string="Issue Date")
    received_by = fields.Many2one("res.partner", string="Received By")
    receiver_designation = fields.Char(string="Receiver Designation")
    receive_date = fields.Date(string="Receive Date")
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
        tracking=True,
    )

    user_has_permission = fields.Boolean(
        string="User Has Special Permission",
        compute="_compute_user_permission",
        store=False,
    )
    is_creator = fields.Boolean(
        string="Is Creator",
        compute="_compute_is_creator",
        store=False,
    )
    ppmp_id = fields.Many2one(
        "upmin_stock.ppmp", string="PPMP", compute="_compute_ppmp_id", store=True
    )

    _sql_constraints = [
        ("ris_no_uniq", "unique(ris_no)", "The RIS No. must be unique!"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ris_no"):
                today = fields.Date.context_today(self)
                year = today.strftime("%Y")
                month = today.strftime("%m")
                code = f"stock.ref.sr.{year}.{month}"

                # find or create sequence
                sequence = (
                    self.env["ir.sequence"]
                    .sudo()
                    .search([("code", "=", code)], limit=1)
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

        return super().create(vals_list)

    @api.onchange("rc_code", "fund_cluster")
    def _onchange_rc_code_fund_cluster(self):
        self.line_ids = [(5, 0, 0)]

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

    @api.constrains("line_ids")
    def _check_unique_stock_id(self):
        for rec in self:
            stock_ids = [
                line.ppmp_balance_id.stock_id
                for line in rec.line_ids
                if line.ppmp_balance_id
            ]
            counts = Counter(stock_ids)
            duplicates = [
                stock.display_name for stock, count in counts.items() if count > 1
            ]

            if duplicates:
                dup_str = ", ".join(duplicates)
                raise ValidationError(
                    f"The following stock(s) are duplicated: {dup_str}"
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
            action = self.env.ref("upmin_stock.action_ris")
            return action.read()[0]

        elif self.status == "receiving":
            self.received_by = False
            self.receive_date = False
            self.receiver_designation = False
            self.status = "issuance"
            for line in self.line_ids:
                issuances = self.env["upmin_stock.issuance"].search(
                    [("ris_line", "=", line.id)]
                )
                issuances.unlink()
        elif self.status == "received":
            self.status = "receiving"

    def _compute_user_permission(self):
        special_group = self.env.ref("upmin_stock.group_spmo_stock_custodian")
        for record in self:
            record.user_has_permission = special_group in self.env.user.groups_id

    @api.depends("create_uid")
    def _compute_is_creator(self):
        current_user = self.env.uid
        for rec in self:
            rec.is_creator = rec.create_uid.id == current_user

    @api.depends("rc_code", "fund_cluster")
    def _compute_ppmp_id(self):
        for rec in self:
            rec.ppmp_id = self.env["upmin_stock.ppmp"].search(
                [
                    ("rc", "=", rec.rc_code.id),
                    ("fund_cluster_id", "=", rec.fund_cluster.id),
                ],
                limit=1,
            )

    def unlink(self):
        for rec in self:
            if not self.env.user.has_group("upmin_stock.group_spmo_stock_custodian"):
                if rec.status in ["receiving", "received"]:
                    raise UserError(
                        "Deletion is blocked for issued records. Please contact the SPMO Custodian."
                    )

        ppmp_balance = self.mapped("line_ids.ppmp_balance_id")
        unlink = super().unlink()
        for stock in ppmp_balance.mapped("stock_id"):
            stock.update_fund_cluster_balance()
        return unlink
