import os

from setuptools import find_packages, setup


def read(file_name):
    """Read the provided file."""
    this_dir = os.path.dirname(__file__)
    file_path = os.path.join(this_dir, file_name)
    with open(file_path) as f:
        return f.read()


def version_scheme(version):
    """
    Version scheme hack for setuptools_scm.
    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342
    If that issue is resolved, this method can be removed.
    """
    import time

    from setuptools_scm.version import guess_next_version

    if version.exact:
        return version.format_with("{tag}")
    else:
        _super_value = version.format_next_version(guess_next_version)
        now = int(time.time())
        return _super_value + str(now)


def local_version(version):
    """
    Local version scheme hack for setuptools_scm.
    Appears to be necessary to due to the bug documented here: https://github.com/pypa/setuptools_scm/issues/342
    If that issue is resolved, this method can be removed.
    """
    return ""


setup(
    name="civic-scraper",
    description="Tools for downloading agendas, minutes and other documents produced by local government",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Serdar Tumgoren",
    author_email="zstumgoren@gmail.com",
    url="https://github.com/biglocalnews/civic-scraper",
    packages=find_packages(),
    include_package_data=True,
    entry_points="""
        [console_scripts]
        civic-scraper=civic_scraper.cli:cli
    """,
    install_requires=[
        "bs4",
        "click",
        "click-option-group",
        "feedparser",
        "requests",
        "demjson3",
        "scraper-legistar",
    ],
    license="Apache 2.0 license",
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    test_suite="tests",
    tests_require=[
        "flake8",
        "pytest",
        "pytest-vcr",
        "pytz",
        "typing-extensions",
        "vcrpy",
    ],
    setup_requires=["setuptools_scm"],
    use_scm_version={"version_scheme": version_scheme, "local_scheme": local_version},
    project_urls={
        "Documentation": "https://civic-scraper.readthedocs.io",
        "Maintainer": "https://github.com/biglocalnews",
        "Source": "https://github.com/biglocalnews/civic-scraper",
        "Tracker": "https://github.com/biglocalnews/civic-scraper/issues",
    },
)
