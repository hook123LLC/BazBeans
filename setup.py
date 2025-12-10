#!/usr/bin/env python3
"""
BazBeans Setup Script

A reusable toolkit for orchestrating distributed applications across multiple nodes.
"""

from setuptools import setup, find_packages
import os

# Import custom commands
try:
    from setup_cli_command import get_cmdclass
    CMDCLASS = get_cmdclass()
except ImportError:
    CMDCLASS = {}

# Read the contents of README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='bazbeans',
    version='0.1.9',
    description='Generic Multi-Node Control Plane Toolkit',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='hook123 LLC',
    author_email='hello@hook123.com',
    url='https://github.com/hook123LLC/bazbeans',
    project_urls={
        'Documentation': 'https://bazbeans.readthedocs.io/',
        'Source': 'https://github.com/hook123LLC/bazbeans',
        'Tracker': 'https://github.com/hook123LLC/bazbeans/issues',
    },
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.8',
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=4.0',
            'black>=22.0',
            'flake8>=5.0',
            'mypy>=1.0',
        ],
        'docker': ['docker>=6.0.0'],
    },
    cmdclass=CMDCLASS,
    entry_points={
        'console_scripts': [
            'bazbeans-cli=src.control_cli:cli',
            'bazbeans-agent=src.node_agent:NodeAgent',
            'bazbeans-updater=src.nginx_updater:NginxUpdater',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Systems Administration',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Database :: Database Engines/Servers',
    ],
    keywords='cluster orchestration distributed nodes load-balancer redis',
    include_package_data=True,
    zip_safe=False,
)