"""
Access tests for remaining sections:
  - ISO Clauses      (all read, staff CRUD)
  - Audit Period     (staff only, full CRUD)
  - Dashboard        (staff only)
  - Directory        (all read; DC filtered by trained=True for non-staff)
  - Significant Risks (menu-level staff only; underlying model is ROR — tested separately)
"""

from odoo.exceptions import AccessError

from .common import ISOAccessBase


class TestISOClauseAccess(ISOAccessBase):
    """
    Model-level: base.group_user R, Staff CRUD, IA R, DC R
    All users can read; only Staff can write/create/delete.
    """

    def test_all_users_can_read_clauses(self):
        for u in self.all_users():
            try:
                clauses = self.env['upmin_iso.iso_clause'].with_user(u).search([])
                # Module data populates clauses; result may be empty in test DB
                # but no AccessError should be raised
            except AccessError:
                self.fail(f"User {u.name} should be able to read ISO clauses but got AccessError")

    def test_u0_cannot_write_clause(self):
        clause = self.env['upmin_iso.iso_clause'].sudo().search([], limit=1)
        if not clause:
            self.skipTest("No ISO clause records found")
        with self.assertRaises(AccessError):
            clause.with_user(self.u0).write({'clause_title': 'attempt'})

    def test_u1_ia_cannot_write_clause(self):
        clause = self.env['upmin_iso.iso_clause'].sudo().search([], limit=1)
        if not clause:
            self.skipTest("No ISO clause records found")
        with self.assertRaises(AccessError):
            clause.with_user(self.u1).write({'clause_title': 'attempt'})

    def test_u2_dc_cannot_write_clause(self):
        clause = self.env['upmin_iso.iso_clause'].sudo().search([], limit=1)
        if not clause:
            self.skipTest("No ISO clause records found")
        with self.assertRaises(AccessError):
            clause.with_user(self.u2).write({'clause_title': 'attempt'})

    def test_u4_staff_can_write_clause(self):
        clause = self.env['upmin_iso.iso_clause'].sudo().search([], limit=1)
        if not clause:
            self.skipTest("No ISO clause records found")
        original = clause.clause_title
        clause.with_user(self.u4).write({'clause_title': original})  # no-op write

    def test_u0_cannot_create_clause(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.iso_clause'].with_user(self.u0).create({
                'clause_number': '99',
                'clause_title': 'Test Clause',
            })

    def test_u4_staff_can_create_clause(self):
        rec = self.env['upmin_iso.iso_clause'].with_user(self.u4).create({
            'clause_number': '99.99',
            'clause_title': 'Test Clause',
        })
        self.assertTrue(rec.id)


class TestAuditPeriodAccess(ISOAccessBase):
    """
    Model-level: Staff only — full CRUD.
    No other group has any access.
    """

    def test_u0_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.audit_period', self.u0)

    def test_u1_ia_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.audit_period', self.u1)

    def test_u2_dc_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.audit_period', self.u2)

    def test_u3_ia_dc_no_access(self):
        with self.assertRaises(AccessError):
            self._search('upmin_iso.audit_period', self.u3)

    def test_u4_staff_can_read(self):
        results = self._search('upmin_iso.audit_period', self.u4)
        self.assertIn(self.period, results)

    def test_u5_staff_dc_can_read(self):
        results = self._search('upmin_iso.audit_period', self.u5)
        self.assertIn(self.period, results)

    def test_u6_staff_ia_can_read(self):
        results = self._search('upmin_iso.audit_period', self.u6)
        self.assertIn(self.period, results)

    def test_u7_all_can_read(self):
        results = self._search('upmin_iso.audit_period', self.u7)
        self.assertIn(self.period, results)

    def test_u4_staff_can_create_and_write(self):
        p = self.env['upmin_iso.audit_period'].with_user(self.u4).create({
            'audit_start_date': '2025-01-01',
            'audit_end_date': '2025-01-31',
        })
        self.assertTrue(p.id)
        p.with_user(self.u4).write({'is_finalized': True})

    def test_u4_staff_can_delete(self):
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2025-02-01',
            'audit_end_date': '2025-02-28',
        })
        p.with_user(self.u4).unlink()

    def test_u1_ia_cannot_create(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.audit_period'].with_user(self.u1).create({
                'audit_start_date': '2025-03-01',
                'audit_end_date': '2025-03-31',
            })


