"""
Access tests for CCAR and its sub-models.

┌─────────────────────────────────────────────────────────────────────────────┐
│ upmin_iso.ccar                                                              │
│ Model-level: Staff=CRUD, DC=R+W(no C/D), IA=R+W(no C/D)                   │
│ Row-level (read):                                                           │
│   DC  → own office                                                          │
│   IA  → auditors.name.user_id = current user                               │
│   Staff → all                                                               │
│ Row-level (write):                                                          │
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

from odoo.exceptions import AccessError

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
