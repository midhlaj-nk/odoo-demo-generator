from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    demo_daily_scale = fields.Integer(
        string='Daily Demo Data Volume (%)',
        config_parameter='demo_data_generator.cron_scale',
        default=25,
        help='Percentage of the full demo batch the daily scheduled action creates. '
             '100 = the same ~465 records as the Generate button.',
    )
