import sys
import os

from .helpers import del_app_models


def setUp():

    ldir = os.path.dirname(__file__)
    apps_list = ['tests'] + ['tests.' + d for d in os.listdir(ldir)
                 if os.path.isdir(os.path.join(ldir, d))]

    for app in apps_list:
        del_app_models(app, app_module=True)
