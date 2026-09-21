from odoo import api, fields, models

NON_RECORD_STEPS = ('modules', 'publish_website')


class DemoDataRun(models.Model):
    _name = 'demo.data.run'
    _description = 'Demo Data Generation Run'
    _order = 'date_start desc, id desc'

    name = fields.Char(required=True, default='Run')
    trigger = fields.Selection(
        [('manual', 'Manual'), ('cron', 'Scheduled')], required=True, default='manual',
    )
    date_start = fields.Datetime(string='Started', default=fields.Datetime.now, required=True)
    date_end = fields.Datetime(string='Finished')
    duration = fields.Float(string='Duration (s)', compute='_compute_duration', store=True)
    state = fields.Selection(
        [('running', 'Running'), ('done', 'Done'), ('partial', 'Done with errors'), ('failed', 'Failed')],
        default='running', required=True,
    )
    scale = fields.Integer(string='Volume (%)', default=100)
    record_count = fields.Integer(string='Records Created', compute='_compute_counts', store=True)
    error_count = fields.Integer(string='Errors', compute='_compute_counts', store=True)
    line_ids = fields.One2many('demo.data.run.line', 'run_id', string='Steps')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == 'Run':
                start = fields.Datetime.to_datetime(vals.get('date_start')) or fields.Datetime.now()
                vals['name'] = f"Run {start.strftime('%Y-%m-%d %H:%M')}"
        return super().create(vals_list)

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for run in self:
            run.duration = (run.date_end - run.date_start).total_seconds() if run.date_end and run.date_start else 0.0

    @api.depends('line_ids.status', 'line_ids.count', 'line_ids.step_key')
    def _compute_counts(self):
        for run in self:
            lines = run.line_ids
            run.error_count = len(lines.filtered(lambda l: l.status == 'error'))
            run.record_count = sum(
                l.count for l in lines if l.status == 'done' and l.step_key not in NON_RECORD_STEPS
            )

    def add_line(self, key, label, result, duration):
        self.ensure_one()
        return self.env['demo.data.run.line'].create({
            'run_id': self.id,
            'sequence': len(self.line_ids) + 1,
            'step_key': key,
            'name': label,
            'status': result['status'],
            'count': result.get('count', 0),
            'detail': result.get('detail', ''),
            'duration': duration,
        })

    def action_finish(self):
        for run in self:
            if not run.line_ids or all(l.status == 'error' for l in run.line_ids):
                state = 'failed'
            elif run.error_count:
                state = 'partial'
            else:
                state = 'done'
            run.write({'state': state, 'date_end': fields.Datetime.now()})
        return True


class DemoDataRunLine(models.Model):
    _name = 'demo.data.run.line'
    _description = 'Demo Data Generation Step'
    _order = 'sequence, id'

    run_id = fields.Many2one('demo.data.run', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer(default=1)
    step_key = fields.Char(required=True)
    name = fields.Char(string='Step', required=True)
    status = fields.Selection([('done', 'Done'), ('error', 'Error')], required=True)
    count = fields.Integer(string='Records')
    detail = fields.Char()
    duration = fields.Float(string='Duration (s)')
