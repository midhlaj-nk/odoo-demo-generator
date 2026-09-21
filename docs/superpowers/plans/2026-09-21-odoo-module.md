# Odoo Module Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `demo_data_generator`, an Odoo 19 module with a "Demo Data" app that generates the same demo dataset the Flask app produces, into its own database.

**Architecture:** `generators.py` is ported almost verbatim behind an `EnvAPI` facade that mimics the old XML-RPC `OdooAPI` over `self.env`. An `AbstractModel` exposes `get_steps()`/`run_step(key)`; generator state between steps is persisted as JSON in `ir.config_parameter`. An OWL client action calls the steps one by one and renders the same progress ring / log UI.

**Tech Stack:** Odoo 19 (Python 3.12, ORM, OWL 2, `@web/core/orm_service`), Pillow (shipped with Odoo), no Faker.

**Spec:** `docs/superpowers/specs/2026-09-21-odoo-module-design.md`

## Global Constraints

- Target Odoo 19; product fields use `type='consu'` + `is_storable=True` (Odoo 18+ API).
- Module depends only on `base` and `web`; business modules are installed at runtime by the `modules` step.
- No `external_dependencies`. Faker is removed. Pillow is used as already present in Odoo.
- Menu, action and RPC methods restricted to `base.group_system`.
- Record counts are `DEFAULT_COUNTS` from the existing `generators.py`, unchanged.
- Test target: docker container `odoo19-odoo-1` (port 8070), addons dir bind-mounted from `~/work/migrations/migrate-odoo/odoo_modules`. Copy the module there for tests: `rsync -a --delete demo_data_generator/ ~/work/migrations/migrate-odoo/odoo_modules/demo_data_generator/`.
- Run Odoo tests with: `docker exec odoo19-odoo-1 odoo -d demogen_test -i demo_data_generator --test-enable --test-tags /demo_data_generator --stop-after-init --db_host odoo19-db-1 --db_user odoo --db_password odoo --http-port 8169`

## File Structure

```
demo_data_generator/
  __manifest__.py
  __init__.py                      from . import models
  models/__init__.py               from . import demo_generator
  models/env_api.py                class EnvAPI
  models/sample_data.py            data lists (+ FIRST_NAMES, LAST_NAMES, COMPANY_WORDS, STREETS, CITIES)
  models/generators.py             DemoGenerator with run_step / to_state / from_state
  models/demo_generator.py         AbstractModel demo.data.generator
  views/actions.xml                ir.actions.client + menu
  static/src/demo_generator.js     OWL component
  static/src/demo_generator.xml    QWeb template
  static/src/demo_generator.scss   styles (from static/style.css)
  tests/__init__.py
  tests/test_env_api.py
  tests/test_generator.py
```

---

### Task 1: Module skeleton that installs

**Files:**
- Create: `demo_data_generator/__manifest__.py`, `demo_data_generator/__init__.py`, `demo_data_generator/models/__init__.py`, `demo_data_generator/views/actions.xml`

**Produces:** client action tag `demo_data_generator`, menu `demo_data_generator.menu_root`.

- [ ] **Step 1: Write manifest**

```python
# demo_data_generator/__manifest__.py
{
    'name': 'Demo Data Generator',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Generate ~500 realistic demo records across Sales, Purchase, Inventory, MRP, Accounting, CRM, Projects, HR and eCommerce',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': ['views/actions.xml'],
    'assets': {
        'web.assets_backend': [
            'demo_data_generator/static/src/demo_generator.scss',
            'demo_data_generator/static/src/demo_generator.xml',
            'demo_data_generator/static/src/demo_generator.js',
        ],
    },
    'application': True,
    'installable': True,
}
```

- [ ] **Step 2: Package inits**

`demo_data_generator/__init__.py`: `from . import models`
`demo_data_generator/models/__init__.py`: `from . import demo_generator` (module added in Task 4; create an empty `demo_generator.py` for now so install succeeds).

- [ ] **Step 3: Action + menu**

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="action_demo_generator" model="ir.actions.client">
        <field name="name">Demo Data</field>
        <field name="tag">demo_data_generator</field>
    </record>
    <menuitem id="menu_root" name="Demo Data" sequence="200"
              action="action_demo_generator" groups="base.group_system"
              web_icon="demo_data_generator,static/description/icon.png"/>
</odoo>
```

Add a placeholder `static/description/icon.png` (generate with Pillow: 128x128 solid `#714B67` square with white "DD").

- [ ] **Step 4: Install on fresh DB, verify**

