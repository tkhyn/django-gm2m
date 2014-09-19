import sys

from django.db.models.loading import cache


__test__ = False


def del_app_models(app, app_module=False):
    """
    Unloads an app and its models module, as well as the app module
    (optionally)
    """
    to_del = [app + '.models']
    if app_module:
        to_del.append(app)
    for m in to_del:
        try:
            del sys.modules[m]
        except KeyError:
            pass
    try:
        del(cache.app_models[app.split('.')[-1]])
    except KeyError:
        pass

