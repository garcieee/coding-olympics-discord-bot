"""
Core package for the Coding Olympics Discord Bot.

This package contains the core functionality for the bot,
including leaderboard management, member compilation,
and ticketing features.
"""

# Import core modules to make them available when importing the package
from .leaderboard import *
from .compile_members import *
from .ticketing import *

__version__ = "1.0.0"