```bash
rsync -a --delete demo_data_generator/ ~/work/migrations/migrate-odoo/odoo_modules/demo_data_generator/
docker exec odoo19-odoo-1 odoo -d demogen_test -i demo_data_generator --stop-after-init --db_host odoo19-db-1 --db_user odoo --db_password odoo --http-port 8169 2>&1 | grep -E "ERROR|CRITICAL|Modules loaded" 
```
Expected: `Modules loaded.` and no ERROR lines.

- [ ] **Step 5: Commit** `feat: scaffold demo_data_generator Odoo module`

---

### Task 2: EnvAPI facade

**Files:**
- Create: `demo_data_generator/models/env_api.py`, `demo_data_generator/tests/__init__.py`, `demo_data_generator/tests/test_env_api.py`

**Produces:** `EnvAPI(env)` with `create(model, vals) -> int|list[int]`, `search(model, domain, limit=0, context=None) -> list[int]`, `search_read(model, domain, fields, limit=0, context=None) -> list[dict]`, `read(model, ids, fields) -> list[dict]`, `write(model, ids, vals) -> True`, `api_call(model, method, args, kwargs=None)`.

- [ ] **Step 1: Failing test**

```python
# tests/test_env_api.py
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
        self.assertEqual(self.api.search('res.partner', [('id', '=', pid)], context={'active_test': False}), [pid])

    def test_api_call_on_records(self):
        pid = self.api.create('res.partner', {'name': 'Call', 'active': True})
        self.api.api_call('res.partner', 'write', [[pid], {'name': 'Called'}])
        self.assertEqual(self.env['res.partner'].browse(pid).name, 'Called')

    def test_api_call_model_create_with_context(self):
        rid = self.api.api_call('res.partner', 'create', [{'name': 'Ctx'}], {'context': {'lang': 'en_US'}})
        self.assertIsInstance(rid, int)
```

- [ ] **Step 2: Run, expect ImportError** (use Global Constraints test command, tag `test_env_api`).

- [ ] **Step 3: Implement**

```python
# models/env_api.py
from odoo import models as odoo_models


def _ctx(model, context):
    return model.with_context(**context) if context else model


class EnvAPI:
    """Mimics the XML-RPC OdooAPI wrapper used by the original Flask app,
    backed by an ORM environment so generators.py ports unchanged."""

    def __init__(self, env):
        self.env = env

    def create(self, model, vals):
        rec = self.env[model].create(vals)
        return rec.ids if isinstance(vals, list) else rec.id

    def search(self, model, domain, limit=0, context=None):
        return _ctx(self.env[model], context).search(domain, limit=limit or None).ids

    def search_read(self, model, domain, fields, limit=0, context=None):
        return _ctx(self.env[model], context).search_read(domain, fields, limit=limit or None)

    def read(self, model, ids, fields):
        return self.env[model].browse(ids).read(fields)

    def write(self, model, ids, vals):
        return self.env[model].browse(ids).write(vals)

    def api_call(self, model, method, args, kwargs=None):
        kwargs = dict(kwargs or {})
        target = _ctx(self.env[model], kwargs.pop('context', None))
        args = list(args)
        if args and isinstance(args[0], list) and all(isinstance(i, int) for i in args[0]):
            target = target.browse(args.pop(0))
        result = getattr(target, method)(*args, **kwargs)
        if isinstance(result, odoo_models.BaseModel):
            if method == 'create' and args and isinstance(args[0], dict):
                return result.id
            return result.ids
        return result
```

- [ ] **Step 4: Run tests, expect 6 passed.**
- [ ] **Step 5: Commit** `feat: EnvAPI ORM facade mirroring OdooAPI`

---

### Task 3: Port generators.py and sample_data.py

**Files:**
- Create: `demo_data_generator/models/sample_data.py` (copy of `sample_data.py` + new lists), `demo_data_generator/models/generators.py` (copy of `generators.py` + edits below), `demo_data_generator/tests/test_generator.py`

**Consumes:** `EnvAPI` from Task 2.
**Produces:** `DemoGenerator(api)` with `STEP_KEYS: list[str]`, `STEP_LABELS: dict`, `run_step(key) -> (count:int, detail:str)`, `to_state() -> dict`, `from_state(dict)`.

- [ ] **Step 1: Failing test**

