"""
Access tests for upmin_iso.audit_info and upmin_iso.audit_finding.

Audit Info
----------
Model-level:
  Staff          — CRUD
  DC             — R only  (perm_write/create/unlink = 0)
  IA             — R + W   (no create/delete)

Row-level:
  DC  → office_to_audit matches own dept/admin_dept/ancestors
  IA  → internal_auditors.name.user_id = current user
  Staff → all

Expected matrix (audit_a = dept_a, assigned; audit_b = dept_b, unassigned)
--------------------------------------------------------------------------
           Read         Write       Create/Delete
  U0       ✗            ✗           ✗
  U1       assigned     assigned    ✗
  U2       own office   ✗           ✗
  U3       assigned OR  assigned    ✗
           own office
  U4       all          CRUD        CRUD
  U5       all          CRUD        CRUD
  U6       all          CRUD        CRUD
  U7       all          CRUD        CRUD

Audit Finding
-------------
Model-level:
  Staff  — R only
  IA     — CRUD
  DC     — R only

Row-level:
  IA  → audit_info.internal_auditors.name.user_id = current user
  DC  → audit_info.office_to_audit matches own dept/ancestors
  Staff → all

Expected matrix
---------------
           Read         Write/Create/Delete
  U0       ✗            ✗
  U1       assigned     assigned only
  U2       own office   ✗
  U3       assigned OR  assigned only
           own office
  U4       all          all (staff)
  U5       all          all (staff)
  U6       all          all (staff+IA)
  U7       all          all (staff+IA)
"""

from odoo.exceptions import AccessError

from .common import ISOAccessBase


class TestAuditInfoAccess(ISOAccessBase):

    # ── Visibility ────────────────────────────────────────────────────────────

    def test_u0_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.audit_info', self.u0)

    def test_u1_ia_sees_assigned_only(self):
        results = self._search('upmin_iso.audit_info', self.u1)
        self.assertIn(self.audit_a, results)      # u1 is an auditor in audit_a
        self.assertNotIn(self.audit_b, results)   # u1 not assigned to audit_b

    def test_u2_dc_sees_own_office_only(self):
        results = self._search('upmin_iso.audit_info', self.u2)
        self.assertIn(self.audit_a, results)      # audit_a office = dept_a
        self.assertNotIn(self.audit_b, results)   # audit_b office = dept_b

    def test_u3_ia_dc_sees_union(self):
        # U3 is IA (assigned to audit_a) + DC (dept_b → audit_b has office=dept_b)
        # Union of both rules → sees BOTH
        results = self._search('upmin_iso.audit_info', self.u3)
        self.assertIn(self.audit_a, results)   # IA: assigned
        self.assertIn(self.audit_b, results)   # DC: office_to_audit=dept_b = own office

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.audit_info', self.u4)
        self.assertIn(self.audit_a, results)
        self.assertIn(self.audit_b, results)

    def test_u5_staff_dc_reads_all(self):
        results = self._search('upmin_iso.audit_info', self.u5)
        self.assertIn(self.audit_a, results)
        self.assertIn(self.audit_b, results)

    def test_u6_staff_ia_reads_all(self):
        results = self._search('upmin_iso.audit_info', self.u6)
        self.assertIn(self.audit_a, results)
        self.assertIn(self.audit_b, results)

    def test_u7_all_reads_all(self):
        results = self._search('upmin_iso.audit_info', self.u7)
        self.assertIn(self.audit_a, results)
        self.assertIn(self.audit_b, results)

    # ── Write ─────────────────────────────────────────────────────────────────

    def test_u2_dc_cannot_write(self):
        # DC has model-level perm_write=0 for audit_info
        with self.assertRaises(AccessError):
            self.audit_a.with_user(self.u2).write({'audit_date': '2024-01-10'})

    def test_u1_ia_can_write_assigned(self):
        # IA has model-level perm_write=1, rule restricts to assigned only
        self.audit_a.with_user(self.u1).write({'audit_date': '2024-01-10'})

    def test_u1_ia_cannot_write_unassigned(self):
        with self.assertRaises(AccessError):
            self.audit_b.with_user(self.u1).write({'audit_date': '2024-01-10'})

    def test_u3_ia_dc_can_write_assigned(self):
        self.audit_a.with_user(self.u3).write({'audit_date': '2024-01-10'})

    def test_u4_staff_can_write(self):
        self.audit_a.with_user(self.u4).write({'audit_date': '2024-01-10'})
        self.audit_b.with_user(self.u4).write({'audit_date': '2024-01-10'})

    # ── Create ────────────────────────────────────────────────────────────────

    def test_u1_ia_cannot_create(self):
        # IA has perm_create=0 for audit_info
        with self.assertRaises(AccessError):
            self.env['upmin_iso.audit_info'].with_user(self.u1).create({
                'office_to_audit': self.dept_a.id,
                'audit_period': self.period.id,
            })

    def test_u2_dc_cannot_create(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.audit_info'].with_user(self.u2).create({
                'office_to_audit': self.dept_a.id,
                'audit_period': self.period.id,
            })

    def test_u4_staff_can_create(self):
        # Need a unique office+period combo — create a new period
        p2 = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-06-01',
            'audit_end_date': '2024-06-30',
        })
        rec = self.env['upmin_iso.audit_info'].with_user(self.u4).create({
            'office_to_audit': self.dept_a.id,
            'audit_period': p2.id,
        })
        self.assertTrue(rec.id)

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_u1_ia_cannot_delete(self):
        p2 = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-07-01',
            'audit_end_date': '2024-07-31',
        })
        tmp = self.env['upmin_iso.audit_info'].sudo().create({
            'office_to_audit': self.dept_a.id,
            'audit_period': p2.id,
            'internal_auditors': [(4, self.ia_u1.id)],
        })
        with self.assertRaises(AccessError):
            tmp.with_user(self.u1).unlink()

    def test_u4_staff_can_delete(self):
        p2 = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-08-01',
            'audit_end_date': '2024-08-31',
        })
        tmp = self.env['upmin_iso.audit_info'].sudo().create({
            'office_to_audit': self.dept_a.id,
            'audit_period': p2.id,
        })
        tmp.with_user(self.u4).unlink()


