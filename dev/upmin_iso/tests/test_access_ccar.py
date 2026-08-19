"""
Access tests for CCAR and its sub-models.

┌─────────────────────────────────────────────────────────────────────────────┐
│ upmin_iso.ccar                                                              │
│ Model-level: Staff=CRUD, DC=R+W(no C/D), IA=R+W(no C/D)                   │
│ Row-level (read):                                                           │
│   DC  → own office                                                          │
│   IA  → auditors.name.user_id = current user                               │
│   Staff → all                                                               │
│ Write eligibility (enforced in CCAR.write(), not ir.rule):                  │
│   DC  → own office AND status in ('office', 'office2')                     │
│   IA  → assigned AND status in ('creation', 'verification')                │
│   Staff → all                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ upmin_iso.ccar_corrective_action                                            │
│ Model-level: Staff=R, DC=CRUD, IA=R                                        │
│ Row-level: DC→own office, IA→assigned                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ upmin_iso.ccar_correction_effectiveness                                     │
│ upmin_iso.ccar_corrective_action_effectiveness                              │
│ Model-level: Staff=R, DC=R, IA=CRUD                                        │
│ Row-level: DC→own office, IA→assigned                                      │
└─────────────────────────────────────────────────────────────────────────────┘

Fixture CCARs (all dept_a unless noted):
  ccar_creation  status='creation'     — assigned IA, DC can read but NOT write
  ccar_office    status='office'       — DC CAN write
  ccar_verif     status='verification' — IA CAN write
  ccar_b         status='creation', office=dept_b — neither u1 nor u2 can see
"""

from odoo.exceptions import AccessError, UserError

from .common import ISOAccessBase