```python
# tests/test_generator.py
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
        self.assertEqual(self.env['res.partner'].search_count([]) - before, 35)
        state = gen.to_state()
        self.assertEqual(len(state['ids']['partner']), 35)
        gen2 = DemoGenerator(EnvAPI(self.env))
        gen2.from_state(state)
        self.assertEqual(gen2.ids['partner'], gen.ids['partner'])

    def test_state_roundtrip_keeps_int_keys(self):
        gen = DemoGenerator(EnvAPI(self.env))
        gen.ids['bom_product_map'] = {7: 9}
        gen._po_done = True
        import json
        gen2 = DemoGenerator(EnvAPI(self.env))
        gen2.from_state(json.loads(json.dumps(gen.to_state())))
        self.assertEqual(gen2.ids['bom_product_map'], {7: 9})
        self.assertTrue(gen2._po_done)
```

- [ ] **Step 2: Copy sample_data.py, append name lists**

```python
FIRST_NAMES = ['James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda',
               'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
               'Thomas', 'Sarah', 'Daniel', 'Karen', 'Aisha', 'Omar', 'Priya', 'Wei', 'Sofia',
               'Luca', 'Fatima', 'Hiroshi', 'Elena', 'Carlos']
LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
              'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
              'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Khan', 'Patel', 'Nguyen', 'Kim',
              'Rossi', 'Silva', 'Novak', 'Tanaka', 'Ivanov', 'Okafor']
COMPANY_WORDS = ['Apex', 'Nova', 'Summit', 'Horizon', 'Vertex', 'Pioneer', 'Quantum', 'Atlas',
                 'Beacon', 'Cascade', 'Zenith', 'Harbor', 'Orion', 'Sterling', 'Meridian']
COMPANY_SUFFIXES = ['Ltd', 'Inc', 'LLC', 'Group', 'Industries', 'Solutions', 'Technologies',
                    'Logistics', 'Partners', 'Holdings']
STREET_NAMES = ['Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Park Blvd', 'Lake Rd', 'Hill St',
                'River Rd', 'Elm St', 'Pine Ave', 'Washington Ave', 'Sunset Blvd']
CITIES = ['Springfield', 'Riverside', 'Fairview', 'Madison', 'Georgetown', 'Clinton', 'Franklin',
          'Greenville', 'Bristol', 'Salem', 'Dover', 'Newport', 'Ashland', 'Burlington']
```

- [ ] **Step 3: Copy generators.py and apply these edits**

1. Replace imports: drop `from faker import Faker` and `fake = Faker()`; add `import logging`, `import string`, `_logger = logging.getLogger(__name__)`; change `from sample_data import (...)` to `from .sample_data import (...)` and add the six new list names to the import.
2. Add helpers after `_as_list`:

```python
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
    return ''.join(random.choices(string.ascii_uppercase, k=3)) + '-' + ''.join(random.choices(string.digits, k=4))
```

3. Replace each `fake.*` call: in `gen_contacts` compute `name = fake.company() if is_company else fake.name()` first, then `'email': _fake_company_email(name) if is_company else _fake_email(name)`, `_fake_phone()`, `_fake_street()`, `_fake_city()`, `_fake_zip()`. In `gen_employees`: `name = _fake_name()`, `'work_email': _fake_email(name)`. In `gen_crm_leads`: `contact = _fake_name()`, `'contact_name': contact`, `'email_from': _fake_email(contact)`, `'phone': _fake_phone()`. In `gen_vehicles`: `'license_plate': _fake_plate()`.
4. Replace every `print(...)` with `_logger.info(...)` (drop `end=' ', flush=True` kwargs).
5. Delete the `generate(self, selections)` method. Add in its place:

```python
    STEP_KEYS = ['modules', 'configure'] + GENERATION_ORDER + ['mto_showcase', 'publish_website']

    STEP_LABELS = {
        'modules': 'Installing modules', 'configure': 'Configuring settings',
        'contacts': 'Contacts', 'products': 'Products', 'employees': 'Employees',
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
```

`STEP_KEYS` must be defined after `GENERATION_ORDER` inside the class body (`GENERATION_ORDER` is a class attribute, so reference it directly in the class body as `GENERATION_ORDER`).

6. In `__init__`, set `self._selections = dict(DEFAULT_COUNTS)` instead of `{}`.

- [ ] **Step 4: Run tests, expect 3 passed** (tag `test_generator`).
- [ ] **Step 5: Commit** `feat: port DemoGenerator to ORM, step-based, no Faker`

---

### Task 4: `demo.data.generator` AbstractModel with persisted state

**Files:**
- Modify: `demo_data_generator/models/demo_generator.py`
- Modify: `demo_data_generator/tests/test_generator.py` (append tests)

**Consumes:** `DemoGenerator`, `EnvAPI`.
**Produces:** RPC methods `get_steps() -> list[{key,label}]`, `run_step(key) -> {status, detail, count}`.

- [ ] **Step 1: Failing tests (append to test_generator.py)**

