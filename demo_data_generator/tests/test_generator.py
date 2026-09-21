import json
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged

from ..models.env_api import EnvAPI
from ..models.generators import DemoGenerator


@tagged('post_install', '-at_install')
class TestDemoGenerator(TransactionCase):
    def test_step_order(self):
        keys = DemoGenerator.STEP_KEYS
        self.assertEqual(keys[:2], ['modules', 'configure'])
        self.assertEqual(keys[-2:], ['mto_showcase', 'publish_website'])
        self.assertIn('contacts', keys)
        self.assertTrue(set(keys) <= set(DemoGenerator.STEP_LABELS))

    def test_contacts_step_creates_partners_and_state(self):
        before = self.env['res.partner'].search_count([])
        gen = DemoGenerator(EnvAPI(self.env))
        count, detail = gen.run_step('contacts')
        self.assertEqual(count, 35)
        self.assertEqual(detail, '35 created')
        self.assertEqual(self.env['res.partner'].search_count([]) - before, 35)
        state = gen.to_state()
        self.assertEqual(len(state['ids']['partner']), 35)
        gen2 = DemoGenerator(EnvAPI(self.env))
        gen2.from_state(state)
        self.assertEqual(gen2.ids['partner'], gen.ids['partner'])

    def test_salespeople_created_once_and_used_on_sales(self):
        if 'sale.order' not in self.env:
            self.skipTest('sale not installed')
        gen = DemoGenerator(EnvAPI(self.env))
        created, _ = gen.run_step('salespeople')
        pool = gen.ids['salesperson']
        self.assertEqual(len(pool), 5)
        users = self.env['res.users'].browse(pool)
        self.assertTrue(all(u.has_group('sales_team.group_sale_salesman') for u in users))
        # second run reuses the same users
        gen2 = DemoGenerator(EnvAPI(self.env))
        created2, _ = gen2.run_step('salespeople')
        self.assertEqual(created2, 0)
        self.assertEqual(gen2.ids['salesperson'], pool)
        # sales orders spread across the pool
        gen.gen_sales(10)
        orders = self.env['sale.order'].browse(gen.ids['sale_order'])
        self.assertTrue(set(orders.mapped('user_id.id')) <= set(pool))
        self.assertGreaterEqual(len(set(orders.mapped('user_id.id'))), 2)

    def test_state_roundtrip_keeps_int_keys(self):
        gen = DemoGenerator(EnvAPI(self.env))
        gen.ids['bom_product_map'] = {7: 9}
        gen._po_done = True
        gen2 = DemoGenerator(EnvAPI(self.env))
        gen2.from_state(json.loads(json.dumps(gen.to_state())))
        self.assertEqual(gen2.ids['bom_product_map'], {7: 9})
        self.assertTrue(gen2._po_done)


@tagged('post_install', '-at_install')
class TestDemoGeneratorModel(TransactionCase):
    def test_get_steps(self):
        steps = self.env['demo.data.generator'].get_steps()
        self.assertEqual([s['key'] for s in steps], DemoGenerator.STEP_KEYS)
        self.assertEqual(steps[0]['label'], 'Installing modules')

    def test_run_contacts_persists_state(self):
        model = self.env['demo.data.generator']
        model._save_state({})
        res = model.run_step('contacts')
        self.assertEqual(res['status'], 'done')
        self.assertEqual(res['count'], 35)
        self.assertEqual(len(model._load_state()['ids']['partner']), 35)

    def test_run_unknown_step_returns_error(self):
        res = self.env['demo.data.generator'].run_step('nope')
        self.assertEqual(res['status'], 'error')
        self.assertIn('Unknown step', res['detail'])

    def test_failed_step_leaves_cursor_usable(self):
        model = self.env['demo.data.generator']
        model._save_state({})

        def boom(gen, key):
            gen.api.env.cr.execute("SELECT 1/0")  # aborts the transaction at SQL level

        with patch.object(DemoGenerator, 'run_step', boom):
            res = model.run_step('contacts')
        self.assertEqual(res['status'], 'error')
        self.assertIn('division by zero', res['detail'])
        # cursor must still work after the failure
        self.assertTrue(self.env['res.partner'].create({'name': 'after failure'}).id)

    def test_non_admin_denied(self):
        user = self.env['res.users'].create({
            'name': 'u', 'login': 'u_demo',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        with self.assertRaises(AccessError):
            self.env['demo.data.generator'].with_user(user).get_steps()
