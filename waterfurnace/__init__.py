"""Top-level package for waterfurnace."""

import importlib.metadata

__author__ = """Sean Dague"""
__email__ = "sean@dague.net"

try:
    __version__ = importlib.metadata.version("waterfurnace")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