```python
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

    def test_non_admin_denied(self):
        user = self.env['res.users'].create({'name': 'u', 'login': 'u_demo', 'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            self.env['demo.data.generator'].with_user(user).get_steps()
```
Add `from odoo.exceptions import AccessError` at top of the file.

- [ ] **Step 2: Run, expect KeyError on model name.**

- [ ] **Step 3: Implement**

```python
# models/demo_generator.py
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
            count, detail = gen.run_step(key)
        except Exception as e:  # noqa: BLE001 - one failing step must not abort the run
            _logger.exception('Demo data step %s failed', key)
            return {'status': 'error', 'detail': str(e)[:200], 'count': 0}
        if key != 'modules':
            self._save_state(gen.to_state())
        return {'status': 'done', 'detail': detail, 'count': count}
```

- [ ] **Step 4: Run tests, expect all in test_generator passing.**
- [ ] **Step 5: Commit** `feat: demo.data.generator RPC model with persisted step state`

---

### Task 5: OWL client action

**Files:**
- Create: `demo_data_generator/static/src/demo_generator.js`, `demo_generator.xml`, `demo_generator.scss`

**Consumes:** `get_steps`, `run_step` from Task 4.

- [ ] **Step 1: JS component**

```js
/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const CIRCUMFERENCE = 2 * Math.PI * 52;

export class DemoGeneratorAction extends Component {
    static template = "demo_data_generator.Action";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            phase: "idle",        // idle | running | complete
            steps: [],
            done: 0,
            errors: 0,
            records: 0,
            current: "",
            working: false,
            log: [],              // newest first: {key, label, detail, ok}
            fatal: "",
        });
    }

    get pct() {
        const total = this.state.steps.length || 1;
        return Math.round((this.state.done / total) * 100);
    }
    get ringOffset() {
        return CIRCUMFERENCE - (this.pct / 100) * CIRCUMFERENCE;
    }
    get circumference() {
        return CIRCUMFERENCE;
    }
    get summary() {
        const s = this.state;
        return s.errors
            ? `Done - ${s.records} records created, ${s.errors} error(s)`
            : `Done - ${s.records} records created`;
    }

    reset() {
        Object.assign(this.state, {
            phase: "idle", steps: [], done: 0, errors: 0, records: 0,
            current: "", working: false, log: [], fatal: "",
        });
    }

    async generate() {
        this.reset();
        this.state.phase = "running";
        this.state.current = "Connecting...";
        try {
            this.state.steps = await this.orm.call("demo.data.generator", "get_steps");
            for (const step of this.state.steps) {
                this.state.current = step.label;
                this.state.working = true;
                const res = await this.orm.call("demo.data.generator", "run_step", [step.key]);
                this.state.working = false;
                this.state.done++;
                const ok = res.status === "done";
                if (!ok) this.state.errors++;
                if (ok && !["modules", "publish_website"].includes(step.key)) {
                    this.state.records += res.count || 0;
                }
                this.state.log.unshift({ key: step.key, label: step.label, detail: res.detail || "", ok });
            }
            this.state.phase = "complete";
            this.state.current = this.summary;
        } catch (e) {
            this.state.working = false;
            this.state.fatal = `Connection failed: ${e.message || e}`;
            this.state.phase = "complete";
        }
    }
}

registry.category("actions").add("demo_data_generator", DemoGeneratorAction);
```

- [ ] **Step 2: QWeb template** — port `templates/index.html` body into `<t t-name="demo_data_generator.Action">`: wrap in `<div class="o_demo_generator"><div class="container">`, keep the `<h1>`, subtitle, the full `<details class="info-panel">` block verbatim, then:

