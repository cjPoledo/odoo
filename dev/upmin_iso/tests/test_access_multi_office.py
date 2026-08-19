"""
Multi-office and access group tests for upmin_iso.

The base fixture (ISOAccessBase) covers users with a single primary office.
This file tests the additional scoping mechanisms:

  A) DC with admin_department_id  ── employee holds two office roles
     - Sees/writes SWOT, ROR, CCAR, AuditInfo for BOTH primary and secondary office
     - Blocked from records belonging to an unrelated office

  B) IA with admin_department_id  ── conflict constraint covers both offices
     - Cannot be assigned to audit their primary department (department_id)
     - Cannot be assigned to audit their secondary department (admin_department_id)
       because ia.office includes both departments
     - Can audit any department not in their office set

  C) IA managing a department  ── ia.office includes managed departments
     - Cannot be assigned to audit a department they manage
     - Can still audit unrelated departments

  D) College-level (iso_access_group + iso_ancestor_ids)  ── ancestor scope
     A DC whose DC record office traverses upward to an iso_access_group parent
     gains access to records owned by that parent (college) department.
     Structure:
       college_dept  ← registered as upmin_iso.iso_access_group
         └── dept_child
     DC in dept_child  →  iso_ancestor_ids = [college_dept]
     Security rule: ('office', 'in', iso_ancestor_ids)
       → grants read/write for records where office = college_dept
"""

from odoo.exceptions import AccessError, ValidationError

from .common import ISOAccessBase


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_user_with_admin_dept(cls, tag, dept_primary, dept_admin, groups):
    """
    Create a user+employee with a primary department AND an admin_department_id
    (the secondary office field added by upmin_hr_ext).
    """
    env = cls.env
    u = env['res.users'].with_context(no_reset_password=True).create({
        'name': tag,
        'login': f'{tag}@iso.test',
        'groups_id': [(6, 0, groups)],
    })
    emp = env['hr.employee'].create({
        'name': tag,
        'department_id': dept_primary.id,
        'user_id': u.id,
    })
    emp.sudo().write({'admin_department_id': dept_admin.id})
    return u, emp


# ─────────────────────────────────────────────────────────────────────────────
# A. DC with admin_department_id
# ─────────────────────────────────────────────────────────────────────────────

