"""
setup_security.py - Compiles Python core modules into C Binary .pyd extensions.
Protects source code against decompilation, anti-tampering, and reverse-engineering.
"""
from setuptools import setup
from Cython.Build import cythonize
import os

modules = [
    "ram_booster/sys_inspector.py",
    "ram_booster/network_optimizer.py",
    "ram_booster/game_mode.py",
    "ram_booster/disk_cleaner.py",
    "ram_booster/optimizer.py",
    "ram_booster/memory.py",
]

setup(
    name="RamBoosterCore",
    ext_modules=cythonize(modules, compiler_directives={'language_level': "3"}),
)
