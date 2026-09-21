import json
import logging

from odoo import api, models
from odoo.exceptions import AccessError

from .env_api import EnvAPI
from .generators import DemoGenerator

_logger = logging.getLogger(__name__)
STATE_PARAM = 'demo_data_generator.state'


class DemoDataGenerator(models.AbstractModel):
    _name = 'demo.data.generator'
    _description = 'Demo Data Generator'

    def _check_admin(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError('Only administrators can generate demo data.')

    def _load_state(self):
        raw = self.env['ir.config_parameter'].sudo().get_param(STATE_PARAM)
        return json.loads(raw) if raw else {}

    def _save_state(self, state):
        self.env['ir.config_parameter'].sudo().set_param(STATE_PARAM, json.dumps(state))

    @api.model
    def get_steps(self):
        self._check_admin()
        return [{'key': k, 'label': DemoGenerator.STEP_LABELS[k]} for k in DemoGenerator.STEP_KEYS]

    @api.model
    def run_step(self, key):
        self._check_admin()
        gen = DemoGenerator(EnvAPI(self.env))
        if key == 'modules':
            # Fresh run: wipe state first. Module install commits and swaps the
            # registry, so do not touch state after it.
            self._save_state({})
        else:
            gen.from_state(self._load_state())
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
        except Exception as e:  # noqa: BLE001 - one failing step must not abort the run
            _logger.exception('Demo data step %s failed', key)
            return {'status': 'error', 'detail': str(e)[:200], 'count': 0}
        if key != 'modules':
            self._save_state(gen.to_state())
        return {'status': 'done', 'detail': detail, 'count': count}
