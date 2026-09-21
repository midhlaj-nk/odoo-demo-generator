from odoo import models as odoo_models


def _ctx(model, context):
    return model.with_context(**context) if context else model


class EnvAPI:
    """Mimics the XML-RPC ``OdooAPI`` wrapper used by the original Flask app,
    backed by an ORM environment so ``generators.py`` ports unchanged."""

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