class TestCCARAccess(ISOAccessBase):

    # ── Visibility ────────────────────────────────────────────────────────────

    def test_u0_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ccar', self.u0)

    def test_u1_ia_sees_assigned_ccars_only(self):
        # u1 is auditor on audit_a → sees ccar_creation/ccar_office/ccar_verif
        # but NOT ccar_b (audit_b has no auditors)
        results = self._search('upmin_iso.ccar', self.u1)
        self.assertIn(self.ccar_creation, results)
        self.assertIn(self.ccar_office, results)
        self.assertIn(self.ccar_verif, results)
        self.assertNotIn(self.ccar_b, results)

    def test_u2_dc_sees_own_office_ccars_only(self):
        results = self._search('upmin_iso.ccar', self.u2)
        self.assertIn(self.ccar_creation, results)
        self.assertIn(self.ccar_office, results)
        self.assertNotIn(self.ccar_b, results)

    def test_u3_ia_dc_sees_union(self):
        # U3: IA (assigned to audit_a) + DC (dept_b)
        # IA → ccar_creation/office/verif; DC → ccar_b/ccar_b_office
        results = self._search('upmin_iso.ccar', self.u3)
        self.assertIn(self.ccar_creation, results)    # IA
        self.assertIn(self.ccar_office, results)      # IA
        self.assertIn(self.ccar_verif, results)       # IA
        self.assertIn(self.ccar_b, results)           # DC (dept_b)
        self.assertIn(self.ccar_b_office, results)    # DC (dept_b)

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.ccar', self.u4)
        self.assertIn(self.ccar_creation, results)
        self.assertIn(self.ccar_b, results)

    def test_u5_staff_dc_reads_all(self):
        results = self._search('upmin_iso.ccar', self.u5)
        self.assertIn(self.ccar_creation, results)
        self.assertIn(self.ccar_b, results)

    def test_u6_staff_ia_reads_all(self):
        results = self._search('upmin_iso.ccar', self.u6)
        self.assertIn(self.ccar_creation, results)
        self.assertIn(self.ccar_b, results)

    def test_u7_all_reads_all(self):
        results = self._search('upmin_iso.ccar', self.u7)
        self.assertIn(self.ccar_creation, results)
        self.assertIn(self.ccar_b, results)

    # ── DC write — status-gated ───────────────────────────────────────────────

    def test_u2_dc_can_write_ccar_at_office_status(self):
        # ccar_office is at status='office' AND office=dept_a → DC write rule matches
        self.ccar_office.with_user(self.u2).write({'description': 'corrected'})

    def test_u2_dc_cannot_write_ccar_at_creation_status(self):
        # ccar_creation is at status='creation' → DC write rule requires office/office2
        with self.assertRaises(AccessError):
            self.ccar_creation.with_user(self.u2).write({'description': 'attempted'})

    def test_u2_dc_cannot_write_ccar_at_verification_status(self):
        with self.assertRaises(AccessError):
            self.ccar_verif.with_user(self.u2).write({'description': 'attempted'})

    def test_u2_dc_cannot_write_other_office_ccar(self):
        # ccar_b is dept_b → outside u2's office
        with self.assertRaises(AccessError):
            self.ccar_b.with_user(self.u2).write({'description': 'attempted'})

    # ── IA write — status-gated ───────────────────────────────────────────────

    def test_u1_ia_can_write_ccar_at_verification_status(self):
        self.ccar_verif.with_user(self.u1).write({'description': 'verified'})

    def test_u1_ia_can_write_ccar_at_creation_status(self):
        self.ccar_creation.with_user(self.u1).write({'description': 'initial'})

    def test_u1_ia_cannot_write_ccar_at_office_status(self):
        # ccar_office is at status='office' → IA write rule requires creation/verification
        with self.assertRaises(AccessError):
            self.ccar_office.with_user(self.u1).write({'description': 'attempted'})

    def test_u1_ia_cannot_write_unassigned_ccar(self):
        # ccar_b has no auditors → u1 can't even read it, let alone write
        with self.assertRaises(AccessError):
            self.ccar_b.with_user(self.u1).write({'description': 'attempted'})

    # ── U3 (IA+DC) can write via whichever rule applies ──────────────────────

    def test_u3_ia_dc_can_write_at_office_status(self):
        # U3's DC scope is dept_b → ccar_b_office (dept_b, status='office') matches DC write rule
        self.ccar_b_office.with_user(self.u3).write({'description': 'u3 office step'})

    def test_u3_ia_dc_can_write_at_creation_status(self):
        # IA rule grants write at status='creation' for assigned
        self.ccar_creation.with_user(self.u3).write({'description': 'u3 creation'})

    def test_u3_ia_dc_cannot_write_foreign_office_ccar_at_office_status(self):
        # ccar_office belongs to dept_a. U3 can READ it (IA assigned to
        # audit_a), but U3's DC scope is dept_b, not dept_a — holding the
        # DC group badge elsewhere must not unlock a DC-gated status
        # (office/office2) on a CCAR of an office U3 isn't actually DC of.
        with self.assertRaises(AccessError):
            self.ccar_office.with_user(self.u3).write({'description': 'attempted'})

    def test_u8_dc_unassigned_ia_cannot_write_at_creation_status(self):
        # U8 is DC of dept_a (ccar_creation's office) and can therefore READ
        # ccar_creation, but is not assigned as auditor on audit_a. Holding
        # the IA group badge alone must not unlock the IA-gated 'creation'
        # status on a CCAR U8 isn't actually the assigned auditor for.
        with self.assertRaises(AccessError):
            self.ccar_creation.with_user(self.u8).write({'description': 'attempted'})

    def test_u8_dc_unassigned_ia_can_write_at_office_status(self):
        # Legitimate: U8 IS DC of dept_a, and ccar_office is dept_a's own
        # CCAR at a DC-gated status.
        self.ccar_office.with_user(self.u8).write({'description': 'u8 dc update'})

    # ── Additional Viewers (bypass_user_ids) act as DC of record ─────────────

    def test_u3_bypass_dc_can_write_foreign_office_ccar_at_office_status(self):
        # U3's DC scope is dept_b, so ccar_office (dept_a) is normally
        # out of reach for DC write (see
        # test_u3_ia_dc_cannot_write_foreign_office_ccar_at_office_status).
        # Once explicitly added as an Additional Viewer, U3 must be able to
        # edit it at a DC-gated status just as if U3 were dept_a's own DC.
        self.ccar_office.sudo().bypass_user_ids = [(4, self.u3.id)]
        self.ccar_office.with_user(self.u3).write({'description': 'bypass dc update'})

    def test_u1_bypass_without_dc_group_still_has_no_ccar_access(self):
        # The bypass_user_ids clause only appears on rule_doc_controller_read
        # (scoped to group_iso_doc_controller). U1 is IA-only, so being
        # added to bypass_user_ids on a CCAR outside their assignment
        # doesn't grant them read/write access at all — that rule never
        # applies to them regardless of bypass_user_ids membership.
        self.ccar_office.sudo().bypass_user_ids = [(4, self.u1.id)]
        with self.assertRaises(AccessError):
            self.ccar_office.with_user(self.u1).write({'description': 'attempted'})

    # ── Staff full CRUD ───────────────────────────────────────────────────────

    def test_u4_staff_can_write_any_ccar(self):
        self.ccar_creation.with_user(self.u4).write({'description': 'staff edit'})
        self.ccar_b.with_user(self.u4).write({'description': 'staff edit b'})

    def test_u4_staff_can_delete_ccar(self):
        p2 = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-10-01', 'audit_end_date': '2024-10-31',
        })
        ai = self.env['upmin_iso.audit_info'].sudo().create({
            'office_to_audit': self.dept_a.id, 'audit_period': p2.id,
        })
        finding = self.env['upmin_iso.audit_finding'].sudo().create({
            'audit_info': ai.id,
            'auditor': self.env.user.partner_id.id,
            'rating': 'nc',
        })
        ccar = self.env['upmin_iso.ccar'].sudo().create({
            'ccar_no': '2024-99', 'date': '2024-10-01',
            'audit_period': p2.id, 'related_nc': finding.id,
        })
        ccar.with_user(self.u4).unlink()

    def test_u1_ia_cannot_create_ccar(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.ccar'].with_user(self.u1).create({
                'ccar_no': '9999-01', 'date': '2024-01-01',
                'audit_period': self.period.id, 'related_nc': self.c_a1.id,
            })

    def test_u2_dc_cannot_create_ccar(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.ccar'].with_user(self.u2).create({
                'ccar_no': '9999-02', 'date': '2024-01-01',
                'audit_period': self.period.id, 'related_nc': self.c_a1.id,
            })


