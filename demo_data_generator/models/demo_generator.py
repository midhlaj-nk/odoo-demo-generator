import json
import logging
import time

from odoo import api, models
from odoo.exceptions import AccessError

from .env_api import EnvAPI
from .generators import DemoGenerator

_logger = logging.getLogger(__name__)
STATE_PARAM = 'demo_data_generator.state'
SCALE_PARAM = 'demo_data_generator.cron_scale'
DEFAULT_CRON_SCALE = 25
# Models that only exist once the business modules are installed
REQUIRED_MODELS = ('sale.order', 'purchase.order', 'mrp.production', 'crm.lead', 'project.task', 'fleet.vehicle')


class DemoDataGenerator(models.AbstractModel):
    _name = 'demo.data.generator'
    _description = 'Demo Data Generator'

    # -- helpers --

    def _check_admin(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError('Only administrators can generate demo data.')

    def _load_state(self):
        raw = self.env['ir.config_parameter'].sudo().get_param(STATE_PARAM)
        return json.loads(raw) if raw else {}

    def _save_state(self, state):
        self.env['ir.config_parameter'].sudo().set_param(STATE_PARAM, json.dumps(state))

    def _modules_ready(self):
        return all(model in self.env for model in REQUIRED_MODELS)

    def _execute_step(self, gen, key, run=None):
        """Run one step with error isolation; log it on ``run`` when given."""
        started = time.monotonic()
        try:
            if key == 'modules':
                # button_immediate_install commits and reloads the registry, so
                # it cannot run inside a savepoint.
                count, detail = gen.run_step(key)
            else:
                # Savepoint: a failed step rolls back cleanly and the cursor
                # stays usable for the response and the state write.
                with self.env.cr.savepoint():
                    count, detail = gen.run_step(key)
            result = {'status': 'done', 'detail': detail, 'count': count}
        except Exception as e:  # noqa: BLE001 - one failing step must not abort the run
            _logger.exception('Demo data step %s failed', key)
            result = {'status': 'error', 'detail': str(e)[:200], 'count': 0}
        if run:
            run.add_line(key, DemoGenerator.STEP_LABELS.get(key, key), result, time.monotonic() - started)
        return result

    # -- RPC surface (manual run from the client action) --

    @api.model
    def get_steps(self):
        self._check_admin()
        return [{'key': k, 'label': DemoGenerator.STEP_LABELS[k]} for k in DemoGenerator.STEP_KEYS]

    @api.model
    def start_run(self):
        self._check_admin()
        self._save_state({})
        return self.env['demo.data.run'].create({'trigger': 'manual', 'scale': 100}).id

    @api.model
    def run_step(self, key, run_id=None):
        self._check_admin()
        gen = DemoGenerator(EnvAPI(self.env))
        if key == 'modules':
            # Fresh run: wipe state first. Module install commits and swaps the
            # registry, so do not touch state after it.
            self._save_state({})
        else:
            gen.from_state(self._load_state())
        run = self.env['demo.data.run'].browse(run_id) if run_id else None
        result = self._execute_step(gen, key, run)
        if key != 'modules':
            self._save_state(gen.to_state())
        return result

    @api.model
    def finish_run(self, run_id):
        self._check_admin()
        run = self.env['demo.data.run'].browse(run_id)
        run.action_finish()
        return {'state': run.state, 'record_count': run.record_count, 'error_count': run.error_count}

    # -- Scheduled action --

    @api.model
    def _cron_scale(self):
        raw = self.env['ir.config_parameter'].sudo().get_param(SCALE_PARAM)
        try:
            scale = int(raw) if raw else DEFAULT_CRON_SCALE
        except (TypeError, ValueError):
            scale = DEFAULT_CRON_SCALE
        return max(1, min(scale, 100))

    @api.model
    def _cron_generate(self):
        scale = self._cron_scale()
        run = self.env['demo.data.run'].create({'trigger': 'cron', 'scale': scale})
        if not self._modules_ready():
            run.add_line('modules', DemoGenerator.STEP_LABELS['modules'], {
                'status': 'error',
                'detail': 'Business modules are not installed. Open Demo Data and click Generate once first.',
            }, 0.0)
            run.action_finish()
            return run
        gen = DemoGenerator(EnvAPI(self.env))
        gen.set_scale(scale)
        showcase_exists = bool(self.env['product.template'].search_count(
            [('name', '=', 'Smart Display Pro')], limit=1))
        for key in DemoGenerator.STEP_KEYS:
            if key == 'modules':
                continue
            if key == 'mto_showcase' and showcase_exists:
                continue  # one showcase product is enough; do not duplicate it daily
            self._execute_step(gen, key, run)
        run.action_finish()
        _logger.info('Scheduled demo data run %s: %s records, %s errors', run.name, run.record_count, run.error_count)
        return run
