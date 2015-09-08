import sys

from django.apps.registry import apps

__test__ = False


def app_mod_path(m):
    return 'tests.' + m


def del_app_models(app, app_module=False):
    """
    Unloads an app and its models module, as well as the app module
    (optionally)
    """

    try:
        del apps.all_models[app]
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
