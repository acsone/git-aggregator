.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. image:: https://travis-ci.org/acsone/git-aggregator.svg?branch=master
    :target: https://travis-ci.org/acsone/git-aggregator
.. image:: https://coveralls.io/repos/acsone/git-aggregator/badge.png?branch=master 
    :target: https://coveralls.io/r/acsone/git-aggregator?branch=master
.. image:: https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5-blue.svg
    :alt: Python support: 2.7, 3.3, 3.4, 3.5

==============
git-aggregator
==============

Manage the aggregation of git branches from different remotes to build a consolidated one.


Command line Usage:
===================

Create a ``repos.yaml`` file:

  .. code-block:: yaml

	./product_attribute:
	    remotes:
		oca: https://github.com/OCA/product-attribute.git
		acsone: git+ssh://git@github.com/acsone/product-attribute.git
	    merges:
		- oca 8.0
		- oca refs/pull/105/head
		- oca refs/pull/106/head
	    target: acsone aggregated_branch_name

	./connector-interfaces:
	    remotes:
		oca:  https://github.com/OCA/connector-interfaces.git
		acsone:  https://github.com/acsone/connector-interfaces.git
	    merges:
		- oca 6054de2c4e669f85cec380da90d746061967dc83
		- acsone 8.0-connector_flow
		- acsone 80_connector_flow_ir_cron_able-lmi
		- acsone 8.0_connector_flow_improve_eval_config
	    target: acsone aggregated_branch_name
	    fetch_all:
		- oca

If any of your merges refer to a specific commit, you will probably need to
fetch all remotes from the corresponding remote or [use any other strategy to
get that fetch working](http://stackoverflow.com/a/30701724/1468388), but we
recommend to simply add this like in the example above:

    fetch_all:
        - oca
        - other-remote

You can specify that you want to fetch all references from all remotes you have defined with:

    fetch_all: true

Aggregate you repositories at any time:

  .. code-block:: bash

    $ gitaggregate -c repos.yaml

You can also aggregate and automatically push the result to the target:

  .. code-block:: bash

    $ gitaggregate -c repos.yaml -p

Only aggregate a specific repository using `fnmatch`_:

  .. code-block:: bash

    $ gitaggregate -c repos.yaml -p -d connector-interfaces

.. _fnmatch: https://docs.python.org/2/library/fnmatch.html

It's also possible to specify a command or a list of shell commands to execute 
after the aggregation (and before the push). The commands are executed into
the aggregated directory.

  .. code-block:: yaml

	./product_attribute:
	    remotes:
		oca: https://github.com/OCA/product-attribute.git
		acsone: git+ssh://git@github.com/acsone/product-attribute.git
	    merges:
		- oca 8.0
	    target: acsone aggregated_branch_name
            shell_command_after: echo 'my command'

	./connector-interfaces:
	    remotes:
		oca:  https://github.com/OCA/connector-interfaces.git
		acsone:  https://github.com/acsone/connector-interfaces.git
	    merges:
		- oca 9.0
	    target: acsone aggregated_branch_name
            shell_command_after:
		- echo 'a first command'
		- echo 'a second command'

Credits
=======

Author
------

  * Laurent Mignon (ACSONE)
  
Contributors
------------

  * Cyril Gaudin (camptocamp)
  * Jairo Llopis <jairo.llopis@tecnativa.com>

Maintainer
----------

.. image:: https://www.acsone.eu/logo.png
   :alt: ACSONE SA/NV
   :target: http://www.acsone.eu

This module is maintained by ACSONE SA/NV.
