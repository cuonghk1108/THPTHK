import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from core.cache_utils import invalidate_all_caches

logger = logging.getLogger(__name__)


def _clear_cache_handler(sender, **kwargs):
    """Signal handler to clear application read caches on data modification."""
    invalidate_all_caches()


def register_cache_invalidation_signals():
    """Register post_save and post_delete signals for critical models."""
    from conduct.models import ViolationRecord, RedStarReport, StudentFeedback
    from competition.models import (
        CompetitionPeriod,
        ClassCompetitionScore,
        ScoreAdjustment,
        ScoreCriterion,
    )
    from core.models import User, AcademicYear, Semester

    models_to_watch = [
        ViolationRecord,
        RedStarReport,
        StudentFeedback,
        CompetitionPeriod,
        ClassCompetitionScore,
        ScoreAdjustment,
        ScoreCriterion,
        User,
        AcademicYear,
        Semester,
    ]

    for model_cls in models_to_watch:
        post_save.connect(_clear_cache_handler, sender=model_cls, weak=False)
        post_delete.connect(_clear_cache_handler, sender=model_cls, weak=False)

    logger.debug("Automatic cache invalidation signals registered for models.")
