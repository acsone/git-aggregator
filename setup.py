# -*- coding: utf-8 -*-
# © 2015 ACSONE SA/NV
# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)

import setuptools

setuptools.setup(
    name='git-aggregator',
    version='0.7.0',
    description='A library to aggregate git branches from different remotes '
                'into a consolidated one',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: GIT',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: '
            'GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
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