class TestDCMultiOffice(ISOAccessBase):
    """
    A DC whose employee has both department_id (dept_a) and admin_department_id
    (dept_c) can see and write records belonging to EITHER office, but not to a
    third unrelated office (dept_b).

    Fixture user: u_dc_multi
      department_id      = dept_a   (primary, covered by existing fixture records)
      admin_department_id = dept_c  (secondary, new records created here)
      group              = group_iso_doc_controller
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        g_user = env.ref('base.group_user')

        # ── Secondary office ─────────────────────────────────────────────────
        cls.dept_c = env['hr.department'].create({'name': '[Test] Office C (multi-dc)'})

        # SWOT and ROR for the secondary office
        cls.swot_c = env['upmin_iso.swot'].sudo().create({
            'year': '2024', 'office': cls.dept_c.id,
        })
        cls.ror_c = env['upmin_iso.ror'].sudo().create({'office': cls.dept_c.id})

        # Audit chain for dept_c (needed for CCAR office derivation)
        cls.period_c = env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-03-01',
            'audit_end_date': '2024-03-31',
        })
        cls.audit_c = env['upmin_iso.audit_info'].sudo().create({
            'office_to_audit': cls.dept_c.id,
            'audit_period': cls.period_c.id,
        })
        cls.nc_c1 = env['upmin_iso.audit_finding'].sudo().create({
            'audit_info': cls.audit_c.id,
            'auditor': env.user.partner_id.id,
            'rating': 'nc',
        })
        # status='office' so DC write rule matches (DC can write at office/office2 status)
        cls.ccar_c = env['upmin_iso.ccar'].sudo().create({
            'ccar_no': '2024-10',
            'date': '2024-03-15',
            'audit_period': cls.period_c.id,
            'related_nc': cls.nc_c1.id,
            'status': 'office',
        })

        # ── Multi-office DC user ──────────────────────────────────────────────
        cls.u_dc_multi, cls.emp_dc_multi = _make_user_with_admin_dept(
            cls, 'u_dc_multi', cls.dept_a, cls.dept_c, [g_user.id, cls.g_dc.id]
        )
        # DC directory record — _compute_office will include dept_a AND dept_c
        env['upmin_iso.document_controller'].sudo().create({
            'name': cls.emp_dc_multi.id,
        })

    # ── SWOT visibility ───────────────────────────────────────────────────────

    def test_dc_multi_sees_primary_office_swot(self):
        results = self._search('upmin_iso.swot', self.u_dc_multi)
        self.assertIn(self.swot_a, results)

    def test_dc_multi_sees_secondary_office_swot(self):
        results = self._search('upmin_iso.swot', self.u_dc_multi)
        self.assertIn(self.swot_c, results)

    def test_dc_multi_cannot_see_unrelated_office_swot(self):
        results = self._search('upmin_iso.swot', self.u_dc_multi)
        self.assertNotIn(self.swot_b, results)

    # ── SWOT write ────────────────────────────────────────────────────────────

    def test_dc_multi_can_write_primary_office_swot(self):
        self.swot_a.with_user(self.u_dc_multi).write({'year': '2025'})

    def test_dc_multi_can_write_secondary_office_swot(self):
        self.swot_c.with_user(self.u_dc_multi).write({'year': '2025'})

    def test_dc_multi_cannot_write_unrelated_office_swot(self):
        with self.assertRaises(AccessError):
            self.swot_b.with_user(self.u_dc_multi).write({'year': '2025'})

    # ── SWOT create ───────────────────────────────────────────────────────────

    def test_dc_multi_can_create_swot_for_secondary_office(self):
        rec = self.env['upmin_iso.swot'].with_user(self.u_dc_multi).create({
            'year': '2099', 'office': self.dept_c.id,
        })
        self.assertTrue(rec.id)

    def test_dc_multi_cannot_create_swot_for_unrelated_office(self):
        with self.assertRaises(AccessError):
            self.env['upmin_iso.swot'].with_user(self.u_dc_multi).create({
                'year': '2099', 'office': self.dept_b.id,
            })

    # ── ROR visibility ────────────────────────────────────────────────────────

    def test_dc_multi_sees_primary_office_ror(self):
        results = self._search('upmin_iso.ror', self.u_dc_multi)
        self.assertIn(self.ror_a, results)

    def test_dc_multi_sees_secondary_office_ror(self):
        results = self._search('upmin_iso.ror', self.u_dc_multi)
        self.assertIn(self.ror_c, results)

    def test_dc_multi_cannot_see_unrelated_office_ror(self):
        results = self._search('upmin_iso.ror', self.u_dc_multi)
        self.assertNotIn(self.ror_b, results)

    # ── ROR write ─────────────────────────────────────────────────────────────

    def test_dc_multi_can_write_secondary_office_ror(self):
        self.ror_c.with_user(self.u_dc_multi).write({'related_swot': False})

    def test_dc_multi_cannot_write_unrelated_office_ror(self):
        with self.assertRaises(AccessError):
            self.ror_b.with_user(self.u_dc_multi).write({'related_swot': False})

    # ── CCAR visibility ───────────────────────────────────────────────────────

    def test_dc_multi_sees_primary_office_ccar(self):
        # ccar_office is dept_a (primary)
        results = self._search('upmin_iso.ccar', self.u_dc_multi)
        self.assertIn(self.ccar_office, results)

    def test_dc_multi_sees_secondary_office_ccar(self):
        results = self._search('upmin_iso.ccar', self.u_dc_multi)
        self.assertIn(self.ccar_c, results)

    def test_dc_multi_cannot_see_unrelated_office_ccar(self):
        # ccar_b is dept_b (unrelated)
        results = self._search('upmin_iso.ccar', self.u_dc_multi)
        self.assertNotIn(self.ccar_b, results)

    # ── CCAR write (status-gated) ─────────────────────────────────────────────

    def test_dc_multi_can_write_secondary_office_ccar_at_office_status(self):
        # ccar_c is status='office' for dept_c (secondary) — DC write rule matches
        self.ccar_c.with_user(self.u_dc_multi).write({'description': 'multi-dc update'})

    def test_dc_multi_cannot_write_unrelated_office_ccar(self):
        with self.assertRaises(AccessError):
            self.ccar_b.with_user(self.u_dc_multi).write({'description': 'attempted'})

    # ── Audit Info visibility ─────────────────────────────────────────────────

    def test_dc_multi_sees_primary_office_audit_info(self):
        results = self._search('upmin_iso.audit_info', self.u_dc_multi)
        self.assertIn(self.audit_a, results)

    def test_dc_multi_sees_secondary_office_audit_info(self):
        results = self._search('upmin_iso.audit_info', self.u_dc_multi)
        self.assertIn(self.audit_c, results)

    def test_dc_multi_cannot_see_unrelated_office_audit_info(self):
        # audit_b is dept_b (unrelated)
        results = self._search('upmin_iso.audit_info', self.u_dc_multi)
        self.assertNotIn(self.audit_b, results)

    # ── Audit Finding visibility ──────────────────────────────────────────────

    def test_dc_multi_sees_primary_office_audit_findings(self):
        results = self._search('upmin_iso.audit_finding', self.u_dc_multi)
        self.assertIn(self.nc_a1, results)

    def test_dc_multi_sees_secondary_office_audit_findings(self):
        results = self._search('upmin_iso.audit_finding', self.u_dc_multi)
        self.assertIn(self.nc_c1, results)

    def test_dc_multi_cannot_see_unrelated_office_audit_findings(self):
        results = self._search('upmin_iso.audit_finding', self.u_dc_multi)
        self.assertNotIn(self.nc_b1, results)


# ─────────────────────────────────────────────────────────────────────────────
# B. IA with admin_department_id  ── conflict constraint
# ─────────────────────────────────────────────────────────────────────────────

class TestIAMultiOfficeConflict(ISOAccessBase):
    """
    An IA whose employee has both department_id and admin_department_id cannot
    audit either of those offices.  ia.office is computed from both fields, so
    both appear as conflicts in _check_auditor_office_conflict.

    Fixture user: u_ia_multi
      department_id       = dept_b  (→ can't audit dept_b)
      admin_department_id = dept_c  (→ can't audit dept_c)
      group               = group_iso_internal_auditor
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        g_user = env.ref('base.group_user')

        cls.dept_c = env['hr.department'].create({'name': '[Test] Office C (multi-ia)'})

        cls.u_ia_multi, cls.emp_ia_multi = _make_user_with_admin_dept(
            cls, 'u_ia_multi', cls.dept_b, cls.dept_c, [g_user.id, cls.g_ia.id]
        )
        cls.ia_multi_rec = env['upmin_iso.internal_auditor'].sudo().create({
            'name': cls.emp_ia_multi.id,
        })

    def test_ia_multi_blocked_from_auditing_primary_dept(self):
        """IA cannot audit department_id (dept_b)."""
        # audit_b already exists for cls.period, so use a fresh period
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-11-01', 'audit_end_date': '2024-11-30',
        })
        with self.assertRaises(ValidationError):
            self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_b.id,
                'audit_period': p.id,
                'internal_auditors': [(4, self.ia_multi_rec.id)],
            })

    def test_ia_multi_blocked_from_auditing_secondary_dept(self):
        """IA cannot audit admin_department_id (dept_c) — it is in ia.office."""
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-12-01', 'audit_end_date': '2024-12-31',
        })
        with self.assertRaises(ValidationError):
            self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_c.id,
                'audit_period': p.id,
                'internal_auditors': [(4, self.ia_multi_rec.id)],
            })

    def test_ia_multi_can_audit_unrelated_dept(self):
        """IA can be assigned to audit dept_a (not in their office set)."""
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-05-01', 'audit_end_date': '2024-05-31',
        })
        try:
            rec = self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_a.id,
                'audit_period': p.id,
                'internal_auditors': [(4, self.ia_multi_rec.id)],
            })
            self.assertTrue(rec.id)
        except ValidationError:
            self.fail("IA should be allowed to audit dept_a (not their office).")


