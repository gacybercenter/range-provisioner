"""
Range Provisioner Package
"""
import os
import sys

_src_dir = os.path.dirname(os.path.abspath(__file__))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

__version__ = "2.0.0"
