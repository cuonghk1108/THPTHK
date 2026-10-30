import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_VERSION_KEY = 'hk_hub_data_cache_version'


def get_cache_version() -> int:
    """Return the current global data cache version integer."""
    try:
        version = cache.get(CACHE_VERSION_KEY)
        if version is None:
            cache.set(CACHE_VERSION_KEY, 1, timeout=86400 * 30)
            return 1
        return int(version)
    except Exception as e:
        logger.warning(f"Error getting cache version: {e}")
        return 1


def invalidate_all_caches():
    """
    Invalidate all application read caches (stats, competition dashboard, 
    period status, scores, filters_meta) immediately upon any data mutation.
    """
    try:
        try:
            cache.incr(CACHE_VERSION_KEY)
        except Exception:
            cache.set(CACHE_VERSION_KEY, get_cache_version() + 1, timeout=86400 * 30)
        cache.clear()
        logger.debug("Application cache successfully invalidated.")
    except Exception as e:
        logger.warning(f"Error invalidating cache: {e}")
