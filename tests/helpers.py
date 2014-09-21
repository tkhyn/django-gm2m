import sys

from django.db.models.loading import cache

__test__ = False


def app_mod_path(m):
    return 'tests.' + m


def del_app_models(app, app_module=False):
    """
    Unloads an app and its models module, as well as the app module
    (optionally)
    """
    try:
        try:  # Django >= 1.7
            del cache.all_models[app]
        except AttributeError:
            del(cache.app_models[app])
    except KeyError:
        pass

    path = app_mod_path(app)

    to_del = [path + '.models']
    if app_module:
        to_del.append(path)

    for m in to_del:
        try:
            del sys.modules[m]
        except KeyError:
            pass
