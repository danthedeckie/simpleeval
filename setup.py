#!/usr/bin/env python3
from pathlib import Path

from setuptools import setup
from setuptools.config import read_configuration

import setuptools_scm

if __name__ == "__main__":
    p = Path(__file__).parent
    setup_dict = read_configuration(str(p / "setup.cfg"))
    v = setuptools_scm.version_from_scm(str(p))
    __version__ = setuptools_scm.format_version(
        v,
        version_scheme=setuptools_scm.DEFAULT_VERSION_SCHEME,
        local_scheme=setuptools_scm.DEFAULT_LOCAL_SCHEME,
    )
    setup_dict = {
        "version": __version__,
    }
    if v.exact:
        setup_dict["download_url"] = setup_dict["url"] + "/tarball/" + str(v.tag)
    setup(**setup_dict)
