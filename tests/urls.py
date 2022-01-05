from .compat import re_path


urlpatterns = [
    re_path('^$', lambda: None)
]
