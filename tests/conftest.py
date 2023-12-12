import os

from .helpers import del_app_models

from .monkeypatch import patch_interactive_mig_questionner


def pytest_sessionstart():
    """
    Unloads apps after pytest tests lookup
    """

    patch_interactive_mig_questionner()

    ldir = os.path.dirname(__file__)
    apps_list = [d for d in os.listdir(ldir)
                 if os.path.isdir(os.path.join(ldir, d))]

    for app in apps_list:
        del_app_models(app, app_module=True)
