from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SWOTLine(models.Model):
    _name = "upmin_iso.swot_line"
    _description = "SWOT Line"
    _rec_name = "label"
    _order = "swot_id,ror_id,label"

    swot_id = fields.Many2one(
        comodel_name="upmin_iso.swot", string="SWOT", ondelete="cascade"
    )
    ror_id = fields.Many2one(
        comodel_name="upmin_iso.ror", string="ROR", ondelete="cascade"
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

    # Risk and Opportunity fields (filled in ROR context)
    interested_parties = fields.Char(
        string="Interested Parties", help="Who are those affected by the issue?"
    )
    needs_and_exp = fields.Text(
        string="Needs and Expectations",
        help="What are the needs and expectations of the identified interested parties?",
    )
    compliance = fields.Html(
        string="Compliance Obligations",
        help='Is there any law, directive, issuance, statute, ordinance or regulation that\'s related to the issue?\nIf yes, then kindly indicate.\nIf none, kindly indicate "None".',
    )
    risks = fields.Text(
        string="Risks (R)", help="Identify the risk/s that may surface from the issue."
    )
    opportunities = fields.Text(
        string="Opportunities (O)",
        help="Indicate an opportunity that may be taken advantage of or capitalize, in relation to the issue.",
    )
    consequence = fields.Text(
        string="Consequence (C)", help="What's the effect if the risk is not addressed?"
    )
    benefit = fields.Text(
        string="Benefit (B)", help="What's the benefit if opportunity is availed of?"
    )
    risk_existing_control = fields.Text(
        string="Existing Control (Risks)",
        help='What is currently being done to address the risk?\nIf none, kindly indicate "None".',
    )
    opportunities_existing_control = fields.Text(
        string="Existing Control (Opportunities)",
        help='What is currently being done to avail of the opportunity?\nIf none, kindly indicate "None".',
    )
    ratings = fields.One2many(
        comodel_name="upmin_iso.ror_rating",
        inverse_name="issue",
        string="Ratings",
    )
    closures = fields.One2many(
        comodel_name="upmin_iso.swot_line_closure",
        inverse_name="swot_line_id",
        string="Closure History",
    )
    is_closed = fields.Boolean(
        string="Closed", compute="_compute_is_closed", store=True,
        help="A closed issue is excluded from pending/notification checks "
        "but stays visible with its full rating and closure history.",
    )

    # remarks
    fields_status = fields.Text(
        string="Fields Status", compute="_compute_fields_status",
    )
    ratings_status = fields.Text(
        string="Ratings Status", compute="_compute_ratings_status",
    )
    fields_missing_count = fields.Integer(
        string="Fields Missing Count", compute="_compute_fields_missing_count", store=True,
    )
    fields_missing_label = fields.Char(
        string="Fields Missing", compute="_compute_fields_missing_label",
    )
    current_quarter_rated = fields.Selection(
        selection=[
            ("complete", "Completed"),
            ("incomplete", "In Progress"),
            ("no", "Not Rated"),
            ("closed", "Closed"),
        ],
        string="This Quarter",
        compute="_compute_current_quarter_rated",
    )

    _HTML_FIELDS = {"compliance"}

    def _is_filled(self, field_name, value):
        if field_name in self._HTML_FIELDS:
            import re
            return bool(re.sub(r"<[^>]+>", "", str(value or "")).strip())
        return bool(value)

    @api.depends(
        "interested_parties", "needs_and_exp", "compliance", "risks",
        "opportunities", "consequence", "benefit",
        "risk_existing_control", "opportunities_existing_control",
    )
    def _compute_fields_status(self):
        for rec in self:
            status_list = []
            field_names = [
                "interested_parties",
                "needs_and_exp",
                "compliance",
                "risks",
                "opportunities",
                "consequence",
                "benefit",
                "risk_existing_control",
                "opportunities_existing_control",
            ]
            for field_name in field_names:
                if not rec._is_filled(field_name, rec[field_name]):
                    field_label = rec._fields[field_name].string
                    status_list.append(field_label)

            if not status_list:
                rec.fields_status = "All fields are filled."
            else:
                rec.fields_status = "Missing: " + ", ".join(status_list)

    @api.depends(
        "ratings", "ratings.progress", "ratings.review_date", "ratings.risk_conclusion",
        "is_closed", "closures.closed_date", "closures.reopened_date",
    )
    def _compute_ratings_status(self):
        from datetime import date as _date

        def current_quarter_end():
            today = _date.today()
            for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
                q = _date(today.year, month, day)
                if today <= q:
                    return q
            return _date(today.year + 1, 3, 31)

        def past_required_quarters(create_date):
            today = _date.today()
            result = []
            for year in range(create_date.year, today.year + 1):
                for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
                    q = _date(year, month, day)
                    if q >= create_date and q < today:
                        result.append(q)
            return result

        q_end = current_quarter_end()

        for rec in self:
            completed_ratings = rec.ratings.filtered(lambda r: r.progress == 100)
            lines = []

            # CTA: current quarter status
            if rec.is_closed:
                lines.append("[ Closed — no rating needed ]")
            else:
                this_quarter = rec.ratings.filtered(lambda r: r.review_date == q_end)
                if not this_quarter:
                    lines.append("[ Rate this quarter ]")
                elif this_quarter[:1].progress < 100:
                    lines.append("[ Complete this quarter's rating ]")

            # Latest completed rating
            if completed_ratings:
                last_date = max(completed_ratings.mapped("review_date"))
                latest = completed_ratings.filtered(lambda r: r.review_date == last_date)[:1]
                lines.append(f"Last: {last_date.strftime('%b %d, %Y')} — {latest.risk_conclusion or 'unrated'}")
            else:
                lines.append("No completed ratings yet")

            # Skipped quarters — a quarter covered by a closure is exempt,
            # since the issue was deliberately dormant, not neglected.
            create_date = rec.create_date.date() if rec.create_date else _date.today()
            all_required = past_required_quarters(create_date)
            entry_dates = set(rec.ratings.mapped("review_date"))
            skipped = [
                q for q in all_required
                if q not in entry_dates and not rec._is_closed_during(q)
            ]
            if skipped:
                skipped_labels = ", ".join(q.strftime("%b %Y") for q in skipped)
                lines.append(f"Skipped: {skipped_labels}")

            # Incomplete past ratings
            incomplete_past = rec.ratings.filtered(
                lambda r: r.review_date < q_end and r.progress < 100
            )
            if incomplete_past:
                labels = ", ".join(
                    r.review_date.strftime("%b %Y")
                    for r in sorted(incomplete_past, key=lambda r: r.review_date)
                )
                lines.append(f"Incomplete past: {labels}")

            rec.ratings_status = "\n".join(lines)

    @api.depends(
        "interested_parties", "needs_and_exp", "compliance", "risks",
        "opportunities", "consequence", "benefit",
        "risk_existing_control", "opportunities_existing_control",
    )
    def _compute_fields_missing_count(self):
        field_names = [
            "interested_parties", "needs_and_exp", "compliance", "risks",
            "opportunities", "consequence", "benefit",
            "risk_existing_control", "opportunities_existing_control",
        ]
        for rec in self:
            rec.fields_missing_count = sum(
                1 for f in field_names if not rec._is_filled(f, rec[f])
            )

    @api.depends("fields_missing_count")
    def _compute_fields_missing_label(self):
        for rec in self:
            rec.fields_missing_label = f"{rec.fields_missing_count} missing" if rec.fields_missing_count else False

    @api.depends("ratings", "ratings.review_date", "ratings.progress", "is_closed")
    def _compute_current_quarter_rated(self):
        from datetime import date as _date
        today = fields.Date.context_today(self)
        year = today.year
        q_end = None
        for month, day in [(3, 31), (6, 30), (9, 30), (12, 31)]:
            q = _date(year, month, day)
            if q >= today:
                q_end = q
                break
        if not q_end:
            q_end = _date(year + 1, 3, 31)
        for rec in self:
            if rec.is_closed:
                rec.current_quarter_rated = "closed"
                continue
            rating = rec.ratings.filtered(lambda r: r.review_date == q_end)[:1]
            if not rating:
                rec.current_quarter_rated = "no"
            elif rating.progress == 100:
                rec.current_quarter_rated = "complete"
            else:
                rec.current_quarter_rated = "incomplete"

    @api.depends("closures.reopened_date")
    def _compute_is_closed(self):
        for rec in self:
            open_closure = rec.closures.filtered(lambda c: not c.reopened_date)
            rec.is_closed = bool(open_closure)

    def _is_closed_during(self, a_date):
        """True if any closure interval covered the given date."""
        self.ensure_one()
        return any(closure._covers(a_date) for closure in self.closures)

    def action_close(self, closed_reason):
        self.ensure_one()
        employee = self.env.user.employee_id
        self.env["upmin_iso.swot_line_closure"].create({
            "swot_line_id": self.id,
            "closed_reason": closed_reason,
            "closed_by": employee.id if employee else False,
        })

    def action_open_close_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Close Issue",
            "res_model": "upmin_iso.swot_line_close_wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_swot_line_id": self.id},
        }

    def action_reopen(self):
        self.ensure_one()
        open_closure = self.closures.filtered(lambda c: not c.reopened_date)[:1]
        if not open_closure:
            return
        employee = self.env.user.employee_id
        open_closure.write({
            "reopened_date": fields.Date.context_today(self),
            "reopened_by": employee.id if employee else False,
        })

    @api.constrains("swot_id", "ror_id")
    def _check_parent(self):
        for rec in self:
            if not rec.swot_id and not rec.ror_id:
                raise ValidationError("A SWOT line must belong to either a SWOT or a ROR.")

    @api.depends("swot_type", "swot_id")
    def _compute_label(self):
        for rec in self:

            # Always empty if missing type or parent (standalone ROR lines have no swot_id)
            if not rec.swot_type or not rec.swot_id:
                rec.label = False
                continue

            # If record is not saved yet → leave label empty
            if not isinstance(rec.id, int):
                rec.label = False
                continue

            field_by_type = {
                "S": "strengths",
                "W": "weaknesses",
                "O": "opportunities",
                "T": "threats",
            }

            siblings = rec.swot_id[field_by_type[rec.swot_type]]

            # Sort siblings reliably
            sibling_lines = siblings.sorted(key=lambda r: r.id or 0)

            # Find index (now always valid because rec.id is real)
            index = sibling_lines.ids.index(rec.id) + 1

            rec.label = f"{rec.swot_type}{index}"

    def unlink(self):
        # Group records by type so we process per type only once
        # Only recompute labels for lines that belong to a SWOT
        type_groups = {}
        for rec in self:
            if not rec.swot_id:
                continue
            type_groups.setdefault(rec.swot_type, self.env[self._name].browse())
            type_groups[rec.swot_type] |= rec

        for swot_type, recs_to_delete in type_groups.items():
            if swot_type not in ["S", "W", "O", "T"]:
                continue

            field = {
                "S": "strengths",
                "W": "weaknesses",
                "O": "opportunities",
                "T": "threats",
            }[swot_type]

            all_related = recs_to_delete[0].swot_id[field]
            remaining = (all_related - recs_to_delete).sorted("id")

            for idx, line in enumerate(remaining, start=1):
                line.label = f"{swot_type}{idx}"

        return super().unlink()