class TestAuditFindingAccess(ISOAccessBase):

    # ── Visibility ────────────────────────────────────────────────────────────

    def test_u0_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.audit_finding', self.u0)

    def test_u1_ia_sees_assigned_audit_findings_only(self):
        # nc_a1/c_a1 → audit_a (u1 is assigned); nc_b1 → audit_b (u1 not assigned)
        results = self._search('upmin_iso.audit_finding', self.u1)
        self.assertIn(self.nc_a1, results)
        self.assertNotIn(self.nc_b1, results)

    def test_u2_dc_sees_own_office_findings_only(self):
        results = self._search('upmin_iso.audit_finding', self.u2)
        self.assertIn(self.nc_a1, results)   # audit_a → dept_a
        self.assertNotIn(self.nc_b1, results) # audit_b → dept_b

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.audit_finding', self.u4)
        self.assertIn(self.nc_a1, results)
        self.assertIn(self.nc_b1, results)

    def test_u6_staff_ia_reads_all(self):
        results = self._search('upmin_iso.audit_finding', self.u6)
        self.assertIn(self.nc_a1, results)
        self.assertIn(self.nc_b1, results)

    # ── Write ─────────────────────────────────────────────────────────────────

    def test_u2_dc_cannot_write(self):
        # DC has perm_write=0 for audit_finding
        with self.assertRaises(AccessError):
            self.nc_a1.with_user(self.u2).write({'evidence': 'test evidence'})

    def test_u4_staff_can_write(self):
        self.nc_a1.with_user(self.u4).write({'evidence': 'test evidence'})

    def test_u1_ia_can_write_assigned_finding(self):
        self.nc_a1.with_user(self.u1).write({'evidence': 'confirmed finding'})

    def test_u1_ia_cannot_write_unassigned_finding(self):
        with self.assertRaises(AccessError):
            self.nc_b1.with_user(self.u1).write({'evidence': 'attempted'})

    def test_u6_staff_ia_can_write_assigned_finding(self):
        self.nc_a1.with_user(self.u6).write({'evidence': 'staff-ia finding'})

    def test_u6_staff_ia_can_write_unassigned_finding(self):
        # Staff rule (full CRUD) overrides IA-only restriction
        self.nc_b1.with_user(self.u6).write({'evidence': 'attempted'})

    # ── Create ────────────────────────────────────────────────────────────────

    def test_u2_dc_cannot_create_finding(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.audit_finding'].with_user(self.u2).create({
                'audit_info': self.audit_a.id,
                'auditor': self.u2.partner_id.id,
                'rating': 'c',
            })

    def test_u4_staff_can_create_finding(self):
        rec = self.env['upmin_iso.audit_finding'].with_user(self.u4).create({
            'audit_info': self.audit_a.id,
            'auditor': self.u4.partner_id.id,
            'rating': 'c',
        })
        self.assertTrue(rec.id)

    def test_u1_ia_can_create_finding_for_assigned_audit(self):
        rec = self.env['upmin_iso.audit_finding'].with_user(self.u1).create({
            'audit_info': self.audit_a.id,
            'auditor': self.u1.partner_id.id,
            'rating': 'ofi',
        })
        self.assertTrue(rec.id)

    def test_u1_ia_cannot_create_finding_for_unassigned_audit(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.audit_finding'].with_user(self.u1).create({
                'audit_info': self.audit_b.id,
                'auditor': self.u1.partner_id.id,
                'rating': 'c',
            })

    # ── Auditor conflict constraint ───────────────────────────────────────────

    def test_auditor_cannot_audit_own_office(self):
        """An IA assigned to audit their own office raises ValidationError."""
        from odoo.exceptions import ValidationError
        # ia_u1 is in dept_b; auditing dept_b (own office) should conflict
        p2 = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-10-01',
            'audit_end_date': '2024-10-31',
        })
        with self.assertRaises(ValidationError):
            self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_b.id,
                'audit_period': p2.id,
                'internal_auditors': [(4, self.ia_u1.id)],
            })

    def test_auditor_can_audit_different_office(self):
        """An IA auditing an office outside their own raises no error."""
        from odoo.exceptions import ValidationError
        # ia_u1 is in dept_b; auditing dept_a (different office) should be fine
        p2 = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-09-01',
            'audit_end_date': '2024-09-30',
        })
        try:
            rec = self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_a.id,
                'audit_period': p2.id,
                'internal_auditors': [(4, self.ia_u1.id)],
            })
            self.assertTrue(rec.id)
        except ValidationError:
            self.fail("ValidationError raised unexpectedly for cross-office audit.")