class TestCCARCorrectiveActionAccess(ISOAccessBase):
    """
    ccar_corrective_action:
      DC   → CRUD, own office
      IA   → R only, assigned
      Staff → R only, all
    """

    def test_u0_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ccar_corrective_action', self.u0)

    def test_u1_ia_sees_assigned_only(self):
        results = self._search('upmin_iso.ccar_corrective_action', self.u1)
        # ca_a is linked to ccar_office which is linked to audit_a (u1 assigned)
        self.assertIn(self.ca_a, results)

    def test_u2_dc_sees_own_office_only(self):
        results = self._search('upmin_iso.ccar_corrective_action', self.u2)
        self.assertIn(self.ca_a, results)   # ccar_office → dept_a

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.ccar_corrective_action', self.u4)
        self.assertIn(self.ca_a, results)

    def test_u1_ia_cannot_write_corrective_action(self):
        # IA has model-level perm_write=0 for corrective_action
        with self.assertRaises(AccessError):
            self.ca_a.with_user(self.u1).write({'corrective_action': 'attempted'})

    def test_u4_staff_cannot_write_corrective_action(self):
        # Staff has model-level perm_write=0
        with self.assertRaises(AccessError):
            self.ca_a.with_user(self.u4).write({'corrective_action': 'attempted'})

    def test_u2_dc_can_write_own_office_ca(self):
        self.ca_a.with_user(self.u2).write({'corrective_action': 'dc update'})

    def test_u2_dc_can_create_ca_for_own_office_ccar(self):
        rec = self.env['upmin_iso.ccar_corrective_action'].with_user(self.u2).create({
            'ccar': self.ccar_office.id,
            'corrective_action': 'new action',
        })
        self.assertTrue(rec.id)

    def test_u2_dc_cannot_create_ca_for_other_office_ccar(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.ccar_corrective_action'].with_user(self.u2).create({
                'ccar': self.ccar_b.id,
            })


