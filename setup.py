"""Build hook for EchoTime's optional C++ kernels.

All metadata lives in pyproject.toml. The extension is marked optional: if it
cannot be compiled (no C++17 compiler, unsupported platform) the install still
succeeds and EchoTime runs the pure-Python reference implementation.
"""

import os
import platform
import sys

from setuptools import setup

ext_modules = []
cmdclass = {}
try:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
except ImportError:  # pybind11 is a build requirement; tolerate its absence
    Pybind11Extension = None

if Pybind11Extension is not None:
    if sys.platform == "win32":
        compile_args = ["/O2", "/fp:precise"]
        link_args = []
    else:
        # Exactness matters more than the last few percent: no fast-math and no
        # FMA contraction, so results match the Python reference bit for bit.
        compile_args = ["-O3", "-fno-fast-math", "-ffp-contract=off", "-pthread"]
        link_args = ["-pthread"]
        # Python builds compiled with -march=native leak that flag into
        # extensions; pin a portable x86-64 level so a build made on one node
        # runs on every node of a cluster. ECHOTIME_NATIVE_MARCH=none keeps the
        # toolchain default.
        march = os.environ.get("ECHOTIME_NATIVE_MARCH", "x86-64-v3")
        if march.lower() != "none" and sys.platform.startswith("linux") and platform.machine() in ("x86_64", "AMD64"):
            compile_args.append(f"-march={march}")
    ext = Pybind11Extension(
        "echotime._echotime_native",
        ["native/echotime_native.cpp"],
        cxx_std=17,
        extra_compile_args=compile_args,
        extra_link_args=link_args,
    )
    ext.optional = True
    ext_modules.append(ext)
    cmdclass["build_ext"] = build_ext

setup(ext_modules=ext_modules, cmdclass=cmdclass)