class TestDashboardAccess(ISOAccessBase):
    """
    Dashboard (TransientModel): Staff only.
    """

    def test_u0_no_access(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.iso_dashboard'].with_user(self.u0).create({})

    def test_u1_ia_no_access(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.iso_dashboard'].with_user(self.u1).create({})

    def test_u2_dc_no_access(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.iso_dashboard'].with_user(self.u2).create({})

    def test_u3_ia_dc_no_access(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.iso_dashboard'].with_user(self.u3).create({})

    def test_u4_staff_can_access(self):
        rec = self.env['upmin_iso.iso_dashboard'].with_user(self.u4).create({})
        self.assertTrue(rec.id)

    def test_u5_staff_dc_can_access(self):
        rec = self.env['upmin_iso.iso_dashboard'].with_user(self.u5).create({})
        self.assertTrue(rec.id)

    def test_u7_all_can_access(self):
        rec = self.env['upmin_iso.iso_dashboard'].with_user(self.u7).create({})
        self.assertTrue(rec.id)


class TestDirectoryAccess(ISOAccessBase):
    """
    Internal Auditor / Unit Head:
      All users — R only (no ir.rule row filter for non-staff)
      Staff     — CRUD

    Document Controller:
      All users — R only, BUT ir.rule for base.group_user restricts to trained=True
      Staff     — R all (no row filter), CRUD
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a UH entry (for read tests — no group grants involved since
        # unit_head is managed separately from DC/IA)
        cls.dept_managed = cls.env['hr.department'].create({'name': '[Test] Managed Dept'})
        cls.emp_manager = cls.env['hr.employee'].create({
            'name': 'Test Manager',
            'department_id': cls.dept_a.id,
        })
        cls.dept_managed.manager_id = cls.emp_manager.id
        cls.uh_rec = cls.env['upmin_iso.unit_head'].sudo().create({
            'name': cls.emp_manager.id,
            'office': [(4, cls.dept_managed.id)],
        })
        # Untrained DC record
        cls.dc_untrained = cls.env['upmin_iso.document_controller'].sudo().create({
            'name': cls.emp_u4.id,  # emp_u4 has no DC record yet; staff emp
        })
        # Trained DC record
        cls.dc_u2.sudo().write({'trained': True})   # mark u2's DC as trained

    def test_all_users_can_read_internal_auditors(self):
        for u in self.all_users():
            try:
                self.env['upmin_iso.internal_auditor'].with_user(u).search([])
            except AccessError:
                self.fail(f"{u.name} should be able to read IA directory")

    def test_all_users_can_read_unit_heads(self):
        for u in self.all_users():
            try:
                self.env['upmin_iso.unit_head'].with_user(u).search([])
            except AccessError:
                self.fail(f"{u.name} should be able to read UH directory")

    def test_non_staff_can_read_dc_directory(self):
        for u in [self.u0, self.u1, self.u2, self.u3]:
            try:
                self.env['upmin_iso.document_controller'].with_user(u).search([])
            except AccessError:
                self.fail(f"{u.name} should be able to read DC directory")

    def test_non_staff_only_see_trained_dcs(self):
        # dc_u2 is trained=True; dc_untrained is trained=False
        for u in [self.u0, self.u1, self.u3]:
            results = self.env['upmin_iso.document_controller'].with_user(u).search([])
            self.assertIn(self.dc_u2, results,
                          f"{u.name} should see trained DC")
            self.assertNotIn(self.dc_untrained, results,
                             f"{u.name} should NOT see untrained DC")

    def test_staff_sees_all_dcs_including_untrained(self):
        for u in self.staff_users():
            results = self.env['upmin_iso.document_controller'].with_user(u).search([])
            self.assertIn(self.dc_u2, results)
            self.assertIn(self.dc_untrained, results)

    def test_non_staff_cannot_write_ia_directory(self):
        with self.assertRaises(AccessError):
            self.ia_u1.with_user(self.u0).write({'trained': True})
        with self.assertRaises(AccessError):
            self.ia_u1.with_user(self.u2).write({'trained': True})

    def test_staff_can_write_ia_directory(self):
        self.ia_u1.with_user(self.u4).write({'trained': True})

    def test_non_staff_cannot_write_uh_directory(self):
        with self.assertRaises(AccessError):
            self.uh_rec.with_user(self.u0).write({'office': [(5,)]})
        with self.assertRaises(AccessError):
            self.uh_rec.with_user(self.u2).write({'office': [(5,)]})

    def test_staff_can_write_uh_directory(self):
        # Staff has model-level write on UH (even if the UI enforces read-only)
        self.uh_rec.with_user(self.u4).write({'office': [(4, self.dept_managed.id)]})

    def test_non_staff_cannot_create_dc(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.document_controller'].with_user(self.u0).create({
                'name': self.emp_u4.id,
            })

    def test_staff_can_create_ia(self):
        emp_new = self.env['hr.employee'].sudo().create({
            'name': '[Test] New IA Emp', 'department_id': self.dept_b.id,
        })
        rec = self.env['upmin_iso.internal_auditor'].with_user(self.u4).create({
            'name': emp_new.id,
        })
        self.assertTrue(rec.id)