```xml
<div t-if="state.phase === 'idle'" class="setup">
    <button class="btn btn-generate" t-on-click="generate">Generate Demo Data</button>
</div>
<div t-else="" class="progress-panel show">
    <div class="progress-hero">
        <div class="progress-ring-wrap">
            <svg t-attf-class="progress-ring {{ state.working ? 'working' : '' }}" viewBox="0 0 120 120">
                <circle class="progress-ring-bg" cx="60" cy="60" r="52"/>
                <circle class="progress-ring-spinner" cx="60" cy="60" r="52"/>
                <circle class="progress-ring-fill" cx="60" cy="60" r="52"
                        t-attf-style="stroke-dasharray: {{ circumference }}; stroke-dashoffset: {{ state.phase === 'complete' and !state.fatal ? 0 : ringOffset }}"/>
            </svg>
            <div class="progress-ring-label"><t t-esc="state.phase === 'complete' and !state.fatal ? 100 : pct"/>%</div>
        </div>
        <div class="progress-info">
            <div t-attf-class="progress-current {{ state.working ? 'working' : '' }} {{ state.phase === 'complete' ? (state.errors or state.fatal ? 'has-errors' : 'complete') : '' }}">
                <t t-esc="state.fatal || state.current"/>
            </div>
            <div class="progress-counter"><t t-esc="state.done"/> of <t t-esc="state.steps.length"/> steps</div>
        </div>
    </div>
    <button t-if="state.phase === 'complete'" class="btn btn-generate btn-again" t-on-click="reset">Run Again</button>
    <div class="progress-log">
        <t t-foreach="state.log" t-as="entry" t-key="entry_index">
            <div t-attf-class="log-entry {{ entry.ok ? 'done' : 'error' }}">
                <span t-attf-class="{{ entry.ok ? 'log-check' : 'log-x' }}"/>
                <span t-esc="entry.label"/>
                <span t-attf-class="log-detail {{ entry.ok ? '' : 'err' }}" t-esc="entry.detail"/>
            </div>
        </t>
    </div>
</div>
```

- [ ] **Step 3: SCSS** — copy `static/style.css` into `demo_generator.scss`, wrap all rules in `.o_demo_generator { ... }`, remove `body`/`html` rules (turn `body` background into `.o_demo_generator` background + `min-height: 100%; overflow: auto`), keep the `stroke-dasharray` on `.progress-ring-fill` consistent with `CIRCUMFERENCE` (2π·52 ≈ 326.73).

- [ ] **Step 4: Install/upgrade on container, open http://localhost:8070 (db demogen_test), log in admin/admin, open "Demo Data" menu.** Expected: page renders, info panel expands, button visible, no console errors.

- [ ] **Step 5: Commit** `feat: OWL client action for demo data generation`

---

### Task 6: End-to-end run on a fresh database

- [ ] **Step 1:** Create fresh DB `demogen_e2e` (via `odoo -d demogen_e2e -i demo_data_generator --stop-after-init ...`, then set admin password if needed).
- [ ] **Step 2:** Open Demo Data, click Generate, wait for completion. Use browser tooling to screenshot the final state.
- [ ] **Step 3:** Verify counts via `docker exec odoo19-odoo-1 odoo shell -d demogen_e2e ...` or psql:

```sql
select 'partner', count(*) from res_partner where customer_rank>0 or supplier_rank>0
union all select 'so', count(*) from sale_order
union all select 'po', count(*) from purchase_order
union all select 'inv', count(*) from account_move where move_type='out_invoice' and payment_state='paid'
union all select 'mo', count(*) from mrp_production where state='done'
union all select 'lead', count(*) from crm_lead
union all select 'task', count(*) from project_task
union all select 'ts', count(*) from account_analytic_line where project_id is not null
union all select 'veh', count(*) from fleet_vehicle
union all select 'pub_tmpl', count(*) from product_template where website_published;
```
Expected: matches info panel numbers (≥ 35 partners, 35 SO, ≥ 30 PO, 35 paid invoices, 15 done MOs, 35 leads, 35 tasks, 40 timesheets, 12 vehicles, ≥ 30 published templates). Any step reporting `error` in the log → fix in `generators.py`, re-run.
- [ ] **Step 4:** Click Run Again → Generate a second time. Expected: `modules` and `configure` steps report done, no crash.
- [ ] **Step 5: Commit fixes** if any.

---

### Task 7: Retire Flask app

**Files:**
- Delete: `app.py`, `odoo_api.py`, `generators.py`, `sample_data.py`, `templates/`, `static/`, `requirements.txt`
- Modify: `.gitignore` (drop `venv/` only if venv removed; keep), `README.md` (create)

- [ ] **Step 1:** `git rm` the Flask files listed above.
- [ ] **Step 2:** Write `README.md`: what the module does (reuse info panel text), install instructions (copy `demo_data_generator/` into addons path, update apps list, install "Demo Data Generator", open Demo Data menu, click Generate), note admin-only, note it installs business modules.
- [ ] **Step 3: Commit** `chore: remove Flask app, module is the product`

## Self-review notes

- Spec coverage: EnvAPI (T2), DemoGenerator port/state (T3), AbstractModel + access (T4), OWL UI (T5), manual + automated tests (T3/T4/T6), Flask removal (T7). Menu/action/group (T1).
- Spec said state is rebuilt via `_ensure_*` lookups; plan persists state in `ir.config_parameter` instead (decided while planning: keeps original behaviour exactly, e.g. publishing only generated templates). Spec updated to match in Task 7 commit? No — update spec now, in the same commit as this plan.
