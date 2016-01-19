# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import setuptools

setuptools.setup(
    name='git-aggregator',
    version='1.0.0',
    description='A library to aggregate git branches from different remotes '
                'into a consolidated one',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: GIT',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
            'GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
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
    install_requires=[
        'kaptan',
        'argcomplete',
        'colorama',
    ],
    entry_points=dict(
        console_scripts=['gitaggregate=git_aggregator.main:main']),
    test_suite='tests',
)