# ─────────────────────────────────────────────────────────────────────────────
# C. IA managing a department  ── managed dept in ia.office
# ─────────────────────────────────────────────────────────────────────────────

class TestIAManagedDeptConflict(ISOAccessBase):
    """
    InternalAuditor._compute_office includes departments where the employee is
    set as manager (via hr.department.manager_id).  The conflict constraint
    checks ia.office, so a managed department is treated the same as a home
    office — the IA cannot audit it.

    Fixture user: u_ia_mgr
      department_id = dept_b  (home)
      manages       = dept_managed (set via dept.manager_id)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        g_user = env.ref('base.group_user')

        cls.dept_managed = env['hr.department'].create({'name': '[Test] Managed Dept'})

        cls.u_ia_mgr = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'u_ia_mgr',
            'login': 'u_ia_mgr@iso.test',
            'groups_id': [(6, 0, [g_user.id, cls.g_ia.id])],
        })
        cls.emp_ia_mgr = env['hr.employee'].create({
            'name': 'u_ia_mgr',
            'department_id': cls.dept_b.id,
            'user_id': cls.u_ia_mgr.id,
        })
        # Set manager BEFORE creating the IA record so that _compute_office,
        # which runs at creation time, finds dept_managed in the managed-depts query.
        cls.dept_managed.sudo().write({'manager_id': cls.emp_ia_mgr.id})
        cls.ia_mgr_rec = env['upmin_iso.internal_auditor'].sudo().create({
            'name': cls.emp_ia_mgr.id,
        })

    def test_ia_manager_blocked_from_auditing_managed_dept(self):
        """IA managing dept_managed cannot audit it — managed dept is in ia.office."""
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-11-01', 'audit_end_date': '2024-11-30',
        })
        with self.assertRaises(ValidationError):
            self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_managed.id,
                'audit_period': p.id,
                'internal_auditors': [(4, self.ia_mgr_rec.id)],
            })

    def test_ia_manager_can_audit_unmanaged_dept(self):
        """IA managing dept_managed can still audit dept_a (not managed)."""
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-06-01', 'audit_end_date': '2024-06-30',
        })
        try:
            rec = self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_a.id,
                'audit_period': p.id,
                'internal_auditors': [(4, self.ia_mgr_rec.id)],
            })
            self.assertTrue(rec.id)
        except ValidationError:
            self.fail("IA manager should be allowed to audit dept_a.")

    def test_ia_manager_still_blocked_from_home_dept(self):
        """Home department (dept_b) is still blocked regardless of managed dept."""
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-07-01', 'audit_end_date': '2024-07-31',
        })
        with self.assertRaises(ValidationError):
            self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_b.id,
                'audit_period': p.id,
                'internal_auditors': [(4, self.ia_mgr_rec.id)],
            })


# ─────────────────────────────────────────────────────────────────────────────
# D. College-level ancestor access via iso_access_group
# ─────────────────────────────────────────────────────────────────────────────

class TestCollegeLevelAccess(ISOAccessBase):
    """
    iso_access_group registers a parent department as a "college" that grants
    upward document visibility to employees in its child departments.

    How it works:
      1. college_dept is registered as upmin_iso.iso_access_group.
      2. emp_child_dc has department_id = dept_child (child of college_dept).
      3. Creating a DC record for emp_child_dc sets DC.office = dept_child.
      4. _compute_iso_ancestor_ids traverses dept_child → college_dept → hit,
         so emp_child_dc.iso_ancestor_ids = [college_dept].
      5. Security rule: ('office', 'in', user.employee_id.iso_ancestor_ids.ids)
         → emp_child_dc can read/write records where record.office = college_dept.

    This allows a sub-department DC to also access the college's ISO documents
    without having college_dept in their direct department_id or admin_department_id.

    Fixture:
      college_dept  ← iso_access_group
        └── dept_child
      swot_college, ror_college  ← office = college_dept
      u_child_dc: dept_child, DC group → iso_ancestor_ids = [college_dept]
      u2 (from base): dept_a, DC group → no college ancestry → cannot see college records
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        g_user = env.ref('base.group_user')

        # ── College hierarchy ─────────────────────────────────────────────────
        cls.college_dept = env['hr.department'].create({'name': '[Test] College Dept'})
        cls.dept_child = env['hr.department'].create({
            'name': '[Test] Child Dept',
            'parent_id': cls.college_dept.id,
        })

        # Register college_dept as an ISO access group
        cls.iso_ag = env['upmin_iso.iso_access_group'].sudo().create({
            'department_id': cls.college_dept.id,
        })

        # ── Records owned by the college ─────────────────────────────────────
        cls.swot_college = env['upmin_iso.swot'].sudo().create({
            'year': '2024', 'office': cls.college_dept.id,
        })
        cls.ror_college = env['upmin_iso.ror'].sudo().create({
            'office': cls.college_dept.id,
        })

        # ── Records owned by dept_child itself ────────────────────────────────
        cls.swot_child = env['upmin_iso.swot'].sudo().create({
            'year': '2024', 'office': cls.dept_child.id,
        })

        # ── DC user in dept_child ─────────────────────────────────────────────
        cls.u_child_dc = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'u_child_dc',
            'login': 'u_child_dc@iso.test',
            'groups_id': [(6, 0, [g_user.id, cls.g_dc.id])],
        })
        cls.emp_child_dc = env['hr.employee'].create({
            'name': 'u_child_dc',
            'department_id': cls.dept_child.id,
            'user_id': cls.u_child_dc.id,
        })
        # DC record: _compute_office → office = dept_child (from department_id)
        # _compute_iso_ancestor_ids looks at DC records → dept_child → college_dept in group
        cls.dc_child_rec = env['upmin_iso.document_controller'].sudo().create({
            'name': cls.emp_child_dc.id,
        })
        # Invalidate so the ancestor computation runs fresh with the new DC record
        cls.emp_child_dc.sudo().invalidate_recordset(['iso_ancestor_ids'])

    # ── Ancestor-based SWOT access ────────────────────────────────────────────

    def test_child_dc_sees_college_swot_via_ancestor(self):
        """DC in dept_child sees college_dept SWOT via iso_ancestor_ids."""
        results = self._search('upmin_iso.swot', self.u_child_dc)
        self.assertIn(self.swot_college, results)

    def test_child_dc_also_sees_own_dept_swot(self):
        """DC in dept_child sees their own dept_child SWOT (direct department_id match)."""
        results = self._search('upmin_iso.swot', self.u_child_dc)
        self.assertIn(self.swot_child, results)

    def test_child_dc_cannot_see_unrelated_swot(self):
        """DC in dept_child cannot see SWOT for dept_b (no ancestry link)."""
        results = self._search('upmin_iso.swot', self.u_child_dc)
        self.assertNotIn(self.swot_b, results)

    def test_unrelated_dc_cannot_see_college_swot(self):
        """DC in dept_a (not a child of college_dept) cannot see college_dept SWOT."""
        results = self._search('upmin_iso.swot', self.u2)
        self.assertNotIn(self.swot_college, results)

    # ── Ancestor-based SWOT write ─────────────────────────────────────────────

    def test_child_dc_can_write_college_swot(self):
        """DC in dept_child can write college_dept SWOT (DC CRUD rule matches ancestor)."""
        self.swot_college.with_user(self.u_child_dc).write({'year': '2025'})

    def test_child_dc_cannot_write_unrelated_swot(self):
        """DC in dept_child cannot write dept_b SWOT."""
        with self.assertRaises(AccessError):
            self.swot_b.with_user(self.u_child_dc).write({'year': '2025'})

    def test_child_dc_can_create_swot_for_college_dept(self):
        """DC in dept_child can create a SWOT owned by college_dept."""
        rec = self.env['upmin_iso.swot'].with_user(self.u_child_dc).create({
            'year': '2099', 'office': self.college_dept.id,
        })
        self.assertTrue(rec.id)

    def test_child_dc_cannot_create_swot_for_unrelated_dept(self):
        """DC in dept_child cannot create a SWOT for dept_b."""
        with self.assertRaises(AccessError):
            self.env['upmin_iso.swot'].with_user(self.u_child_dc).create({
                'year': '2099', 'office': self.dept_b.id,
            })

    # ── Ancestor-based ROR access ─────────────────────────────────────────────

    def test_child_dc_sees_college_ror_via_ancestor(self):
        """DC in dept_child sees college_dept ROR via iso_ancestor_ids."""
        results = self._search('upmin_iso.ror', self.u_child_dc)
        self.assertIn(self.ror_college, results)

    def test_child_dc_cannot_see_unrelated_ror(self):
        """DC in dept_child cannot see dept_b ROR."""
        results = self._search('upmin_iso.ror', self.u_child_dc)
        self.assertNotIn(self.ror_b, results)

    def test_unrelated_dc_cannot_see_college_ror(self):
        """DC in dept_a (no college ancestry) cannot see college_dept ROR."""
        results = self._search('upmin_iso.ror', self.u2)
        self.assertNotIn(self.ror_college, results)

    def test_child_dc_can_write_college_ror(self):
        """DC in dept_child can write college_dept ROR."""
        self.ror_college.with_user(self.u_child_dc).write({'related_swot': False})

    # ── iso_access_group removal revokes ancestor access ──────────────────────

    def test_removing_access_group_revokes_ancestor_access(self):
        """
        When the iso_access_group record for college_dept is deleted,
        emp_child_dc.iso_ancestor_ids becomes empty and the DC loses
        access to college_dept records.
        """
        # Confirm access before removal
        results_before = self._search('upmin_iso.swot', self.u_child_dc)
        self.assertIn(self.swot_college, results_before)

        # Remove the access group (sudo to bypass any model-level restrictions)
        self.iso_ag.sudo().unlink()
        self.emp_child_dc.sudo().invalidate_recordset(['iso_ancestor_ids'])

        # Access should now be revoked
        results_after = self._search('upmin_iso.swot', self.u_child_dc)
        self.assertNotIn(self.swot_college, results_after)

    # ── College ancestor conflict in auditor assignment ────────────────────────

    def test_ia_in_child_dept_blocked_from_auditing_college_ancestor(self):
        """
        An IA whose department_id is dept_child (child of college_dept, which is an
        iso_access_group) cannot be assigned to audit college_dept itself.
        The conflict check traverses college_ancestors(emp) for the employee's
        department_id path and blocks the assignment.
        """
        ia_child_emp = self.env['hr.employee'].sudo().create({
            'name': 'IA Child Emp',
            'department_id': self.dept_child.id,
            'work_email': 'ia.child.emp@iso.test',
        })
        ia_child_rec = self.env['upmin_iso.internal_auditor'].sudo().create({
            'name': ia_child_emp.id,
        })
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-08-01', 'audit_end_date': '2024-08-31',
        })
        with self.assertRaises(ValidationError):
            self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.college_dept.id,
                'audit_period': p.id,
                'internal_auditors': [(4, ia_child_rec.id)],
            })

    def test_ia_in_child_dept_can_audit_unrelated_dept(self):
        """Same IA in dept_child (child of college) can audit dept_a (unrelated)."""
        ia_child_emp = self.env['hr.employee'].sudo().create({
            'name': 'IA Child Emp 2',
            'department_id': self.dept_child.id,
            'work_email': 'ia.child.emp.2@iso.test',
        })
        ia_child_rec = self.env['upmin_iso.internal_auditor'].sudo().create({
            'name': ia_child_emp.id,
        })
        p = self.env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-09-01', 'audit_end_date': '2024-09-30',
        })
        try:
            rec = self.env['upmin_iso.audit_info'].sudo().create({
                'office_to_audit': self.dept_a.id,
                'audit_period': p.id,
                'internal_auditors': [(4, ia_child_rec.id)],
            })
            self.assertTrue(rec.id)
        except ValidationError:
            self.fail("IA in dept_child should be allowed to audit dept_a.")
