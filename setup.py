from setuptools import setup
from Cython.Build import cythonize

setup(
    name='CPGeometryUtils',
    ext_modules=cythonize("invasionEngine\cpmodules\geometry_utils.pyx"),
    zip_safe=False,
)
