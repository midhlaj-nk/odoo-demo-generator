import base64
import io
import logging
import math
import random
import string
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from .sample_data import (
    PRODUCTS, RAW_MATERIALS, SERVICES, WORK_CENTERS, BOM_TEMPLATES,
    PROJECTS, TASK_NAMES, TIMESHEET_DESCRIPTIONS, EXPENSE_ITEMS,
    JOB_TITLES, DEPARTMENTS, VEHICLE_BRANDS_MODELS, CRM_NAMES,
    OPERATION_NAMES, JOURNAL_ENTRY_TEMPLATES,
    FIRST_NAMES, LAST_NAMES, COMPANY_WORDS, COMPANY_SUFFIXES, STREET_NAMES, CITIES,
)

_logger = logging.getLogger(__name__)

DAYS_BACK = 730  # 2 years


def _rand_date():
    days = random.randint(0, DAYS_BACK)
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')


def _rand_datetime():
    days = random.randint(0, DAYS_BACK)
    hours = random.randint(8, 17)
    mins = random.choice([0, 15, 30, 45])
    dt = datetime.now() - timedelta(days=days)
    dt = dt.replace(hour=hours, minute=mins, second=0)
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def _as_list(result):
    """Normalize create result to list of IDs."""
    if isinstance(result, list):
        return result
    return [result]


def _fake_name():
    return f'{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}'


def _fake_company():
    return f'{random.choice(COMPANY_WORDS)} {random.choice(COMPANY_SUFFIXES)}'


def _slug(text):
    return ''.join(c for c in text.lower() if c.isalnum())


def _fake_email(name=None):
    name = name or _fake_name()
    return f'{_slug(name)}{random.randint(1, 99)}@example.com'


def _fake_company_email(company=None):
    company = company or _fake_company()
    return f'info@{_slug(company)}.com'


def _fake_phone():
    return f'+1 {random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}'


def _fake_street():
    return f'{random.randint(10, 9999)} {random.choice(STREET_NAMES)}'


def _fake_city():
    return random.choice(CITIES)


def _fake_zip():
    return f'{random.randint(10000, 99999)}'


def _fake_plate():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    digits = ''.join(random.choices(string.digits, k=4))
    return f'{letters}-{digits}'


def _product_image(name):
    """Generate a placeholder product image as base64 PNG."""
    h = sum(ord(c) for c in name)
    r = (h * 37) % 160 + 40
    g = (h * 73) % 160 + 40
    b = (h * 113) % 160 + 40
    img = Image.new('RGB', (256, 256), (r, g, b))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:
        font = ImageFont.load_default()
    # Simple word-wrap
    words = name.split()
    lines, line = [], ''
    for word in words:
        test = f'{line} {word}'.strip()
        if len(test) > 16 and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    text = '\n'.join(lines)
    draw.multiline_text((128, 128), text, fill='white', anchor='mm', align='center', font=font)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


DEFAULT_COUNTS = {
    'contacts': 35, 'products': 30, 'employees': 20, 'salespeople': 5,
    'work_centers': 8, 'boms': 5, 'operations': 15,
    'projects': 8, 'tasks': 35,
    'purchase_orders': 30, 'sales': 35, 'invoices': 35,
    'crm_leads': 35, 'manufacturing_orders': 15,
    'deliveries': 25, 'receipts': 25, 'inventory': 10,
    'timesheets': 40, 'expenses': 25, 'vehicles': 12,
    'journal_entries': 30,
}


