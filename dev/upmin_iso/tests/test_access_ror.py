"""
Access tests for upmin_iso.ror and upmin_iso.ror_rating.

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


class TestRORAccess(ISOAccessBase):

    # ── Visibility ────────────────────────────────────────────────────────────

    def test_u0_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ror', self.u0)

    def test_u1_ia_no_read_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ror', self.u1)

    def test_u2_dc_sees_own_office_only(self):
        results = self._search('upmin_iso.ror', self.u2)
        self.assertIn(self.ror_a, results)
        self.assertNotIn(self.ror_b, results)

    def test_u3_ia_dc_sees_own_office_only(self):
        # U3's DC scope is dept_b
        results = self._search('upmin_iso.ror', self.u3)
        self.assertIn(self.ror_b, results)
        self.assertNotIn(self.ror_a, results)

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.ror', self.u4)
        self.assertIn(self.ror_a, results)
        self.assertIn(self.ror_b, results)

    def test_u5_staff_dc_reads_all(self):
        results = self._search('upmin_iso.ror', self.u5)
        self.assertIn(self.ror_a, results)
        self.assertIn(self.ror_b, results)

    def test_u6_staff_ia_reads_all(self):
        results = self._search('upmin_iso.ror', self.u6)
        self.assertIn(self.ror_a, results)
        self.assertIn(self.ror_b, results)

    def test_u7_all_reads_all(self):
        results = self._search('upmin_iso.ror', self.u7)
        self.assertIn(self.ror_a, results)
        self.assertIn(self.ror_b, results)

    # ── Write ─────────────────────────────────────────────────────────────────

    def test_u2_dc_can_write_own_office(self):
        self.ror_a.with_user(self.u2).write({'related_swot': False})

    def test_u2_dc_cannot_write_other_office(self):
        with self.assertRaises(AccessError):
            self.ror_b.with_user(self.u2).write({'related_swot': False})

    def test_u4_staff_can_write_any_office(self):
        # Staff has full CRUD on all ROR records, not just own office.
        self.ror_a.with_user(self.u4).write({'related_swot': False})

    def test_u5_staff_dc_can_write_own_office(self):
        self.ror_a.with_user(self.u5).write({'related_swot': False})

    def test_u5_staff_dc_can_write_other_office(self):
        # Staff grants full CRUD regardless of DC office scope.
        self.ror_b.with_user(self.u5).write({'related_swot': False})

    def test_u6_staff_ia_can_write_any_office(self):
        self.ror_a.with_user(self.u6).write({'related_swot': False})

    def test_u7_all_can_write_own_office(self):
        # U7's DC scope is dept_b
        self.ror_b.with_user(self.u7).write({'related_swot': False})

    def test_u7_all_can_write_other_office(self):
        # ror_a is dept_a — outside U7's DC scope, but staff has full CRUD.
        self.ror_a.with_user(self.u7).write({'related_swot': False})

    # ── Create ────────────────────────────────────────────────────────────────

    def test_u0_cannot_create(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.ror'].with_user(self.u0).create(
                {'office': self.dept_a.id}
            )

    def test_u4_staff_can_create(self):
        rec = self.env['upmin_iso.ror'].with_user(self.u4).create(
            {'office': self.dept_a.id}
        )
        self.assertTrue(rec.id)

    def test_u2_dc_can_create_own_office(self):
        rec = self.env['upmin_iso.ror'].with_user(self.u2).create(
            {'office': self.dept_a.id}
        )
        self.assertTrue(rec.id)

    def test_u2_dc_cannot_create_other_office(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.ror'].with_user(self.u2).create(
                {'office': self.dept_b.id}
            )

    # ── Delete ────────────────────────────────────────────────────────────────

    def test_u4_staff_can_delete(self):
        tmp = self.env['upmin_iso.ror'].sudo().create({'office': self.dept_a.id})
        tmp.with_user(self.u4).unlink()

    def test_u2_dc_can_delete_own_office(self):
        tmp = self.env['upmin_iso.ror'].sudo().create({'office': self.dept_a.id})
        tmp.with_user(self.u2).unlink()

    def test_u2_dc_cannot_delete_other_office(self):
        tmp = self.env['upmin_iso.ror'].sudo().create({'office': self.dept_b.id})
        with self.assertRaises(AccessError):
            tmp.with_user(self.u2).unlink()


class TestRORRatingAccess(ISOAccessBase):
    """
    ROR Rating follows identical rules to ROR:
      Staff  → R only, all records
      DC     → CRUD, own office (via issue→ror/swot→office chain)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a ROR rating linked through swot_line → ror_a
        # The ir.rule resolves office via issue.ror_id.office or issue.swot_id.office
        # We use a swot_line linked to ror_a so office=dept_a
        cls.swot_line_a = cls.env['upmin_iso.swot_line'].sudo().create({
            'swot_id': cls.swot_a.id,
            'ror_id': cls.ror_a.id,
            'swot_type': 'W',
            'description': '[Test] risk item A',
        })
        cls.swot_line_b = cls.env['upmin_iso.swot_line'].sudo().create({
            'swot_id': cls.swot_b.id,
            'ror_id': cls.ror_b.id,
            'swot_type': 'W',
            'description': '[Test] risk item B',
        })
        cls.rating_a = cls.env['upmin_iso.ror_rating'].sudo().create({
            'issue': cls.swot_line_a.id,
            'review_date': '2024-03-31',
        })
        cls.rating_b = cls.env['upmin_iso.ror_rating'].sudo().create({
            'issue': cls.swot_line_b.id,
            'review_date': '2024-03-31',
        })

    def test_u0_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ror_rating', self.u0)

    def test_u1_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.ror_rating', self.u1)

    def test_u2_dc_sees_own_office_only(self):
        results = self._search('upmin_iso.ror_rating', self.u2)
        self.assertIn(self.rating_a, results)
        self.assertNotIn(self.rating_b, results)

    def test_u4_staff_reads_all(self):
        results = self._search('upmin_iso.ror_rating', self.u4)
        self.assertIn(self.rating_a, results)
        self.assertIn(self.rating_b, results)

    def test_u4_staff_can_write(self):
        self.rating_a.with_user(self.u4).write({'progress': 50})

    def test_u2_dc_can_write_own_office(self):
        self.rating_a.with_user(self.u2).write({'progress': 50})

    def test_u2_dc_cannot_write_other_office(self):
        with self.assertRaises(AccessError):
            self.rating_b.with_user(self.u2).write({'progress': 50})
