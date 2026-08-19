"""
Tests for Unit Head sync logic and DC group perm guards.

Sync (action_sync_unit_heads)
------------------------------
1. Creates UH entries for all department managers.
2. Updates UH.office when managed depts change.
3. Deletes UH entries when employee no longer manages any dept.
4. Grants DC group to newly synced UH employees.
5. Does NOT revoke DC group during sync for employees removed from UH if
   they still have an active DC record.

Group perm guards (cross-model _revoke_group)
---------------------------------------------
6. Deleting a UH record revokes DC group (employee not in DC).
7. Deleting a UH record does NOT revoke DC group if employee is still in DC.
8. Deleting a DC record revokes DC group (employee not in UH).
9. Deleting a DC record does NOT revoke DC group if employee is still in UH.
"""

from .common import ISOAccessBase


class TestUnitHeadSync(ISOAccessBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Extra employees who manage departments — not linked to any ISO user
        cls.emp_mgr_a = cls.env['hr.employee'].create({
            'name': '[Test] Manager A',
            'department_id': cls.dept_a.id,
            'work_email': 'test.manager.a@iso.test',
        })
        cls.emp_mgr_b = cls.env['hr.employee'].create({
            'name': '[Test] Manager B',
            'department_id': cls.dept_b.id,
            'work_email': 'test.manager.b@iso.test',
        })
        cls.dept_c = cls.env['hr.department'].create({'name': '[Test] Dept C'})

        # Set dept managers (simulates what sync reads from hr.department)
        cls.dept_a.manager_id = cls.emp_mgr_a.id
        cls.dept_b.manager_id = cls.emp_mgr_b.id

    def _sync(self):
        return self.env['upmin_iso.unit_head'].sudo().action_sync_unit_heads()

    def _uh_for(self, emp):
        return self.env['upmin_iso.unit_head'].sudo().search([('name', '=', emp.id)], limit=1)

    def _has_dc_group(self, user):
        group = self.env.ref('upmin_iso.group_iso_doc_controller')
        return group in user.sudo().groups_id

    # ── Sync: create ──────────────────────────────────────────────────────────

    def test_sync_creates_uh_for_dept_managers(self):
        # Remove any pre-existing UH entries for our managers
        self.env['upmin_iso.unit_head'].sudo().search([
            ('name', 'in', [self.emp_mgr_a.id, self.emp_mgr_b.id])
        ]).unlink()

        self._sync()

        uh_a = self._uh_for(self.emp_mgr_a)
        uh_b = self._uh_for(self.emp_mgr_b)
        self.assertTrue(uh_a, "UH entry should be created for Manager A")
        self.assertTrue(uh_b, "UH entry should be created for Manager B")

    def test_sync_assigns_managed_depts_as_office(self):
        self.env['upmin_iso.unit_head'].sudo().search([
            ('name', '=', self.emp_mgr_a.id)
        ]).unlink()

        self._sync()
        uh_a = self._uh_for(self.emp_mgr_a)
        self.assertIn(self.dept_a, uh_a.office)

    # ── Sync: update ──────────────────────────────────────────────────────────

    def test_sync_updates_office_when_managed_depts_change(self):
        # Ensure UH exists for mgr_a (manages dept_a)
        self._sync()
        uh_a = self._uh_for(self.emp_mgr_a)
        self.assertIn(self.dept_a, uh_a.office)
        self.assertNotIn(self.dept_c, uh_a.office)

        # Now also assign dept_c to mgr_a
        self.dept_c.manager_id = self.emp_mgr_a.id
        self._sync()

        uh_a = self._uh_for(self.emp_mgr_a)
        self.assertIn(self.dept_a, uh_a.office)
        self.assertIn(self.dept_c, uh_a.office)

        # Cleanup: remove dept_c manager
        self.dept_c.manager_id = False

    # ── Sync: delete ─────────────────────────────────────────────────────────

    def test_sync_deletes_uh_when_manager_removed(self):
        self._sync()
        self.assertTrue(self._uh_for(self.emp_mgr_b), "UH should exist before removal")

        # Remove mgr_b from dept_b
        self.dept_b.manager_id = False
        self._sync()

        uh_b = self._uh_for(self.emp_mgr_b)
        self.assertFalse(uh_b, "UH should be removed when employee no longer manages any dept")

        # Restore for subsequent tests
        self.dept_b.manager_id = self.emp_mgr_b.id

    # ── Sync: DC group grants ─────────────────────────────────────────────────

    def test_sync_grants_dc_group_to_uh_employees_with_user(self):
        # Create a user for mgr_a (previously had no user) and run sync
        user_mgr_a = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'mgr_a_user',
            'login': 'mgr_a@iso.test',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.emp_mgr_a.user_id = user_mgr_a.id

        # Ensure no UH exists, then sync
        self.env['upmin_iso.unit_head'].sudo().search([('name', '=', self.emp_mgr_a.id)]).unlink()
        self._sync()

        self.assertTrue(self._has_dc_group(user_mgr_a),
                        "Sync should grant DC group to UH employee with user account")

        # Cleanup user link
        self.emp_mgr_a.user_id = False

    def test_sync_does_not_revoke_dc_group_if_employee_still_in_dc(self):
        # emp_u2 is in DC (dc_u2); give emp_u2 a managed dept so sync creates a UH
        self.dept_c.manager_id = self.emp_u2.id
        self._sync()
        self.assertTrue(self._has_dc_group(self.u2), "u2 should still have DC group")

        # Now remove mgr ship and re-sync (UH deleted)
        self.dept_c.manager_id = False
        self._sync()
        self.assertTrue(self._has_dc_group(self.u2),
                        "u2 should retain DC group — still in DC directory")


class TestPermGuards(ISOAccessBase):
    """Cross-model _revoke_group guards on DC and UH."""

    def _has_dc_group(self, user):
        group = self.env.ref('upmin_iso.group_iso_doc_controller')
        return group in user.sudo().groups_id

    def _make_emp_user(self, tag):
        u = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': tag,
            'login': f'{tag}@perm.test',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        emp = self.env['hr.employee'].create({
            'name': tag,
            'department_id': self.dept_a.id,
            'user_id': u.id,
        })
        return u, emp

    # ── UH delete revokes DC group (not in DC) ────────────────────────────────

    def test_delete_uh_revokes_dc_group_when_not_in_dc(self):
        u, emp = self._make_emp_user('uh_only')
        uh = self.env['upmin_iso.unit_head'].sudo().create({
            'name': emp.id,
            'office': [(4, self.dept_a.id)],
        })
        self.assertTrue(self._has_dc_group(u), "UH create should grant DC group")

        uh.sudo().unlink()
        self.assertFalse(self._has_dc_group(u),
                         "Deleting UH should revoke DC group (not in DC)")

    # ── UH delete does NOT revoke DC group (still in DC) ─────────────────────

    def test_delete_uh_does_not_revoke_dc_group_when_in_dc(self):
        u, emp = self._make_emp_user('uh_and_dc')
        uh = self.env['upmin_iso.unit_head'].sudo().create({
            'name': emp.id,
            'office': [(4, self.dept_a.id)],
        })
        dc = self.env['upmin_iso.document_controller'].sudo().create({'name': emp.id})
        self.assertTrue(self._has_dc_group(u))

        uh.sudo().unlink()
        self.assertTrue(self._has_dc_group(u),
                        "DC group should be retained — employee still in DC directory")

        # Cleanup
        dc.sudo().unlink()

    # ── DC delete revokes DC group (not in UH) ────────────────────────────────

    def test_delete_dc_revokes_dc_group_when_not_in_uh(self):
        u, emp = self._make_emp_user('dc_only')
        dc = self.env['upmin_iso.document_controller'].sudo().create({'name': emp.id})
        self.assertTrue(self._has_dc_group(u), "DC create should grant DC group")

        dc.sudo().unlink()
        self.assertFalse(self._has_dc_group(u),
                         "Deleting DC should revoke DC group (not in UH)")

    # ── DC delete does NOT revoke DC group (still in UH) ─────────────────────

    def test_delete_dc_does_not_revoke_dc_group_when_in_uh(self):
        u, emp = self._make_emp_user('dc_and_uh')
        dc = self.env['upmin_iso.document_controller'].sudo().create({'name': emp.id})
        uh = self.env['upmin_iso.unit_head'].sudo().create({
            'name': emp.id,
            'office': [(4, self.dept_a.id)],
        })
        self.assertTrue(self._has_dc_group(u))

        dc.sudo().unlink()
        self.assertTrue(self._has_dc_group(u),
                        "DC group should be retained — employee still in UH directory")

        # Cleanup
        uh.sudo().unlink()

    # ── Deleting both removes the group ──────────────────────────────────────

    def test_delete_both_dc_and_uh_revokes_dc_group(self):
        u, emp = self._make_emp_user('dc_and_uh_both')
        dc = self.env['upmin_iso.document_controller'].sudo().create({'name': emp.id})
        uh = self.env['upmin_iso.unit_head'].sudo().create({
            'name': emp.id,
            'office': [(4, self.dept_a.id)],
        })
        self.assertTrue(self._has_dc_group(u))

        dc.sudo().unlink()
        self.assertTrue(self._has_dc_group(u), "Still in UH — group retained")

        uh.sudo().unlink()
        self.assertFalse(self._has_dc_group(u),
                         "Both DC and UH deleted — DC group should be revoked")

    # ── IA group behaves independently ────────────────────────────────────────

    def test_delete_ia_revokes_ia_group(self):
        u, emp = self._make_emp_user('ia_only')
        ia = self.env['upmin_iso.internal_auditor'].sudo().create({'name': emp.id})
        g_ia = self.env.ref('upmin_iso.group_iso_internal_auditor')
        self.assertIn(g_ia, u.sudo().groups_id, "IA create should grant IA group")

        ia.sudo().unlink()
        self.assertNotIn(g_ia, u.sudo().groups_id,
                         "Deleting IA should revoke IA group")
