"""
Shared test fixture for upmin_iso access/permission tests.

Departments
-----------
dept_a  — "Office A"  (the home office for all DC/IA test users)
dept_b  — "Office B"  (the foreign office — cross-office blocking target)

Users (U0–U7)
-------------
u0  — plain internal user, no ISO group
u1  — ISO Internal Auditor only
u2  — ISO Document Controller only
u3  — IA + DC
u4  — ISO Staff
u5  — Staff + DC
u6  — Staff + IA
u7  — All (Staff + DC + IA)

Every ISO user (u1-u7) has a linked hr.employee with department_id = dept_a,
so "own office" checks resolve to dept_a for all of them.

Directory membership
--------------------
IA records : u1, u3, u6, u7
DC records : u2, u3, u5, u7

Audit chain
-----------
audit_a  — office=dept_a, auditors=[ia_u1, ia_u3, ia_u6, ia_u7]
audit_b  — office=dept_b, auditors=none

CCARs (all dept_a unless noted)
--------------------------------
ccar_creation  — status='creation'  (linked to nc_a1)
ccar_office    — status='office'    (linked to nc_a2)
ccar_verif     — status='verification' (linked to nc_a3)
ccar_b         — status='creation', office=dept_b (linked to nc_b1)
"""

from odoo.tests.common import TransactionCase


class ISOAccessBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        # ── Groups ────────────────────────────────────────────────────────────
        cls.g_ia    = env.ref('upmin_iso.group_iso_internal_auditor')
        cls.g_dc    = env.ref('upmin_iso.group_iso_doc_controller')
        cls.g_staff = env.ref('upmin_iso.group_iso_staff')
        g_user      = env.ref('base.group_user')

        # ── Departments ───────────────────────────────────────────────────────
        cls.dept_a = env['hr.department'].create({'name': '[Test] Office A'})
        cls.dept_b = env['hr.department'].create({'name': '[Test] Office B'})

        # ── Users + Employees ─────────────────────────────────────────────────
        # IA-role users (u1, u3, u6, u7) are based in dept_b so they can audit
        # dept_a without triggering the auditor-own-office conflict constraint.
        # DC-role users (u2, u5) are based in dept_a (their edit scope).
        # U3 (IA+DC): dept_b home → DC scope is dept_b, IA audits dept_a.
        # U7 (All):   dept_b home → same reasoning as U3.
        def _make(tag, dept, groups):
            u = env['res.users'].with_context(no_reset_password=True).create({
                'name': tag,
                'login': f'{tag}@iso.test',
                'groups_id': [(6, 0, groups)],
            })
            emp = env['hr.employee'].create({
                'name': tag,
                'department_id': dept.id,
                'user_id': u.id,
            })
            return u, emp

        cls.u0 = env['res.users'].with_context(no_reset_password=True).create({
            'name': 'u0_plain',
            'login': 'u0@iso.test',
            'groups_id': [(6, 0, [g_user.id])],
        })
        cls.u1, cls.emp_u1 = _make('u1_ia',       cls.dept_b, [g_user.id, cls.g_ia.id])
        cls.u2, cls.emp_u2 = _make('u2_dc',       cls.dept_a, [g_user.id, cls.g_dc.id])
        cls.u3, cls.emp_u3 = _make('u3_ia_dc',    cls.dept_b, [g_user.id, cls.g_ia.id, cls.g_dc.id])
        cls.u4, cls.emp_u4 = _make('u4_staff',    cls.dept_a, [g_user.id, cls.g_staff.id])
        cls.u5, cls.emp_u5 = _make('u5_staff_dc', cls.dept_a, [g_user.id, cls.g_staff.id, cls.g_dc.id])
        cls.u6, cls.emp_u6 = _make('u6_staff_ia', cls.dept_b, [g_user.id, cls.g_staff.id, cls.g_ia.id])
        cls.u7, cls.emp_u7 = _make('u7_all',      cls.dept_b, [g_user.id, cls.g_staff.id, cls.g_dc.id, cls.g_ia.id])

        # ── Directory records ─────────────────────────────────────────────────
        # Use sudo() so group-grant side-effects don't interfere with explicitly
        # assigned groups above (grant is idempotent but cleaner to be explicit).
        IA = env['upmin_iso.internal_auditor']
        DC = env['upmin_iso.document_controller']

        cls.ia_u1 = IA.sudo().create({'name': cls.emp_u1.id})
        cls.ia_u3 = IA.sudo().create({'name': cls.emp_u3.id})
        cls.ia_u6 = IA.sudo().create({'name': cls.emp_u6.id})
        cls.ia_u7 = IA.sudo().create({'name': cls.emp_u7.id})

        cls.dc_u2 = DC.sudo().create({'name': cls.emp_u2.id})
        cls.dc_u3 = DC.sudo().create({'name': cls.emp_u3.id})
        cls.dc_u5 = DC.sudo().create({'name': cls.emp_u5.id})
        cls.dc_u7 = DC.sudo().create({'name': cls.emp_u7.id})

        # ── SWOT ──────────────────────────────────────────────────────────────
        cls.swot_a = env['upmin_iso.swot'].sudo().create({
            'year': '2024', 'office': cls.dept_a.id,
        })
        cls.swot_b = env['upmin_iso.swot'].sudo().create({
            'year': '2024', 'office': cls.dept_b.id,
        })

        # ── TOWS ──────────────────────────────────────────────────────────────
        cls.tows_a = env['upmin_iso.tows'].sudo().create({'swot': cls.swot_a.id})
        cls.tows_b = env['upmin_iso.tows'].sudo().create({'swot': cls.swot_b.id})

        # ── ROR ───────────────────────────────────────────────────────────────
        cls.ror_a = env['upmin_iso.ror'].sudo().create({'office': cls.dept_a.id})
        cls.ror_b = env['upmin_iso.ror'].sudo().create({'office': cls.dept_b.id})

        # ── Audit chain ───────────────────────────────────────────────────────
        cls.period = env['upmin_iso.audit_period'].sudo().create({
            'audit_start_date': '2024-01-01',
            'audit_end_date': '2024-01-31',
        })
        cls.audit_a = env['upmin_iso.audit_info'].sudo().create({
            'office_to_audit': cls.dept_a.id,
            'audit_period': cls.period.id,
            'internal_auditors': [
                (4, cls.ia_u1.id),
                (4, cls.ia_u3.id),
                (4, cls.ia_u6.id),
                (4, cls.ia_u7.id),
            ],
        })
        cls.audit_b = env['upmin_iso.audit_info'].sudo().create({
            'office_to_audit': cls.dept_b.id,
            'audit_period': cls.period.id,
        })

        admin_partner = env.user.partner_id.id

        def _finding(audit_info, rating):
            return env['upmin_iso.audit_finding'].sudo().create({
                'audit_info': audit_info.id,
                'auditor': admin_partner,
                'rating': rating,
            })

        # 3 NCs for dept_a (one per CCAR), 2 NCs for dept_b
        cls.nc_a1 = _finding(cls.audit_a, 'nc')
        cls.nc_a2 = _finding(cls.audit_a, 'nc')
        cls.nc_a3 = _finding(cls.audit_a, 'nc')
        cls.nc_b1 = _finding(cls.audit_b, 'nc')
        cls.nc_b2 = _finding(cls.audit_b, 'nc')
        cls.c_a1  = _finding(cls.audit_a, 'c')

        # ── CCARs ─────────────────────────────────────────────────────────────
        def _ccar(no, nc, status):
            return env['upmin_iso.ccar'].sudo().create({
                'ccar_no': no,
                'date': '2024-01-15',
                'audit_period': cls.period.id,
                'related_nc': nc.id,
                'status': status,
            })

        cls.ccar_creation = _ccar('2024-01', cls.nc_a1, 'creation')    # dept_a
        cls.ccar_office   = _ccar('2024-02', cls.nc_a2, 'office')      # dept_a
        cls.ccar_verif    = _ccar('2024-03', cls.nc_a3, 'verification') # dept_a
        cls.ccar_b        = _ccar('2024-04', cls.nc_b1, 'creation')    # dept_b
        cls.ccar_b_office = _ccar('2024-05', cls.nc_b2, 'office')      # dept_b, status=office (for U3 DC write test)

        # ── CCAR sub-records ──────────────────────────────────────────────────
        cls.ca_a = env['upmin_iso.ccar_corrective_action'].sudo().create({
            'ccar': cls.ccar_office.id,
        })
        cls.ce_a = env['upmin_iso.ccar_correction_effectiveness'].sudo().create({
            'ccar': cls.ccar_verif.id,
        })
        cls.cae_a = env['upmin_iso.ccar_corrective_action_effectiveness'].sudo().create({
            'ccar': cls.ccar_verif.id,
        })

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _search(self, model, user):
        return self.env[model].with_user(user).search([])

    def all_users(self):
        return [self.u0, self.u1, self.u2, self.u3, self.u4, self.u5, self.u6, self.u7]

    def staff_users(self):
        """Users that include group_iso_staff."""
        return [self.u4, self.u5, self.u6, self.u7]

    def dc_users(self):
        """Users that include group_iso_doc_controller (with or without staff)."""
        return [self.u2, self.u3, self.u5, self.u7]

    def ia_users(self):
        """Users that include group_iso_internal_auditor (with or without staff)."""
        return [self.u1, self.u3, self.u6, self.u7]

    def no_iso_users(self):
        """Users with no ISO group at all."""
        return [self.u0]
