"""
Access tests for upmin_iso.swot and upmin_iso.tows.

Model-level (ir.model.access):
  group_iso_staff          — CRUD
  group_iso_doc_controller — CRUD

Row-level (ir.rule):
  DC    → own office only (CRUD)
  Staff → all records, full CRUD

Expected matrix
---------------
           Read        Write/Create/Delete
  U0       ✗           ✗
  U1       ✗           ✗
  U2       own office  own office
  U3       own office  own office
  U4       all         all
  U5       all         all
  U6       all         all
  U7       all         all
"""

from odoo.exceptions import AccessError

from .common import ISOAccessBase


class TestSWOTAccess(ISOAccessBase):

    # ── Visibility ────────────────────────────────────────────────────────────

    def test_u0_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.swot', self.u0)

    def test_u1_ia_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.swot', self.u1)

    def test_u2_dc_sees_own_office_only(self):
        results = self._search('upmin_iso.swot', self.u2)
        self.assertIn(self.swot_a, results)
        self.assertNotIn(self.swot_b, results)

    def test_u3_ia_dc_sees_own_office_only(self):
        # U3's employee is in dept_b → DC scope is dept_b
        results = self._search('upmin_iso.swot', self.u3)
        self.assertIn(self.swot_b, results)
        self.assertNotIn(self.swot_a, results)

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.swot', self.u4)
        self.assertIn(self.swot_a, results)
        self.assertIn(self.swot_b, results)

    def test_u5_staff_dc_reads_all(self):
        results = self._search('upmin_iso.swot', self.u5)
        self.assertIn(self.swot_a, results)
        self.assertIn(self.swot_b, results)

    def test_u6_staff_ia_reads_all(self):
        results = self._search('upmin_iso.swot', self.u6)
        self.assertIn(self.swot_a, results)
        self.assertIn(self.swot_b, results)

    def test_u7_all_reads_all(self):
        results = self._search('upmin_iso.swot', self.u7)
        self.assertIn(self.swot_a, results)
        self.assertIn(self.swot_b, results)

    # ── Write ─────────────────────────────────────────────────────────────────

    def test_u2_dc_can_write_own_office(self):
        self.swot_a.with_user(self.u2).write({'year': '2025'})

    def test_u2_dc_cannot_write_other_office(self):
        with self.assertRaises(AccessError):
            self.swot_b.with_user(self.u2).write({'year': '2025'})

    def test_u3_ia_dc_can_write_own_office(self):
        self.swot_b.with_user(self.u3).write({'year': '2025'})

    def test_u4_staff_can_write_any_office(self):
        # Staff has full CRUD on all SWOT records, not just own office.
        self.swot_a.with_user(self.u4).write({'year': '2025'})

    def test_u5_staff_dc_can_write_own_office(self):
        self.swot_a.with_user(self.u5).write({'year': '2025'})

    def test_u5_staff_dc_can_write_other_office(self):
        # Staff grants full CRUD regardless of DC office scope.
        self.swot_b.with_user(self.u5).write({'year': '2025'})

    def test_u6_staff_ia_can_write_any_office(self):
        self.swot_a.with_user(self.u6).write({'year': '2025'})

    def test_u7_all_can_write_own_office(self):
        # U7's DC scope is dept_b
        self.swot_b.with_user(self.u7).write({'year': '2025'})

    def test_u7_all_can_write_other_office(self):
        # swot_a is dept_a — outside U7's DC scope, but staff has full CRUD.
        self.swot_a.with_user(self.u7).write({'year': '2025'})

    # ── Create ────────────────────────────────────────────────────────────────

    def test_u0_cannot_create(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.swot'].with_user(self.u0).create(
                {'year': '2099', 'office': self.dept_a.id}
            )

    def test_u1_cannot_create(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.swot'].with_user(self.u1).create(
                {'year': '2099', 'office': self.dept_a.id}
            )

    def test_u4_staff_can_create(self):
        rec = self.env['upmin_iso.swot'].with_user(self.u4).create(
            {'year': '2099', 'office': self.dept_a.id}
        )
        self.assertTrue(rec.id)

    def test_u2_dc_can_create_own_office(self):
        rec = self.env['upmin_iso.swot'].with_user(self.u2).create(
            {'year': '2099', 'office': self.dept_a.id}
        )
        self.assertTrue(rec.id)

    def test_u2_dc_cannot_create_other_office(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.swot'].with_user(self.u2).create(
                {'year': '2099', 'office': self.dept_b.id}
            )

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_u4_staff_can_delete(self):
        tmp = self.env['upmin_iso.swot'].sudo().create(
            {'year': '2098', 'office': self.dept_a.id}
        )
        tmp.with_user(self.u4).unlink()

    def test_u2_dc_can_delete_own_office(self):
        tmp = self.env['upmin_iso.swot'].sudo().create(
            {'year': '2098', 'office': self.dept_a.id}
        )
        tmp.with_user(self.u2).unlink()

    def test_u2_dc_cannot_delete_other_office(self):
        tmp = self.env['upmin_iso.swot'].sudo().create(
            {'year': '2098', 'office': self.dept_b.id}
        )
        with self.assertRaises(AccessError):
            tmp.with_user(self.u2).unlink()


class TestTOWSAccess(ISOAccessBase):
    """TOWS follows the same rules as SWOT (same groups, same ir.rule pattern)."""

    def test_u0_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.tows', self.u0)

    def test_u1_ia_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.tows', self.u1)

    def test_u2_dc_sees_own_office_only(self):
        results = self._search('upmin_iso.tows', self.u2)
        self.assertIn(self.tows_a, results)
        self.assertNotIn(self.tows_b, results)

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.tows', self.u4)
        self.assertIn(self.tows_a, results)
        self.assertIn(self.tows_b, results)

    def test_u4_staff_can_write(self):
        # tows_a already exists in fixture — write to it directly (no new record needed)
        self.tows_a.with_user(self.u4).write({'swot': self.swot_a.id})

    def test_u2_dc_can_write_own_office(self):
        # Re-writing swot to the same value is valid and confirms write access
        self.tows_a.with_user(self.u2).write({'swot': self.swot_a.id})

    def test_u2_dc_cannot_write_other_office(self):
        with self.assertRaises(AccessError):
            self.tows_b.with_user(self.u2).write({'swot': self.swot_b.id})

    def test_u5_staff_dc_can_write_own_office(self):
        self.tows_a.with_user(self.u5).write({'swot': self.swot_a.id})

    def test_u6_staff_ia_can_write(self):
        self.tows_a.with_user(self.u6).write({'swot': self.swot_a.id})
