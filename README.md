# Demo Data Generator (Odoo 19 module)

An installable Odoo app that fills the database it runs in with realistic
demo data: contacts, products with images, employees, five salesperson users,
confirmed and delivered sales orders spread across those salespeople, received purchase orders, paid invoices, completed manufacturing
orders, CRM opportunities, projects, tasks, timesheets, expenses, vehicles and
posted journal entries. It also installs the business modules it needs,
enables the MTO route, automatic invoicing and the Demo payment provider, and
publishes every product on the eCommerce storefront.

## Install

1. Copy `demo_data_generator/` into an addons path of your Odoo 19 instance.
2. Restart Odoo, then **Apps → Update Apps List**.
3. Install **Demo Data Generator**.
4. Open the **Demo Data** app from the home menu and click **Generate Demo Data**.

Only users in the *Administration / Settings* group can see the app or run it.

## What happens when you click Generate

Each step is a separate request, so the page shows live progress and one
failing step does not stop the others:

1. Install modules: accountant/account, website, website_sale, payment_demo,
   sale_management, stock, mrp, purchase, hr, project, hr_timesheet,
   hr_expense, fleet, crm.
2. Configure settings: MTO route, automatic invoice, Demo payment provider.
3. Generate ~500 records in dependency order (contacts → employees → salespeople → products →
   work centers → BOMs → operations → projects → tasks → purchase orders →
   sales orders → invoices → journal entries → CRM leads → manufacturing
   orders → deliveries → receipts → internal transfers → timesheets →
   expenses → vehicles).
4. Create the "Smart Display Pro" MTO showcase (finished good + 3 raw
   materials with vendor pricing and a BOM).
5. Publish all product templates on the website.

Running it again adds another full batch on top of the existing data.

## Daily scheduled generation

A scheduled action **Demo Data: daily generation** runs once a day and adds a
fresh slice of data (all steps except module installation) so the database
looks alive. By default it creates **25%** of the full batch (~115 records a
day). Change it under **Settings → Demo Data → Daily Volume**; 100 = the full
~465 records every day. The scheduled run skips the MTO showcase product once
it exists, and logs a failed run with an explanation if Generate was never
clicked (modules not installed).

## History

**Demo Data → History** lists every run, manual or scheduled: start time,
duration, volume, records created, errors and state. Open a run to see one
line per step with its status, count, detail and duration.

## Development

Module layout:

- `models/generators.py` — the data generator (ported from the original
  Flask tool; talks to the ORM through `models/env_api.py`).
- `models/demo_generator.py` — `demo.data.generator` abstract model exposing
  `get_steps()`, `start_run()`, `run_step(key, run_id)` and `finish_run()`
  over RPC, persisting step state in `ir.config_parameter`, plus the
  `_cron_generate()` entry point of the daily scheduled action.
- `models/demo_run.py` — `demo.data.run` / `demo.data.run.line` history.
- `models/res_config_settings.py` — the Daily Volume setting.
- `static/src/` — OWL client action with the progress UI.
- `tests/` — Odoo unit tests.

Run tests:

```bash
odoo -d <db> -i demo_data_generator --test-enable --test-tags /demo_data_generator --stop-after-init
```
