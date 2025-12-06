"""
Backward compatibility wrapper for tests.
Factories have been moved to src.apps.health.factories for production use.
"""

from src.apps.health.factories import *  # noqa: F401, F403