class TestCCAREffectivenessAccess(ISOAccessBase):
    """
    ccar_correction_effectiveness and ccar_corrective_action_effectiveness:
      IA   → CRUD, assigned
      DC   → R only, own office
      Staff → R only, all
    """

    def test_u0_no_access_correction_eff(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ccar_correction_effectiveness', self.u0)

    def test_u0_no_access_ca_eff(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ccar_corrective_action_effectiveness', self.u0)

    def test_u1_ia_sees_assigned_correction_eff(self):
        results = self._search('upmin_iso.ccar_correction_effectiveness', self.u1)
        self.assertIn(self.ce_a, results)  # ce_a → ccar_verif → audit_a (u1 assigned)

    def test_u2_dc_sees_own_office_correction_eff(self):
        results = self._search('upmin_iso.ccar_correction_effectiveness', self.u2)
        self.assertIn(self.ce_a, results)  # ccar_verif → dept_a

    def test_u4_staff_sees_all_correction_eff(self):
        results = self._search('upmin_iso.ccar_correction_effectiveness', self.u4)
        self.assertIn(self.ce_a, results)

    def test_u2_dc_cannot_write_correction_eff(self):
        # DC has perm_write=0 for correction_effectiveness
        with self.assertRaises(AccessError):
            self.ce_a.with_user(self.u2).write({'correction': 'attempted'})

    def test_u4_staff_cannot_write_correction_eff(self):
        with self.assertRaises(AccessError):
            self.ce_a.with_user(self.u4).write({'correction': 'attempted'})

    def test_u1_ia_can_write_assigned_correction_eff(self):
        self.ce_a.with_user(self.u1).write({'correction': 'ia update'})

    def test_u1_ia_can_create_correction_eff_for_assigned_ccar(self):
        rec = self.env['upmin_iso.ccar_correction_effectiveness'].with_user(self.u1).create({
            'ccar': self.ccar_verif.id,
        })
        self.assertTrue(rec.id)

    def test_u6_staff_ia_can_write_assigned_correction_eff(self):
        # Staff(R) + IA(CRUD assigned) → write allowed for assigned
        self.ce_a.with_user(self.u6).write({'correction': 'staff-ia update'})

    def test_u5_staff_dc_cannot_write_correction_eff(self):
        # Staff(R) + DC(R) → still R only
        with self.assertRaises(AccessError):
            self.ce_a.with_user(self.u5).write({'correction': 'attempted'})

    # ── ccar_corrective_action_effectiveness mirrors correction_effectiveness ─

    def test_u1_ia_sees_assigned_ca_eff(self):
        results = self._search('upmin_iso.ccar_corrective_action_effectiveness', self.u1)
        self.assertIn(self.cae_a, results)

    def test_u2_dc_cannot_write_ca_eff(self):
        with self.assertRaises(AccessError):
            self.cae_a.with_user(self.u2).write({'corrective_action': 'attempted'})

    def test_u1_ia_can_write_assigned_ca_eff(self):
        self.cae_a.with_user(self.u1).write({'corrective_action': 'ia ca update'})


class TestCCARChatterAccess(ISOAccessBase):
    """All users with read access to a CCAR can post to the chatter."""

    def _post_message(self, record, user):
        return record.with_user(user).message_post(
            body='Test chatter message',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def test_dc_can_post_at_verification_status(self):
        # u2 (DC) has read-only access at 'verification' — must be able to post
        msg = self._post_message(self.ccar_verif, self.u2)
        self.assertEqual(msg.author_id, self.u2.partner_id)

    def test_ia_can_post_at_office_status(self):
        # u1 (IA) has read-only access at 'office' — must be able to post
        msg = self._post_message(self.ccar_office, self.u1)
        self.assertEqual(msg.author_id, self.u1.partner_id)

    def test_dc_can_post_at_creation_status(self):
        msg = self._post_message(self.ccar_creation, self.u2)
        self.assertEqual(msg.author_id, self.u2.partner_id)

    def test_ia_can_post_at_creation_status(self):
        msg = self._post_message(self.ccar_creation, self.u1)
        self.assertEqual(msg.author_id, self.u1.partner_id)

    def test_staff_can_always_post(self):
        msg = self._post_message(self.ccar_verif, self.u4)
        self.assertEqual(msg.author_id, self.u4.partner_id)

    def test_cannot_post_without_read_access(self):
        # u2 (DC dept_a) cannot read ccar_b (dept_b) — should fail
        with self.assertRaises(AccessError):
            self._post_message(self.ccar_b, self.u2)

    def test_plain_user_cannot_post(self):
        with self.assertRaises(AccessError):
            self._post_message(self.ccar_creation, self.u0)

    # ── Followers widget (message_subscribe) ─────────────────────────────────
    # The chatter "Followers" widget calls ``message_subscribe`` to add /
    # remove followers. The default Odoo implementation requires
    # ``check_access_rule('write')`` when adding a partner other than
    # yourself. CCAR's ir.rule records grant unconditional write access to
    # any CCAR a Doc Controller / Internal Auditor can read — status-based
    # write eligibility is enforced separately in ``CCAR.write()`` — so this
    # check passes for any user who can read the record, at any status.
    # These tests pin that behavior.

    def _add_follower(self, record, user, partner):
        return record.with_user(user).message_subscribe(partner_ids=[partner.id])

    def test_dc_can_follow_self_at_any_status(self):
        # u2 (DC dept_a) following ccar_creation (status=creation) — would
        # raise before the message_subscribe override.
        self._add_follower(self.ccar_creation, self.u2, self.u2.partner_id)
        self.assertIn(
            self.u2.partner_id,
            self.ccar_creation.message_follower_ids.mapped("partner_id"),
        )

    def test_dc_can_add_other_follower_at_creation_status(self):
        # The pre-fix bug: u2 trying to add u1 as a follower at
        # status=creation raised AccessError because message_subscribe
        # demanded write access and rule_doc_controller_write_office
        # only allowed writes at status in ('office', 'office2').
        other_partner = self.u1.partner_id
        self._add_follower(self.ccar_creation, self.u2, other_partner)
        self.assertIn(
            other_partner,
            self.ccar_creation.message_follower_ids.mapped("partner_id"),
        )

    def test_ia_can_add_other_follower_at_creation_status(self):
        # Same shape for Internal Auditor: rule_internal_auditor_write
        # only allowed writes at status='verification', so a chatter
        # follower add at 'creation' used to fail.
        other_partner = self.u2.partner_id
        self._add_follower(self.ccar_creation, self.u1, other_partner)
        self.assertIn(
            other_partner,
            self.ccar_creation.message_follower_ids.mapped("partner_id"),
        )

    def test_cannot_follow_without_read_access(self):
        # u2 (DC dept_a) cannot read ccar_b (dept_b). message_subscribe
        # returns False silently in that case (matches the parent class
        # behavior), and no follower is added.
        result = self._add_follower(self.ccar_b, self.u2, self.u2.partner_id)
        self.assertFalse(result)
        self.assertFalse(
            self.ccar_b.sudo().message_follower_ids.filtered(
                lambda f: f.partner_id == self.u2.partner_id
            )
        )

    def test_plain_user_cannot_follow(self):
        # u0 has no ISO group, so read access is denied on
        # ccar_creation. message_subscribe returns False silently (no
        # follower added) — that's the expected user-facing behavior
        # for a user with no access to the record.
        result = self._add_follower(self.ccar_creation, self.u0, self.u0.partner_id)
        self.assertFalse(result)
        self.assertFalse(
            self.ccar_creation.sudo().message_follower_ids.filtered(
                lambda f: f.partner_id == self.u0.partner_id
            )
        )

    # ── Schedule activity (mail.activity.create auto-subscribes) ─────────────
    # ``mail.activity.create`` calls ``message_subscribe`` on the parent
    # record to auto-subscribe the assigned user. The pre-fix bug meant
    # DC/IA could not schedule activities on CCARs outside their
    # status-gated write window. Pin that activity creation now works
    # for any user who can read the CCAR.

    def _schedule_activity(self, ccar, user, assigned_user):
        return self.env["mail.activity"].with_user(user).create({
            "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
            "res_model_id": self.env["ir.model"]._get_id("upmin_iso.ccar"),
            "res_id": ccar.id,
            "user_id": assigned_user.id,
            "date_deadline": "2026-12-31",
            "summary": "Test activity",
        })

    def test_dc_can_schedule_activity_at_creation_status(self):
        # u2 (DC) scheduling an activity on ccar_creation (status=creation)
        # used to fail with AccessError because mail.activity.create
        # called message_subscribe on the parent and the write rule
        # didn't grant write to u2 here.
        act = self._schedule_activity(self.ccar_creation, self.u2, self.u2)
        self.assertTrue(act.id)

    def test_ia_can_schedule_activity_at_office_status(self):
        # u1 (IA) on ccar_office (status=office) — IA's write rule only
        # covered status='verification', so the activity create path
        # used to fail here too.
        act = self._schedule_activity(self.ccar_office, self.u1, self.u1)
        self.assertTrue(act.id)

    def test_dc_cannot_schedule_activity_on_unread_ccar(self):
        # u2 (DC dept_a) cannot read ccar_b (dept_b). The activity
        # create path checks the assigned user's read access via
        # _check_access_assignation and raises UserError when the
        # assignee can't see the parent record. (Odoo's assertRaises
        # only accepts a single exception class, so we use a manual
        # try/except.)
        try:
            self._schedule_activity(self.ccar_b, self.u2, self.u2)
        except (AccessError, UserError):
            pass
        else:
            self.fail("Expected AccessError or UserError, got none")

    def test_plain_user_cannot_schedule_activity(self):
        # u0 is a plain user with no ISO group, so they cannot read
        # ccar_creation. The activity create path raises UserError via
        # _check_access_assignation.
        try:
            self._schedule_activity(self.ccar_creation, self.u0, self.u0)
        except (AccessError, UserError):
            pass
        else:
            self.fail("Expected AccessError or UserError, got none")
