from odoo import models, fields, api


class UnitHead(models.Model):
    _name = "upmin_iso.unit_head"
    _description = "Unit Head"
    _rec_name = "name"
    _order = "name"

    name = fields.Many2one(comodel_name="hr.employee", string="Name", required=True)
    email = fields.Char(
        string="Email", related="name.work_email", readonly=True, store=True
    )
    office = fields.Many2many(
        comodel_name="hr.department",
        string="Managed Departments",
        relation="upmin_iso_uh_office_rel",
        column1="uh_id",
        column2="dept_id",
    )
    have_doc_control_perms = fields.Boolean(
        string="Have Document Control Permissions?",
        readonly=True,
        compute="_compute_have_doc_control_perms",
    )
    perms_label = fields.Selection(
        selection=[("active", "Access Active"), ("inactive", "No Access")],
        string="System Access",
        readonly=True,
        compute="_compute_have_doc_control_perms",
    )

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            "Unit Head already exists.",
        ),
    ]

    def _compute_have_doc_control_perms(self):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
        for rec in self:
            user = rec.name.user_id
            has = bool(user and group in user.groups_id)
            rec.have_doc_control_perms = has
            rec.perms_label = "active" if has else "inactive"

    def _grant_group(self, user):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
        if user:
            user.sudo().write({"groups_id": [(4, group.id)]})

    def _revoke_group(self, user):
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
        if not user or group not in user.groups_id:
            return
        # Keep perms if the employee still has an active Document Controller record
        emp = user.employee_id
        if emp and self.env["upmin_iso.document_controller"].sudo().search_count([("name", "=", emp.id)]):
            return
        user.sudo().write({"groups_id": [(3, group.id)]})

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            self._grant_group(rec.name.user_id)
        return records

    def write(self, vals):
        if "name" in vals:
            old_users = {rec.id: rec.name.user_id for rec in self}

        result = super().write(vals)

        if "name" in vals:
            for rec in self:
                self._revoke_group(old_users[rec.id])
                self._grant_group(rec.name.user_id)

        return result

    def unlink(self):
        users = [rec.name.user_id for rec in self]
        result = super().unlink()
        for user in users:
            self._revoke_group(user)
        return result

    @api.model
    def action_sync_unit_heads(self):
        departments = self.env["hr.department"].sudo().search([("manager_id", "!=", False)])

        # Group managed depts by employee
        manager_to_depts = {}
        for dept in departments:
            emp_id = dept.manager_id.id
            manager_to_depts.setdefault(emp_id, []).append(dept.id)

        existing_uhs = self.search([])
        existing_by_emp = {uh.name.id: uh for uh in existing_uhs}

        # Create entries for new managers
        created = 0
        for emp_id, dept_ids in manager_to_depts.items():
            if emp_id not in existing_by_emp:
                self.create([{"name": emp_id, "office": [(6, 0, dept_ids)]}])
                created += 1

        # Update office for existing entries where managed depts changed
        updated = 0
        for emp_id, dept_ids in manager_to_depts.items():
            if emp_id in existing_by_emp:
                uh = existing_by_emp[emp_id]
                current_ids = set(uh.office.ids)
                new_ids = set(dept_ids)
                if current_ids != new_ids:
                    uh.write({"office": [(6, 0, dept_ids)]})
                    updated += 1

        # Delete entries where employee no longer manages any dept
        to_delete = existing_uhs.filtered(lambda uh: uh.name.id not in manager_to_depts)
        deleted = len(to_delete)
        if to_delete:
            to_delete.unlink()

        # Ensure perms are correct for all remaining unit heads
        group = self.env.ref("upmin_iso.group_iso_doc_controller")
        for uh in self.search([]):
            user = uh.name.user_id
            if user and group not in user.groups_id:
                self._grant_group(user)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Sync Complete",
                "message": f"Unit heads synchronized. Created: {created}, Updated: {updated}, Removed: {deleted}.",
                "sticky": False,
                "type": "success",
            },
        }
