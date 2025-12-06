"""
Backward compatibility wrapper for tests.
Factories have been moved to src.apps.store.factories for production use.
"""

from src.apps.store.factories import *  # noqa: F401, F403
