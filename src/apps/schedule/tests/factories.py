"""
Backward compatibility wrapper for tests.
Factories have been moved to src.apps.schedule.factories for production use.
"""

from src.apps.schedule.factories import *  # noqa: F401, F403
