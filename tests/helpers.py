import re
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


class reset_warning_registry(object):
    """
    context manager which archives & clears warning registry for duration of
    context
    http://bugs.python.org/issue21724
    http://bugs.python.org/file40031/reset_warning_registry.py

    :param pattern:
          optional regex pattern, causes manager to only reset modules whose names
          match this pattern. defaults to ``".*"``.
    """

    #: regexp for filtering which modules are reset
    _pattern = None

    #: dict mapping module name -> old registry contents
    _backup = None

    def __init__(self, pattern=None):
        self._pattern = re.compile(pattern or ".*")

    def __enter__(self):
        # archive and clear the __warningregistry__ key for all modules
        # that match the 'reset' pattern.
        pattern = self._pattern
        backup = self._backup = {}
        for name, mod in list(sys.modules.items()):
            if pattern.match(name):
                reg = getattr(mod, "__warningregistry__", None)
                if reg:
                    backup[name] = reg.copy()
                    reg.clear()
        return self

    def __exit__(self, *exc_info):
        # restore warning registry from backup
        modules = sys.modules
        backup = self._backup
        for name, content in backup.items():
            mod = modules.get(name)
            if mod is None:
                continue
            reg = getattr(mod, "__warningregistry__", None)
            if reg is None:
                setattr(mod, "__warningregistry__", content)
            else:
                reg.clear()
                reg.update(content)

        # clear all registry entries that we didn't archive
        pattern = self._pattern
        for name, mod in list(modules.items()):
            if pattern.match(name) and name not in backup:
                reg = getattr(mod, "__warningregistry__", None)
                if reg:
                    reg.clear()
