import sys
import os
from cx_Freeze import setup, Executable

file_path = 'main.py'

if sys.platform == "win32":
    base = None
    os.environ['TCL_LIBRARY'] = os.path.expanduser('~') + "\\miniconda3\\envs\\rename\\tcl\\tcl8.6"
    os.environ['TK_LIBRARY'] = os.path.expanduser('~') + "\\miniconda3\\envs\\rename\\tcl\\tk8.6"
else:
    base = None

packages = []
includes = [
    "argparse",
    "glob",
    "os",
    "sys",
    "itertools",
    "functools",
    "re",
    "datetime",
    "collections"
]
excludes = [
    "asyncio",
    # "collections",
    "concurrent",
    # "ctypes",
    "distutils",
    "email",
    # "encodings",
    "html",
    "http",
    # "importlib",
    "lib2to3",
    "logging",
    "multiprocessing",
    "pydoc_data",
    "test",
    "tkinter",
    "unittest",
    "urllib",
    "xml",
    "xmlrpc"
]

exe = Executable(
    script=file_path,
    base=base
)

setup(
    name='MultipleRenamer',
    options={
        "build_exe": {
            "packages": packages,
            "includes": includes,
            "excludes": excludes,
        }
    },
    version='1.0',
    description='',
    executables=[exe]
)
