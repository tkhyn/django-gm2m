"""
Preventing user input when invoking makemigrations, without requiring
--noinput (which will not be available with makemigrations until Django 1.9
anyway)
"""

try:
    # for django 1.7+ only
    from django.db.migrations.questioner import InteractiveMigrationQuestioner

    class GM2MInteractiveMigrationQuestioner(InteractiveMigrationQuestioner):

        def ask_rename(self, model_name, old_name, new_name, field_instance):
            return True

        def ask_rename_model(self, old_model_state, new_model_state):
            return True

    from django.core.management.commands import makemigrations
    makemigrations.InteractiveMigrationQuestioner = \
        GM2MInteractiveMigrationQuestioner
except ImportError:
    pass

