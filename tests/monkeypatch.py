
def patch_interactive_mig_questionner():
    """
    Prevents user input when invoking makemigrations, without requiring
    --noinput (which is not available before Django 1.9 anyway)
    """

    from django.db.migrations.questioner import InteractiveMigrationQuestioner

    def true(*args, **kwargs):
        return True

    InteractiveMigrationQuestioner.ask_rename = true
    InteractiveMigrationQuestioner.ask_rename_model = true
