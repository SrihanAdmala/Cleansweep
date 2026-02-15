"""
CleanSweep — Open Source PC Cleaner
pip install cleansweep
"""

from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="cleansweep",
    version="1.0.0",
    author="CleanSweep Contributors",
    author_email="hello@cleansweep.dev",
    description="Free, open-source PC cleaner and optimizer for Windows, macOS, and Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cleansweep/cleansweep",
    project_urls={
        "Bug Tracker":   "https://github.com/cleansweep/cleansweep/issues",
        "Documentation": "https://github.com/cleansweep/cleansweep#readme",
        "Source Code":   "https://github.com/cleansweep/cleansweep",
    },
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    package_data={
        "": ["templates/**", "static/**"],
    },
    install_requires=[
        "flask>=2.3.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "black",
            "flake8",
        ],
    },
    entry_points={
        "console_scripts": [
            "cleansweep=run:main",
        ],
    },
    keywords=[
        "cleaner", "optimizer", "junk", "temp files",
        "pc cleaner", "disk cleanup", "cache cleaner",
        "windows cleaner", "macos cleaner", "linux cleaner",
    ],
)
