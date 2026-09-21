from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from ..models.generators import DemoGenerator


@tagged('post_install', '-at_install')
class TestDemoRunHistory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.model = self.env['demo.data.generator']

    def test_manual_run_logs_lines_and_finishes(self):
        run_id = self.model.start_run()
        run = self.env['demo.data.run'].browse(run_id)
        self.assertEqual(run.trigger, 'manual')
        self.assertEqual(run.state, 'running')
        res = self.model.run_step('contacts', run_id)
        self.assertEqual(res['status'], 'done')
        summary = self.model.finish_run(run_id)
        self.assertEqual(summary['state'], 'done')
        self.assertEqual(summary['record_count'], 35)
        self.assertEqual(len(run.line_ids), 1)
        line = run.line_ids[0]
        self.assertEqual((line.step_key, line.name, line.status, line.count), ('contacts', 'Contacts', 'done', 35))
        self.assertTrue(run.date_end)
        self.assertTrue(run.name.startswith('Run '))

    def test_error_step_marks_run_partial(self):
        run_id = self.model.start_run()
        self.model.run_step('contacts', run_id)
        self.model.run_step('nope', run_id)
        summary = self.model.finish_run(run_id)
        self.assertEqual(summary['state'], 'partial')
        self.assertEqual(summary['error_count'], 1)

    def test_cron_without_modules_fails_cleanly(self):
        with patch.object(type(self.model), '_modules_ready', return_value=False):
            run = self.model._cron_generate()
        self.assertEqual(run.trigger, 'cron')
        self.assertEqual(run.state, 'failed')
        self.assertEqual(len(run.line_ids), 1)
        self.assertEqual(run.line_ids.status, 'error')
        self.assertIn('Generate once first', run.line_ids.detail)

    def test_cron_runs_scaled_steps_without_module_install(self):
        self.env['ir.config_parameter'].sudo().set_param('demo_data_generator.cron_scale', '10')
        calls = []

        def fake_step(gen, key):
            calls.append((key, gen._selections.get(key)))
            return 1, 'ok'

        with patch.object(type(self.model), '_modules_ready', return_value=True), \
                patch.object(DemoGenerator, 'run_step', fake_step):
            run = self.model._cron_generate()
        keys = [k for k, _ in calls]
        expected = [k for k in DemoGenerator.STEP_KEYS if k != 'modules']
        if self.env['product.template'].search_count([('name', '=', 'Smart Display Pro')], limit=1):
            expected.remove('mto_showcase')
        self.assertEqual(keys, expected)
        self.assertEqual(dict(calls)['contacts'], 4)  # ceil(35 * 10%)
        self.assertEqual(dict(calls)['salespeople'], 5)  # fixed pool, never scaled
        self.assertEqual(run.scale, 10)
        self.assertEqual(run.state, 'done')
        self.assertEqual(len(run.line_ids), len(keys))

    def test_cron_scale_defaults_and_clamps(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('demo_data_generator.cron_scale', '')
        self.assertEqual(self.model._cron_scale(), 25)
        icp.set_param('demo_data_generator.cron_scale', '500')
        self.assertEqual(self.model._cron_scale(), 100)
        icp.set_param('demo_data_generator.cron_scale', '0')
        self.assertEqual(self.model._cron_scale(), 1)

    def test_cron_record_exists_and_is_active(self):
        cron = self.env.ref('demo_data_generator.ir_cron_daily_demo_data')
        self.assertTrue(cron.active)
        self.assertEqual((cron.interval_number, cron.interval_type), (1, 'days'))
