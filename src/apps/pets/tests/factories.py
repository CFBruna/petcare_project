"""
Backward compatibility wrapper for tests.
Factories have been moved to src.apps.pets.factories for production use.
"""

from src.apps.pets.factories import *  # noqa: F401, F403
