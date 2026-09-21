from odoo.tests import TransactionCase, tagged

from ..models.env_api import EnvAPI


@tagged('post_install', '-at_install')
class TestEnvAPI(TransactionCase):
    def setUp(self):
        super().setUp()
        self.api = EnvAPI(self.env)

    def test_create_single_returns_int(self):
        pid = self.api.create('res.partner', {'name': 'EnvAPI One'})
        self.assertIsInstance(pid, int)

    def test_create_batch_returns_list(self):
        ids = self.api.create('res.partner', [{'name': 'A'}, {'name': 'B'}])
        self.assertEqual(len(ids), 2)

    def test_search_read_and_write(self):
        pid = self.api.create('res.partner', {'name': 'EnvAPI Two'})
        self.assertEqual(self.api.search('res.partner', [('name', '=', 'EnvAPI Two')]), [pid])
        rows = self.api.search_read('res.partner', [('id', '=', pid)], ['name'])
        self.assertEqual(rows[0]['name'], 'EnvAPI Two')
        self.api.write('res.partner', [pid], {'name': 'Renamed'})
        self.assertEqual(self.api.read('res.partner', [pid], ['name'])[0]['name'], 'Renamed')

    def test_search_context_active_test(self):
        pid = self.api.create('res.partner', {'name': 'Archived', 'active': False})
        self.assertEqual(self.api.search('res.partner', [('id', '=', pid)]), [])
        self.assertEqual(
            self.api.search('res.partner', [('id', '=', pid)], context={'active_test': False}),
            [pid],
        )

    def test_api_call_on_records(self):
        pid = self.api.create('res.partner', {'name': 'Call', 'active': True})
        self.api.api_call('res.partner', 'write', [[pid], {'name': 'Called'}])
        self.assertEqual(self.env['res.partner'].browse(pid).name, 'Called')

    def test_api_call_model_create_with_context(self):
        rid = self.api.api_call(
            'res.partner', 'create', [{'name': 'Ctx'}], {'context': {'lang': 'en_US'}}
        )
        self.assertIsInstance(rid, int)

    def test_has_field(self):
        self.assertTrue(self.api.has_field('res.partner', 'name'))
        self.assertFalse(self.api.has_field('res.partner', 'no_such_field_xyz'))

    def test_many2one_values_are_lists(self):
        company = self.env.ref('base.main_company')
        pid = self.api.create('res.partner', {'name': 'M2O', 'company_id': company.id})
        row = self.api.read('res.partner', [pid], ['company_id'])[0]
        self.assertIsInstance(row['company_id'], list)
        self.assertEqual(row['company_id'][0], company.id)
        row = self.api.search_read('res.partner', [('id', '=', pid)], ['company_id'])[0]
        self.assertIsInstance(row['company_id'], list)
