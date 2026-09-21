# Demo Data Generator (Odoo 19 module)

An installable Odoo app that fills the database it runs in with realistic
demo data: contacts, products with images, employees, confirmed and delivered
sales orders, received purchase orders, paid invoices, completed manufacturing
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
3. Generate ~500 records in dependency order (contacts → employees → products →
   work centers → BOMs → operations → projects → tasks → purchase orders →
   sales orders → invoices → journal entries → CRM leads → manufacturing
   orders → deliveries → receipts → internal transfers → timesheets →
   expenses → vehicles).
4. Create the "Smart Display Pro" MTO showcase (finished good + 3 raw
   materials with vendor pricing and a BOM).
5. Publish all product templates on the website.

Running it again adds another full batch on top of the existing data.

## Development

Module layout:

- `models/generators.py` — the data generator (ported from the original
  Flask tool; talks to the ORM through `models/env_api.py`).
- `models/demo_generator.py` — `demo.data.generator` abstract model exposing
  `get_steps()` and `run_step(key)` over RPC and persisting step state in
  `ir.config_parameter`.
- `static/src/` — OWL client action with the progress UI.
- `tests/` — Odoo unit tests.

Run tests:

```bash
odoo -d <db> -i demo_data_generator --test-enable --test-tags /demo_data_generator --stop-after-init
```
