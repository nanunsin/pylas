from distutils.core import setup
import py2exe, sys, os
import numpy

includes = []

options = {
    "bundle_files":1,
    "compressed":1,
    "optimize":2,
    "includes":includes,
}

def numpy_dll_paths_fix():
    paths = set()
    np_path = numpy.__path__[0]
    for dirpath, _, filenames in os.walk(np_path):
        for item in filenames:
            if item.endswith('.dll'):
                paths.add(dirpath)
    sys.path.append(*list(paths))

numpy_dll_paths_fix()
setup(
    options = {"py2exe": options},
    console=[{'script':"las.py"}],
    zipfile = None,
)