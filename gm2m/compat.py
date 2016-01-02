import django


if django.VERSION >= (1, 9):
    def resolve_related_class(rel, model, cls):
        rel.model = model
        rel.do_related_class()
else:
    def resolve_related_class(rel, model, cls):
        rel.to = model
        rel.do_related_class()
