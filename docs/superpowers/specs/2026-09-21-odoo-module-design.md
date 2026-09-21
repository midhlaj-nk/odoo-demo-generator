# Demo Data Generator as an Odoo Module — Design

Date: 2026-09-21

## Goal

Replace the standalone Flask app (`app.py`, `odoo_api.py`, `generators.py`,
`sample_data.py`, `templates/index.html`) with an installable Odoo 19 module,
`demo_data_generator`, that produces the same demo data set in the database it
is installed on. No external connection form; no external Python dependencies.

## Non-goals

- Configurable record counts (defaults from `DEFAULT_COUNTS` are used).
- Pushing data to a remote Odoo instance.
- Background jobs / cron / queue.
- Multi-company handling beyond the current user's company.

## Architecture

```
demo_data_generator/
  __manifest__.py            depends: base, web
  models/
    __init__.py
    env_api.py               EnvAPI: OdooAPI-compatible facade over self.env
    sample_data.py           copied verbatim
    generators.py            ported DemoGenerator (no Faker, no print, step-based)
    demo_generator.py        AbstractModel demo.data.generator (RPC surface)
  security/
    ir.model.access.csv      (none needed for AbstractModel; file omitted)
  static/src/
    demo_generator.js        OWL client action
    demo_generator.xml       QWeb template
    demo_generator.scss      adapted from static/style.css
  views/
    actions.xml              ir.actions.client + top-level menu, group_system
```

### Server side

**`EnvAPI`** exposes the six methods `generators.py` already uses:
`create`, `search`, `search_read`, `read`, `write`, `api_call`. Each maps to
the ORM on `self.env`. `api_call(model, method, args, kwargs)` calls
`env[model].with_context(**kwargs.get('context', {})).browse(args[0]).<method>(*args[1:])`
when `args[0]` is a list of ints, otherwise `env[model].<method>(*args)`. This
lets `generators.py` port with minimal edits.

**`DemoGenerator`** (plain Python class, in `generators.py`) keeps the existing
`gen_*`, `_ensure_*`, `_configure_settings`, `_create_mto_showcase`,
`_publish_products`, `_install_modules` methods. Changes:

- Remove `Faker`; replace the nine `fake.*` calls with local helpers drawing
  from small name/company/street/city lists in `sample_data.py`.
- Replace `print` with `_logger.info`.
- Replace the streaming `generate()` generator with `steps()` (ordered list of
  step keys) and `run_step(key)` returning `(detail_str, count)`.
- Per-request state: every step must work with a fresh `DemoGenerator`
  instance. `self.ids[...]` caches are rebuilt lazily through the existing
  `_ensure_*` helpers, which already `search` when the cache is empty. Where a
  step assumed an earlier step populated `self.ids` directly, switch it to the
  matching `_ensure_*` call.

**`demo.data.generator`** (`AbstractModel`) exposes two `@api.model` methods
for RPC, both restricted to `base.group_system` via `has_group` check:

- `get_steps()` → `[{key, label}, ...]` in execution order:
  `modules`, `configure`, then `GENERATION_ORDER`, then `mto_showcase`,
  `publish_website`.
- `run_step(key)` → `{status: 'done'|'error', detail: str, count: int}`.
  Exceptions are caught and returned as `error` with the message truncated to
  200 chars, so one failing step never aborts the run. Each call is its own
  transaction, so `button_immediate_install` (which commits and reloads the
  registry) is isolated in the `modules` step.

### Client side

OWL client action `demo_data_generator.action`, tag `demo_data_generator`.
Layout mirrors `templates/index.html` minus the connection form:

- Info panel (`<details>`) listing what gets generated (static text).
- "Generate Demo Data" button.
- Progress panel: SVG ring, percentage, current step label, `n of N steps`,
  reverse-chronological log with done/error rows.
- On completion: "Done - X records created[, Y error(s)]" and a "Run Again"
  button that resets to the form state.

Flow: `steps = await orm.call('demo.data.generator', 'get_steps')`, then
`for step of steps: result = await orm.call(..., 'run_step', [step.key])`,
updating state after each. Total = `steps.length`. Records total =
sum of `count` for steps whose key is not `modules` or `publish_website`
(matches current `_complete` maths).

### Access

Menu and action visible only to `base.group_system`. Server methods raise
`AccessError` for anyone else.

### Error handling

- Step errors: returned, logged, shown in the log row, run continues.
- RPC transport failure: JS catches, shows "Connection failed: ..." in the
  current-step label, stops the loop.

### Testing

Manual on the local `odoo19-odoo-1` container (addons path
`~/work/migrations/migrate-odoo/odoo_modules`): fresh DB, install module, open
Demo Data menu, run, confirm all steps done with no errors and the record
counts match the info panel. Rerun once to confirm idempotence of the
`modules`/`configure` steps.

Automated: one `TransactionCase` test that `get_steps()` returns the expected
keys in order and that `run_step('contacts')` creates partners. Heavy steps
are not unit-tested (they install modules).

## Repo layout after the change

The module lives at `demo_data_generator/` in this repo. The Flask files stay
until the module is verified, then are removed in a follow-up commit.
