from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        try:
            from core.signals import register_cache_invalidation_signals
            register_cache_invalidation_signals()
        except Exception:
            pass
