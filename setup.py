# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import setuptools

setuptools.setup(
    name='git_aggregator',
    use_scm_version=True,
    description='A program to aggregate git branches from different remotes '
                'into a consolidated one',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
        'GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        "Topic :: Utilities",
        "Topic :: System :: Shells",
    ],
    license="AGPLv3+",
    author='ACSONE SA/NV',
    author_email='info@acsone.eu',
    url='http://github.com/acsone/git-aggregator',
    packages=[
        'git_aggregator',
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    install_requires=[
        'PyYAML>=5',
        'argcomplete',
        'colorama',
        'requests',
    ],
    python_requires=">=3.7",
    entry_points=dict(
        console_scripts=['gitaggregate=git_aggregator.main:main']),
    test_suite='tests',
)