class DemoGenerator:
    GENERATION_ORDER = [
        'contacts', 'employees', 'salespeople', 'products', 'work_centers',
        'boms', 'operations', 'projects', 'tasks',
        'purchase_orders',
        'sales', 'invoices', 'journal_entries', 'crm_leads',
        'manufacturing_orders', 'deliveries', 'receipts',
        'inventory', 'timesheets', 'expenses', 'vehicles',
    ]

    MODULE_MAP = {
        'contacts': [],
        'employees': ['hr'],
        'salespeople': ['sale_management', 'crm'],
        'products': [],
        'work_centers': ['mrp'],
        'boms': ['mrp'],
        'operations': ['mrp'],
        'projects': ['project'],
        'tasks': ['project'],
        'sales': ['sale_management'],
        'purchase_orders': ['purchase'],
        'invoices': ['account'],
        'journal_entries': ['account'],
        'crm_leads': ['crm'],
        'manufacturing_orders': ['mrp'],
        'deliveries': ['stock'],
        'receipts': ['stock'],
        'inventory': ['stock'],
        'timesheets': ['hr_timesheet'],
        'expenses': ['hr_expense'],
        'vehicles': ['fleet'],
    }

    def __init__(self, api):
        self.api = api
        self.ids = {
            'partner': [],
            'product': [],
            'product_tmpl': [],
            'employee': [],
            'salesperson': [],
            'project': [],
            'task': [],
            'workcenter': [],
            'bom': [],
            'bom_product_map': {},
            'sale_order': [],
        }
        self._product_info = {}  # product_id -> {name, list_price, standard_price}
        self._cache = {}
        self._selections = dict(DEFAULT_COUNTS)
        self._po_done = False

    # -- Module install --

    # Always install these regardless of selections
    ALWAYS_INSTALL = [
        'accountant', 'account', 'website', 'website_sale', 'payment_demo',
        'sale_management', 'stock', 'mrp', 'purchase',
    ]

    def _install_modules(self, selections):
        needed = set(self.ALWAYS_INSTALL)
        for dtype, count in selections.items():
            if count > 0:
                needed.update(self.MODULE_MAP.get(dtype, []))
        # Check which modules exist and their state
        all_mods = self.api.search_read(
            'ir.module.module',
            [('name', 'in', list(needed))],
            ['name', 'state'],
        )
        found_names = {m['name'] for m in all_mods}
        missing = needed - found_names
        if missing:
            _logger.info(f"  Modules not found in registry: {', '.join(sorted(missing))}")
        already = [m['name'] for m in all_mods if m['state'] == 'installed']
        if already:
            _logger.info(f"  Already installed: {', '.join(sorted(already))}")
        to_install = [m for m in all_mods if m['state'] != 'installed']
        if not to_install:
            return []
        names = [m['name'] for m in to_install]
        mod_ids = [m['id'] for m in to_install]
        for n in names:
            _logger.info(f"  Installing: {n}...")
        # Install all at once
        self.api.api_call('ir.module.module', 'button_immediate_install', [mod_ids])
        return names

    # -- Step API --

    STEP_KEYS = ['modules', 'configure'] + GENERATION_ORDER + ['mto_showcase', 'publish_website']

    STEP_LABELS = {
        'modules': 'Installing modules', 'configure': 'Configuring settings',
        'contacts': 'Contacts', 'products': 'Products', 'employees': 'Employees',
        'salespeople': 'Salespeople',
        'work_centers': 'Work Centers', 'boms': 'Bills of Materials', 'operations': 'Operations',
        'projects': 'Projects', 'tasks': 'Tasks', 'sales': 'Sales Orders',
        'purchase_orders': 'Purchase Orders', 'invoices': 'Invoices', 'crm_leads': 'CRM Leads',
        'manufacturing_orders': 'Manufacturing Orders', 'deliveries': 'Deliveries',
        'receipts': 'Receipts', 'inventory': 'Inventory Transfers',
        'timesheets': 'Timesheets', 'expenses': 'Expenses', 'vehicles': 'Vehicles',
        'journal_entries': 'Journal Entries',
        'mto_showcase': 'MTO Products', 'publish_website': 'Publishing to Website',
    }

    def run_step(self, key):
        """Run one step. Returns (count, detail). Raises on failure."""
        if key == 'modules':
            installed = self._install_modules(self._selections)
            detail = f'Installed: {", ".join(installed)}' if installed else 'All modules ready'
            return 0, detail
        if key == 'configure':
            self._configure_settings()
            return 0, 'Settings configured'
        if key == 'mto_showcase':
            n = self._create_mto_showcase()
            return n, f'{n} MTO products'
        if key == 'publish_website':
            n = self._publish_products()
            return n, f'{n} published'
        if key not in self.GENERATION_ORDER:
            raise ValueError(f'Unknown step: {key}')
        count = self._selections.get(key, 0)
        created = getattr(self, f'gen_{key}')(count)
        return created, f'{created} created'

    UNSCALED_STEPS = ('salespeople',)  # a fixed pool, not daily volume

    def set_scale(self, percent):
        """Scale every step count to ``percent`` of the defaults (minimum 1)."""
        self._selections = {
            k: v if k in self.UNSCALED_STEPS else max(1, math.ceil(v * percent / 100.0))
            for k, v in DEFAULT_COUNTS.items()
        }

    def to_state(self):
        return {
            'ids': self.ids,
            'po_done': self._po_done,
            'mto_route': self._cache.get('mto_route'),
        }

    def from_state(self, state):
        if not state:
            return
        ids = dict(state.get('ids', {}))
        ids['bom_product_map'] = {int(k): v for k, v in ids.get('bom_product_map', {}).items()}
        self.ids.update(ids)
        self._po_done = bool(state.get('po_done'))
        if state.get('mto_route'):
            self._cache['mto_route'] = state['mto_route']

    # -- Lookups --

    def _get_uom_unit(self):
        if 'uom_unit' not in self._cache:
            ids = self.api.search('uom.uom', [('name', '=', 'Units')], limit=1)
            self._cache['uom_unit'] = ids[0] if ids else 1
        return self._cache['uom_unit']

    def _get_picking_type(self, code):
        key = f'picking_type_{code}'
        if key not in self._cache:
            ctx = {'active_test': False} if code == 'internal' else None
            ids = self.api.search(
                'stock.picking.type', [('code', '=', code)], limit=1, context=ctx
            )
            self._cache[key] = ids[0] if ids else False
        return self._cache[key]

    def _get_location(self, usage):
        key = f'location_{usage}'
        if key not in self._cache:
            ids = self.api.search('stock.location', [('usage', '=', usage)], limit=1)
            self._cache[key] = ids[0] if ids else False
        return self._cache[key]

    def _get_stock_location(self):
        if 'stock_loc' not in self._cache:
            ids = self.api.search(
                'stock.location',
                [('usage', '=', 'internal'), ('name', 'ilike', 'Stock')],
                limit=1,
            )
            if not ids:
                ids = self.api.search('stock.location', [('usage', '=', 'internal')], limit=1)
            self._cache['stock_loc'] = ids[0] if ids else False
        return self._cache['stock_loc']

    def _load_product_info(self):
        """Bulk-load product info for all created products."""
        if self.ids['product'] and not self._product_info:
            data = self.api.read(
                'product.product', self.ids['product'],
                ['name', 'list_price', 'standard_price'],
            )
            for d in data:
                self._product_info[d['id']] = d

    # -- Dependency helpers --

    def _ensure_contacts(self, n=10):
        if not self.ids['partner']:
            self.gen_contacts(n)

    def _ensure_products(self, n=10):
        if not self.ids['product']:
            self.gen_products(n)

    def _ensure_employees(self, n=5):
        if not self.ids['employee']:
            self.gen_employees(n)

    def _ensure_salespeople(self, n=5):
        if not self.ids['salesperson']:
            self.gen_salespeople(n)

    def _ensure_projects(self, n=5):
        if not self.ids['project']:
            self.gen_projects(n)

    def _ensure_tasks(self, n=10):
        if not self.ids['task']:
            self.gen_tasks(n)

    def _ensure_work_centers(self, n=3):
        if not self.ids['workcenter']:
            self.gen_work_centers(n)

    def _ensure_boms(self, n=3):
        if not self.ids['bom']:
            self.gen_boms(n)

    def _ensure_purchase_orders(self):
        """Auto-create and receive POs if stock is needed but POs weren't selected."""
        if not self._po_done:
            n = max(5, len(self.ids['product']) // 3)
            _logger.info(f"  [auto] creating {n} POs for stock supply...")
            self.gen_purchase_orders(n)

    def _calc_supply_needed(self):
        """Estimate units per product to purchase to cover all downstream demand."""
        s = self._selections
        n = max(len(self.ids['product']), 1)
        total = 0
        # Sales: count × avg_lines(3) × avg_qty(12)
        total += s.get('sales', 0) * 3 * 12
        # Extra SOs auto-created by invoices
        total += max(0, s.get('invoices', 0) - s.get('sales', 0)) * 3 * 12
        # Deliveries: count × avg_moves(2) × avg_qty(18)
        total += s.get('deliveries', 0) * 2 * 18
        # MO components: count × avg_qty(12) × avg_components(4) × avg_comp_qty(2)
        total += s.get('manufacturing_orders', 0) * 12 * 4 * 2
        # Per product with 2× buffer
        return int((total * 2) / n) + 50

    # -- Workflow helpers --

    def _validate_pickings(self, picking_ids):
        """Set done quantities and validate pickings."""
        if not picking_ids:
            return
        # Check availability
        self.api.api_call('stock.picking', 'action_assign', [picking_ids])
        # Set done quantities on all moves — batch by same quantity to reduce API calls
        move_ids = self.api.search(
            'stock.move',
            [('picking_id', 'in', picking_ids), ('state', 'not in', ['done', 'cancel'])],
        )
        if move_ids:
            moves = self.api.read('stock.move', move_ids, ['product_uom_qty'])
            # Group moves by quantity for batch writes
            qty_groups = {}
            for m in moves:
                qty = m['product_uom_qty']
                qty_groups.setdefault(qty, []).append(m['id'])
            for qty, ids in qty_groups.items():
                self.api.write('stock.move', ids, {'quantity': qty})
        # Validate — try batch first, fall back to individual
        ctx = {
            'skip_backorder': True, 'picking_ids_not_to_backorder': picking_ids,
            'skip_sms': True, 'skip_immediate': True, 'skip_expired': True,
        }
        try:
            self.api.api_call('stock.picking', 'button_validate', [picking_ids], {'context': ctx})
        except Exception:
            for pid in picking_ids:
                try:
                    self.api.api_call('stock.picking', 'button_validate', [[pid]], {'context': ctx})
                except Exception:
                    pass

    # -- Configuration --

    def _configure_settings(self):
        """Configure MTO route, automatic invoicing, and Demo payment provider."""
        # Find all routes in one query (including archived)
        all_routes = self.api.search_read(
            'stock.route',
            [('name', 'ilike', '%order%')],
            ['name'], context={'active_test': False},
        )
        mto_route = None
        for r in all_routes:
            if 'replenish on order' in r['name'].lower() or 'make to order' in r['name'].lower():
                mto_route = r['id']
                break
        if mto_route:
            self.api.write('stock.route', [mto_route], {'active': True})
            self._cache['mto_route'] = mto_route
            _logger.info("  MTO route enabled")

        # Enable automatic invoicing on online payment
        try:
            config_id = self.api.create('res.config.settings', {
                'automatic_invoice': True,
            })
            self.api.api_call('res.config.settings', 'execute', [[config_id]])
            _logger.info("  Automatic invoicing enabled")
        except Exception as e:
            _logger.info(f"  Auto-invoice setting: {e}")

        # Enable Demo payment provider
        demo = self.api.search_read(
            'payment.provider',
            ['|', ('code', '=', 'demo'), ('name', 'ilike', 'demo')],
            ['name'], context={'active_test': False},
        )
        if demo:
            self.api.write('payment.provider', [demo[0]['id']], {
                'state': 'test',
                'is_published': True,
            })
            _logger.info("  Demo payment provider enabled")

    def _create_mto_showcase(self):
        """Create a finished good with MTO+Manufacture route, raw materials with Buy route, BOM, and vendors."""
        uom = self._get_uom_unit()

        # Find routes — use cache or single batch query
        mto_id = self._cache.get('mto_route')
        buy_id = self._cache.get('buy_route')
        mfg_id = self._cache.get('mfg_route')
        if not all([mto_id, buy_id, mfg_id]):
            routes = self.api.search_read('stock.route', [], ['name'], context={'active_test': False})
            for r in routes:
                name_l = r['name'].lower()
                if not mto_id and ('replenish on order' in name_l or 'make to order' in name_l):
                    mto_id = r['id']
                elif not buy_id and name_l == 'buy':
                    buy_id = r['id']
                elif not mfg_id and name_l == 'manufacture':
                    mfg_id = r['id']
            self._cache['mto_route'] = mto_id
            self._cache['buy_route'] = buy_id
            self._cache['mfg_route'] = mfg_id

        if not all([mto_id, buy_id, mfg_id]):
            raise Exception(f'Missing routes: MTO={mto_id}, Buy={buy_id}, Manufacture={mfg_id}')

        # Pick a vendor
        self._ensure_contacts(5)
        vendors = [p for p in self.ids['partner']]
        vendor_id = vendors[0] if vendors else False

        # Raw materials with MTO + Buy route — batch create
        raw_materials = [
            {'name': 'Processor Module', 'price': 85.00, 'cost': 52.00},
            {'name': 'Touch Display Panel', 'price': 145.00, 'cost': 88.00},
            {'name': 'Aluminum Enclosure', 'price': 35.00, 'cost': 18.00},
        ]
        raw_vals = [{
            'name': rm['name'], 'type': 'consu', 'is_storable': True,
            'list_price': rm['price'], 'standard_price': rm['cost'],
            'uom_id': uom, 'route_ids': [(6, 0, [mto_id, buy_id])],
            'image_1920': _product_image(rm['name']),
        } for rm in raw_materials]
        # Also create the finished good in the same batch
        all_vals = raw_vals + [{
            'name': 'Smart Display Pro', 'type': 'consu', 'is_storable': True,
            'list_price': 499.00, 'standard_price': 280.00,
            'uom_id': uom, 'route_ids': [(6, 0, [mto_id, mfg_id])],
            'invoice_policy': 'order',
            'image_1920': _product_image('Smart Display Pro'),
        }]
        all_tmpl_ids = _as_list(self.api.create('product.template', all_vals))
        raw_tmpl_ids = all_tmpl_ids[:3]
        fg_tmpl_id = all_tmpl_ids[3]

        # Batch lookup product.product IDs
        all_pp = self.api.search_read('product.product', [('product_tmpl_id', 'in', all_tmpl_ids)], ['product_tmpl_id'])
        tmpl_to_pp = {d['product_tmpl_id'][0]: d['id'] for d in all_pp}
        raw_pp_ids = [tmpl_to_pp[t] for t in raw_tmpl_ids]
        fg_pp = [tmpl_to_pp[fg_tmpl_id]]

        # Batch create vendor pricing
        if vendor_id:
            supplier_vals = [{'product_tmpl_id': tmpl_id, 'partner_id': vendor_id, 'price': rm['cost']}
                             for tmpl_id, rm in zip(raw_tmpl_ids, raw_materials)]
            self.api.create('product.supplierinfo', supplier_vals)

        # BOM
        bom_lines = [
            (0, 0, {'product_id': raw_pp_ids[0], 'product_qty': 1}),
            (0, 0, {'product_id': raw_pp_ids[1], 'product_qty': 1}),
            (0, 0, {'product_id': raw_pp_ids[2], 'product_qty': 2}),
        ]
        self.api.create('mrp.bom', {
            'product_tmpl_id': fg_tmpl_id,
            'product_qty': 1.0,
            'bom_line_ids': bom_lines,
        })

        # Track these IDs
        self.ids['product_tmpl'].extend(raw_tmpl_ids + [fg_tmpl_id])
        self.ids['product'].extend(raw_pp_ids + fg_pp)

        _logger.info(f"  MTO showcase: Smart Display Pro + {len(raw_materials)} raw materials")
        return 1 + len(raw_materials)

    def _publish_products(self):
        """Publish all product templates on the eCommerce website."""
        tmpl_ids = self.ids['product_tmpl']
        if not tmpl_ids:
            return 0
        self.api.write('product.template', tmpl_ids, {'website_published': True})
        _logger.info(f"  Published {len(tmpl_ids)} products on website")
        return len(tmpl_ids)

    # -- Generators (batch) --

    def gen_contacts(self, count):
        # Rank fields come from the account module, which may not be installed yet
        has_rank = self.api.has_field('res.partner', 'customer_rank')
        vals_list = []
        for i in range(count):
            is_company = (i % 3 == 0)
            name = _fake_company() if is_company else _fake_name()
            vals = {
                'name': name,
                'is_company': is_company,
                'email': _fake_company_email(name) if is_company else _fake_email(name),
                'phone': _fake_phone(),
                'street': _fake_street(),
                'city': _fake_city(),
                'zip': _fake_zip(),
            }
            if has_rank:
                vals['customer_rank'] = 1 if random.random() > 0.3 else 0
                vals['supplier_rank'] = 1 if random.random() > 0.7 else 0
            vals_list.append(vals)
        ids = _as_list(self.api.create('res.partner', vals_list))
        self.ids['partner'].extend(ids)
        return len(ids)

    def gen_products(self, count):
        all_products = PRODUCTS + RAW_MATERIALS + SERVICES
        items = random.sample(all_products, min(count, len(all_products)))
        if count > len(items):
            items += random.choices(all_products, k=count - len(items))
        uom = self._get_uom_unit()
        vals_list = []
        for item in items:
            is_service = item in SERVICES
            vals = {
                'name': item['name'],
                'list_price': item['price'],
                'standard_price': item['cost'],
                'type': 'service' if is_service else 'consu',
                'uom_id': uom,
                'image_1920': _product_image(item['name']),
            }
            if not is_service:
                vals['is_storable'] = True
            vals_list.append(vals)
        tmpl_ids = _as_list(self.api.create('product.template', vals_list))
        self.ids['product_tmpl'].extend(tmpl_ids)
        # Batch fetch product.product IDs
        pp_ids = self.api.search('product.product', [('product_tmpl_id', 'in', tmpl_ids)])
        self.ids['product'].extend(pp_ids)
        return len(tmpl_ids)

    def gen_employees(self, count):
        # Pre-create departments — batch search + batch create
        existing_depts = self.api.search_read('hr.department', [('name', 'in', DEPARTMENTS)], ['name'])
        dept_ids = {d['name']: d['id'] for d in existing_depts}
        missing_depts = [n for n in DEPARTMENTS if n not in dept_ids]
        if missing_depts:
            new_ids = _as_list(self.api.create('hr.department', [{'name': n} for n in missing_depts]))
            for name, did in zip(missing_depts, new_ids):
                dept_ids[name] = did
        vals_list = []
        for i in range(count):
            name = _fake_name()
            vals_list.append({
                'name': name,
                'job_title': random.choice(JOB_TITLES),
                'work_email': _fake_email(name),
                'department_id': dept_ids[random.choice(DEPARTMENTS)],
            })
        ids = _as_list(self.api.create('hr.employee', vals_list))
        self.ids['employee'].extend(ids)
        return len(ids)

    SALES_GROUPS = ['base.group_user', 'sales_team.group_sale_salesman']

    def gen_salespeople(self, count):
        """Create (or reuse) internal users with Sales rights to spread
        quotations and opportunities across several salespeople."""
        self._ensure_employees(count)
        logins = [f'sales{i}@example.com' for i in range(1, count + 1)]
        existing = self.api.search_read(
            'res.users', [('login', 'in', logins)], ['login'], context={'active_test': False},
        )
        by_login = {u['login']: u['id'] for u in existing}
        group_ids = []
        for xmlid in self.SALES_GROUPS:
            gid = self.api.api_call('ir.model.data', '_xmlid_to_res_id', [xmlid], {'raise_if_not_found': False})
            if gid:
                group_ids.append(gid)
        group_field = 'group_ids' if self.api.has_field('res.users', 'group_ids') else 'groups_id'
        missing = [l for l in logins if l not in by_login]
        created = 0
        if missing:
            vals_list = []
            for login in missing:
                vals = {'name': _fake_name(), 'login': login, 'email': login}
                if group_ids:
                    vals[group_field] = [(6, 0, group_ids)]
                vals_list.append(vals)
            new_ids = _as_list(self.api.api_call(
                'res.users', 'create', [vals_list],
                {'context': {'no_reset_password': True, 'mail_create_nolog': True}},
            ))
            for login, uid in zip(missing, new_ids):
                by_login[login] = uid
            created = len(new_ids)
        pool = [by_login[l] for l in logins if l in by_login]
        self.ids['salesperson'].extend(pool)
        # Link salespeople to employees so HR and Sales line up
        if created and self.ids['employee'] and self.api.has_field('hr.employee', 'user_id'):
            free = self.api.search_read(
                'hr.employee', [('id', 'in', self.ids['employee']), ('user_id', '=', False)], ['id'],
                limit=len(pool),
            )
            for emp, uid in zip(free, pool):
                try:
                    self.api.write('hr.employee', [emp['id']], {'user_id': uid})
                except Exception as e:  # noqa: BLE001 - linking is cosmetic
                    _logger.info('Could not link employee %s to user %s: %s', emp['id'], uid, e)
        return created

    def gen_work_centers(self, count):
        items = WORK_CENTERS[:count] if count <= len(WORK_CENTERS) else (
            WORK_CENTERS + random.choices(WORK_CENTERS, k=count - len(WORK_CENTERS))
        )
        vals_list = [{'name': w['name'], 'costs_hour': w['cost'], 'time_efficiency': 100} for w in items]
        ids = _as_list(self.api.create('mrp.workcenter', vals_list))
        self.ids['workcenter'].extend(ids)
        return len(ids)

    def gen_boms(self, count):
        self._ensure_products(10)
        uom = self._get_uom_unit()

        # Build name→tmpl_id map from existing products
        tmpl_data = self.api.read('product.template', self.ids['product_tmpl'], ['name'])
        name_to_tmpl = {d['name']: d['id'] for d in tmpl_data}

        templates = BOM_TEMPLATES[:count] if count <= len(BOM_TEMPLATES) else (
            BOM_TEMPLATES + random.choices(BOM_TEMPLATES, k=count - len(BOM_TEMPLATES))
        )

        # Collect all product names we need
        needed_names = set()
        for t in templates:
            needed_names.add(t['product'])
            for comp_name, _ in t['components']:
                needed_names.add(comp_name)

        # Create any missing products in batch
        missing = []
        for name in needed_names:
            if name not in name_to_tmpl:
                match = [p for p in PRODUCTS + RAW_MATERIALS if p['name'] == name]
                price = match[0]['price'] if match else 50.0
                cost = match[0]['cost'] if match else 25.0
                missing.append({'name': name, 'list_price': price, 'standard_price': cost, 'type': 'consu', 'is_storable': True, 'uom_id': uom})

        if missing:
            new_tmpl_ids = _as_list(self.api.create('product.template', missing))
            self.ids['product_tmpl'].extend(new_tmpl_ids)
            new_data = self.api.read('product.template', new_tmpl_ids, ['name'])
            for d in new_data:
                name_to_tmpl[d['name']] = d['id']
            new_pp = self.api.search('product.product', [('product_tmpl_id', 'in', new_tmpl_ids)])
            self.ids['product'].extend(new_pp)

        # Build tmpl→pp map
        all_tmpl = list(name_to_tmpl.values())
        pp_data = self.api.search_read('product.product', [('product_tmpl_id', 'in', all_tmpl)], ['product_tmpl_id'])
        tmpl_to_pp = {d['product_tmpl_id'][0]: d['id'] for d in pp_data}

        # Create BOMs one at a time (each has unique lines)
        created = 0
        for template in templates:
            prod_tmpl_id = name_to_tmpl.get(template['product'])
            if not prod_tmpl_id:
                continue
            bom_lines = []
            for comp_name, qty in template['components']:
                comp_tmpl = name_to_tmpl.get(comp_name)
                comp_pp = tmpl_to_pp.get(comp_tmpl)
                if comp_pp:
                    bom_lines.append((0, 0, {'product_id': comp_pp, 'product_qty': qty}))

            bom_id = self.api.create('mrp.bom', {
                'product_tmpl_id': prod_tmpl_id,
                'product_qty': 1.0,
                'bom_line_ids': bom_lines,
            })
            self.ids['bom'].append(bom_id)
            pp_id = tmpl_to_pp.get(prod_tmpl_id)
            if pp_id:
                self.ids['bom_product_map'][bom_id] = pp_id
            created += 1
        return created

    def gen_operations(self, count):
        self._ensure_work_centers(3)
        self._ensure_boms(2)
        vals_list = []
        for _ in range(count):
            vals_list.append({
                'name': random.choice(OPERATION_NAMES),
                'workcenter_id': random.choice(self.ids['workcenter']),
                'bom_id': random.choice(self.ids['bom']),
                'time_cycle_manual': round(random.uniform(5, 60), 1),
            })
        ids = _as_list(self.api.create('mrp.routing.workcenter', vals_list))
        return len(ids)

    def gen_projects(self, count):
        names = random.sample(PROJECTS, min(count, len(PROJECTS)))
        if count > len(names):
            names += [f'{random.choice(PROJECTS)} ({i})' for i in range(count - len(names))]
        vals_list = [{'name': n, 'date_start': _rand_date()} for n in names]
        ids = _as_list(self.api.create('project.project', vals_list))
        self.ids['project'].extend(ids)
        return len(ids)

    def gen_tasks(self, count):
        self._ensure_projects(5)
        # Fetch task stages for distribution
        stage_ids = self.api.search_read('project.task.type', [], ['id'], limit=20)
        stages = [s['id'] for s in stage_ids] if stage_ids else []
        vals_list = []
        for _ in range(count):
            d = random.randint(0, DAYS_BACK)
            deadline = (datetime.now() - timedelta(days=d) + timedelta(days=random.randint(7, 90))).strftime('%Y-%m-%d')
            vals = {
                'name': random.choice(TASK_NAMES),
                'project_id': random.choice(self.ids['project']),
                'date_deadline': deadline,
            }
            if stages:
                vals['stage_id'] = random.choice(stages)
            vals_list.append(vals)
        ids = _as_list(self.api.create('project.task', vals_list))
        self.ids['task'].extend(ids)
        return len(ids)

    def gen_sales(self, count):
        self._ensure_contacts(10)
        self._ensure_products(10)
        self._ensure_salespeople()
        self._ensure_purchase_orders()
        self._load_product_info()
        vals_list = []
        for _ in range(count):
            lines = []
            for _ in range(random.randint(1, 5)):
                pid = random.choice(self.ids['product'])
                info = self._product_info.get(pid, {})
                lines.append((0, 0, {
                    'product_id': pid,
                    'name': info.get('name', 'Product'),
                    'product_uom_qty': random.randint(1, 20),
                    'price_unit': info.get('list_price', 10.0),
                }))
            vals = {
                'partner_id': random.choice(self.ids['partner']),
                'date_order': _rand_datetime(),
                'order_line': lines,
            }
            if self.ids['salesperson']:
                vals['user_id'] = random.choice(self.ids['salesperson'])
            vals_list.append(vals)
        ids = _as_list(self.api.create('sale.order', vals_list))
        self.ids['sale_order'].extend(ids)
        # Confirm sales orders
        _logger.info("confirming...")
        self.api.api_call('sale.order', 'action_confirm', [ids])
        # Validate auto-created delivery orders
        _logger.info("validating deliveries...")
        so_data = self.api.read('sale.order', ids, ['picking_ids'])
        picking_ids = []
        for so in so_data:
            picking_ids.extend(so.get('picking_ids', []))
        if picking_ids:
            self._validate_pickings(picking_ids)
        return len(ids)

    def gen_purchase_orders(self, count):
        self._ensure_contacts(10)
        self._ensure_products(10)
        self._load_product_info()

        supply_qty = self._calc_supply_needed()
        products = self.ids['product']

        # Ensure every product is covered across all POs
        # Distribute products in round-robin across POs
        vals_list = []
        for i in range(count):
            # Each PO gets a slice of products
            per_po = max(1, len(products) // count)
            start = i * per_po
            po_products = products[start:start + per_po]
            if i == count - 1:
                po_products = products[start:]  # last PO picks up remainder
            if not po_products:
                po_products = random.sample(products, min(3, len(products)))

            lines = []
            for pid in po_products:
                info = self._product_info.get(pid, {})
                lines.append((0, 0, {
                    'product_id': pid,
                    'name': info.get('name', 'Product'),
                    'product_qty': supply_qty,
                    'price_unit': info.get('standard_price', 10.0) or 10.0,
                }))
            vals_list.append({
                'partner_id': random.choice(self.ids['partner']),
                'date_order': _rand_datetime(),
                'order_line': lines,
            })

        ids = _as_list(self.api.create('purchase.order', vals_list))

        # Confirm POs
        _logger.info("confirming...")
        self.api.api_call('purchase.order', 'button_confirm', [ids])

        # Validate auto-created receipts → puts products in stock
        _logger.info("receiving...")
        po_data = self.api.read('purchase.order', ids, ['picking_ids'])
        picking_ids = []
        for po in po_data:
            picking_ids.extend(po.get('picking_ids', []))
        if picking_ids:
            self._validate_pickings(picking_ids)

        self._po_done = True
        return len(ids)

    def gen_invoices(self, count):
        # All invoices must come from sale orders
        needed = count - len(self.ids['sale_order'])
        if needed > 0:
            _logger.info(f"creating {needed} SOs first...")
            self.gen_sales(needed)

        so_ids = self.ids['sale_order'][:count]

        # Create invoices via the standard SO wizard
        _logger.info("invoicing SOs...")
        ctx = {'active_ids': so_ids, 'active_model': 'sale.order'}
        wiz_id = self.api.api_call(
            'sale.advance.payment.inv', 'create',
            [{'advance_payment_method': 'delivered'}],
            {'context': ctx},
        )
        self.api.api_call(
            'sale.advance.payment.inv', 'create_invoices',
            [_as_list(wiz_id)],
            {'context': ctx},
        )

        # Read back the invoice IDs from the SOs
        so_data = self.api.read('sale.order', so_ids, ['invoice_ids'])
        ids = []
        for so in so_data:
            ids.extend(so.get('invoice_ids', []))
        ids = list(set(ids))  # deduplicate

        if not ids:
            raise Exception('No invoices were created from sale orders.')

        # Post invoices (creates journal entries)
        _logger.info("posting...")
        self.api.api_call('account.move', 'action_post', [ids])
        # Register payments (marks invoices as paid)
        _logger.info("paying...")
        self._pay_invoices(ids)
        return len(ids)

    def _pay_invoices(self, ids):
        """Register payments for invoices via the payment wizard."""
        pay_ctx = {'active_model': 'account.move', 'active_ids': ids}
        try:
            wiz_id = self.api.api_call(
                'account.payment.register', 'create', [{}], {'context': pay_ctx},
            )
            self.api.api_call(
                'account.payment.register', 'action_create_payments',
                [_as_list(wiz_id)], {'context': pay_ctx},
            )
        except Exception:
            for inv_id in ids:
                try:
                    ctx = {'active_model': 'account.move', 'active_ids': [inv_id]}
                    wid = self.api.api_call(
                        'account.payment.register', 'create', [{}], {'context': ctx},
                    )
                    self.api.api_call(
                        'account.payment.register', 'action_create_payments',
                        [_as_list(wid)], {'context': ctx},
                    )
                except Exception:
                    pass

    def gen_crm_leads(self, count):
        self._ensure_contacts(10)
        self._ensure_salespeople()
        # Fetch CRM stages for distribution
        stage_data = self.api.search_read('crm.stage', [], ['id', 'is_won'], limit=20)
        stages = [s for s in stage_data] if stage_data else []
        vals_list = []
        for _ in range(count):
            d = random.randint(0, DAYS_BACK)
            deadline = (datetime.now() - timedelta(days=d) + timedelta(days=random.randint(14, 120))).strftime('%Y-%m-%d')
            contact = _fake_name()
            vals = {
                'name': random.choice(CRM_NAMES),
                'type': 'opportunity',
                'partner_id': random.choice(self.ids['partner']),
                'expected_revenue': round(random.uniform(5000, 150000), 2),
                'contact_name': contact,
                'email_from': _fake_email(contact),
                'phone': _fake_phone(),
                'date_deadline': deadline,
            }
            if self.ids['salesperson']:
                vals['user_id'] = random.choice(self.ids['salesperson'])
            if stages:
                stage = random.choice(stages)
                vals['stage_id'] = stage['id']
                # Set probability based on stage
                vals['probability'] = 100 if stage.get('is_won') else random.choice([10, 20, 30, 50, 70, 80, 90])
            vals_list.append(vals)
        ids = _as_list(self.api.create('crm.lead', vals_list))
        return len(ids)

    def gen_journal_entries(self, count):
        """Create misc journal entries for expenses, liabilities, and assets."""
        # Find bank/cash account for the balancing side
        bank_ids = self.api.search('account.account', [('account_type', '=', 'asset_cash')], limit=1)
        if not bank_ids:
            bank_ids = self.api.search('account.account', [('code', 'like', '1012%')], limit=1)
        if not bank_ids:
            raise Exception('No bank/cash account found for journal entries')
        bank_id = bank_ids[0]

        # Pre-cache all needed accounts in one query
        all_codes = list({t['account_code'] for t in JOURNAL_ENTRY_TEMPLATES})
        all_types = list({t['account_type'] for t in JOURNAL_ENTRY_TEMPLATES})
        accounts = self.api.search_read(
            'account.account',
            ['|', ('code', 'in', all_codes), ('account_type', 'in', all_types)],
            ['code', 'account_type'],
        )
        code_to_id = {}
        type_to_id = {}
        for a in accounts:
            code_to_id[a['code']] = a['id']
            if a['account_type'] not in type_to_id:
                type_to_id[a['account_type']] = a['id']

        def find_account(code, account_type):
            return code_to_id.get(code) or type_to_id.get(account_type)

        vals_list = []
        for _ in range(count):
            tmpl = random.choice(JOURNAL_ENTRY_TEMPLATES)
            target_id = find_account(tmpl['account_code'], tmpl['account_type'])
            if not target_id:
                continue

            amount = round(random.uniform(tmpl['min_amount'], tmpl['max_amount']), 2)
            date = _rand_date()

            if tmpl['entry_type'] == 'expense':
                lines = [
                    (0, 0, {'account_id': target_id, 'name': tmpl['description'], 'debit': amount, 'credit': 0}),
                    (0, 0, {'account_id': bank_id, 'name': tmpl['description'], 'debit': 0, 'credit': amount}),
                ]
            elif tmpl['entry_type'] == 'liability':
                lines = [
                    (0, 0, {'account_id': bank_id, 'name': tmpl['description'], 'debit': amount, 'credit': 0}),
                    (0, 0, {'account_id': target_id, 'name': tmpl['description'], 'debit': 0, 'credit': amount}),
                ]
            elif tmpl['entry_type'] == 'asset':
                lines = [
                    (0, 0, {'account_id': target_id, 'name': tmpl['description'], 'debit': amount, 'credit': 0}),
                    (0, 0, {'account_id': bank_id, 'name': tmpl['description'], 'debit': 0, 'credit': amount}),
                ]
            else:
                continue

            vals_list.append({
                'move_type': 'entry',
                'date': date,
                'ref': tmpl['description'],
                'line_ids': lines,
            })

        if not vals_list:
            return 0
        ids = _as_list(self.api.create('account.move', vals_list))
        # Post journal entries
        _logger.info("posting...")
        self.api.api_call('account.move', 'action_post', [ids])
        return len(ids)

    def gen_manufacturing_orders(self, count):
        self._ensure_boms(3)
        self._ensure_purchase_orders()
        uom = self._get_uom_unit()
        vals_list = []
        for _ in range(count):
            bom_id = random.choice(self.ids['bom'])
            product_id = self.ids['bom_product_map'].get(bom_id)
            if not product_id:
                continue
            vals_list.append({
                'product_id': product_id,
                'product_qty': random.randint(1, 20),
                'bom_id': bom_id,
                'product_uom_id': uom,
                'date_start': _rand_datetime(),
            })
        if not vals_list:
            return 0
        ids = _as_list(self.api.create('mrp.production', vals_list))
        # Confirm manufacturing orders
        _logger.info("confirming...")
        self.api.api_call('mrp.production', 'action_confirm', [ids])
        # Set qty_producing to full quantity — batch by same quantity
        _logger.info("producing...")
        mo_data = self.api.read('mrp.production', ids, ['product_qty'])
        qty_groups = {}
        for mo in mo_data:
            qty = mo['product_qty']
            qty_groups.setdefault(qty, []).append(mo['id'])
        for qty, mo_ids in qty_groups.items():
            self.api.write('mrp.production', mo_ids, {'qty_producing': qty})
        # Mark as done
        _logger.info("closing...")
        ctx = {'skip_consumption': True, 'skip_backorder': True}
        try:
            self.api.api_call('mrp.production', 'button_mark_done', [ids], {'context': ctx})
        except Exception:
            for mo_id in ids:
                try:
                    self.api.api_call('mrp.production', 'button_mark_done', [[mo_id]], {'context': ctx})
                except Exception:
                    pass
        return len(ids)

    def _gen_picking(self, count, code, src_loc, dest_loc, validate=False):
        self._ensure_contacts(10)
        self._ensure_products(10)
        if code in ('outgoing', 'internal'):
            self._ensure_purchase_orders()
        self._load_product_info()
        picking_type = self._get_picking_type(code)
        if not picking_type or not src_loc or not dest_loc:
            raise Exception(f'Could not find picking type ({code}) or locations.')
        vals_list = []
        for _ in range(count):
            moves = []
            for _ in range(random.randint(1, 3)):
                pid = random.choice(self.ids['product'])
                moves.append((0, 0, {
                    'product_id': pid,
                    'product_uom_qty': random.randint(1, 30),
                    'location_id': src_loc,
                    'location_dest_id': dest_loc,
                }))
            vals = {
                'picking_type_id': picking_type,
                'scheduled_date': _rand_datetime(),
                'move_ids': moves,
            }
            if code != 'internal':
                vals['partner_id'] = random.choice(self.ids['partner'])
            vals_list.append(vals)
        ids = _as_list(self.api.create('stock.picking', vals_list))
        if validate:
            _logger.info("validating...")
            self._validate_pickings(ids)
        return len(ids)

    def gen_deliveries(self, count):
        return self._gen_picking(count, 'outgoing', self._get_stock_location(), self._get_location('customer'), validate=True)

    def gen_receipts(self, count):
        return self._gen_picking(count, 'incoming', self._get_location('supplier'), self._get_stock_location())

    def gen_inventory(self, count):
        stock_loc = self._get_stock_location()
        all_internal = self.api.search('stock.location', [('usage', '=', 'internal')], limit=5)
        dest = [l for l in all_internal if l != stock_loc]
        dest_loc = dest[0] if dest else stock_loc
        return self._gen_picking(count, 'internal', stock_loc, dest_loc)

    def gen_timesheets(self, count):
        self._ensure_employees(5)
        self._ensure_projects(5)
        self._ensure_tasks(10)
        # Pre-fetch task→project mapping
        task_data = self.api.read('project.task', self.ids['task'], ['project_id'])
        task_project = {}
        for t in task_data:
            if t.get('project_id'):
                task_project[t['id']] = t['project_id'][0] if isinstance(t['project_id'], list) else t['project_id']

        vals_list = []
        for _ in range(count):
            task_id = random.choice(self.ids['task'])
            project_id = task_project.get(task_id, random.choice(self.ids['project']))
            vals_list.append({
                'employee_id': random.choice(self.ids['employee']),
                'project_id': project_id,
                'task_id': task_id,
                'name': random.choice(TIMESHEET_DESCRIPTIONS),
                'unit_amount': round(random.uniform(0.5, 8.0), 1),
                'date': _rand_date(),
            })
        ids = _as_list(self.api.create('account.analytic.line', vals_list))
        return len(ids)

    def gen_expenses(self, count):
        self._ensure_employees(5)
        vals_list = []
        for _ in range(count):
            item = random.choice(EXPENSE_ITEMS)
            vals_list.append({
                'name': item['name'],
                'employee_id': random.choice(self.ids['employee']),
                'total_amount': item['amount'] * round(random.uniform(0.8, 1.3), 2),
                'date': _rand_date(),
            })
        ids = _as_list(self.api.create('hr.expense', vals_list))
        return len(ids)

    def gen_vehicles(self, count):
        self._ensure_employees(5)
        items = random.choices(VEHICLE_BRANDS_MODELS, k=count)

        # Batch search/create brands
        unique_brands = list({b for b, _ in items})
        existing_brands = self.api.search_read('fleet.vehicle.model.brand', [('name', 'in', unique_brands)], ['name'])
        brand_cache = {b['name']: b['id'] for b in existing_brands}
        missing_brands = [b for b in unique_brands if b not in brand_cache]
        if missing_brands:
            new_ids = _as_list(self.api.create('fleet.vehicle.model.brand', [{'name': b} for b in missing_brands]))
            for name, bid in zip(missing_brands, new_ids):
                brand_cache[name] = bid

        # Batch search/create models
        unique_models = list({(b, m) for b, m in items})
        model_names = [m for _, m in unique_models]
        existing_models = self.api.search_read('fleet.vehicle.model', [('name', 'in', model_names)], ['name', 'brand_id'])
        model_cache = {}
        for m in existing_models:
            model_cache[f"{m['brand_id'][1]}_{m['name']}"] = m['id']
        missing_models = [(b, m) for b, m in unique_models if f'{b}_{m}' not in model_cache]
        if missing_models:
            new_ids = _as_list(self.api.create('fleet.vehicle.model', [{'name': m, 'brand_id': brand_cache[b]} for b, m in missing_models]))
            for (b, m), mid in zip(missing_models, new_ids):
                model_cache[f'{b}_{m}'] = mid

        # Get driver IDs from employees
        emp_data = self.api.read('hr.employee', self.ids['employee'], ['work_contact_id'])
        driver_ids = []
        for e in emp_data:
            wc = e.get('work_contact_id')
            if wc:
                driver_ids.append(wc[0] if isinstance(wc, list) else wc)
        if not driver_ids:
            driver_ids = self.ids['partner'][:count] or [False]

        vals_list = []
        for brand_name, model_name in items:
            vals_list.append({
                'model_id': model_cache[f'{brand_name}_{model_name}'],
                'license_plate': _fake_plate(),
                'driver_id': random.choice(driver_ids),
            })
        ids = _as_list(self.api.create('fleet.vehicle', vals_list))
        return len(ids)
