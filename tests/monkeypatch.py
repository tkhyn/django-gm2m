
def patch_interactive_mig_questionner():
    """
    Prevents user input when invoking makemigrations
    Indeed, using interactive=False does not prevent Django from asking
    confirmation to rename a field or model
    """

    from django.db.migrations.questioner import InteractiveMigrationQuestioner

    def true(*args, **kwargs):
        return True

    InteractiveMigrationQuestioner.ask_rename = true
    InteractiveMigrationQuestioner.ask_rename_model = true
