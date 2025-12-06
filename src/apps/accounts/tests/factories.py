"""
Backward compatibility wrapper for tests.
Factories have been moved to src.apps.accounts.factories for production use.
"""

from src.apps.accounts.factories import *  # noqa: F401, F403
