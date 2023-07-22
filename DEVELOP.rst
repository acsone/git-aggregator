Developer instructions
~~~~~~~~~~~~~~~~~~~~~~

How to run tests
----------------

* run ``tox`` (if not installed ``apt-get install tox``)

How to release
--------------

* update the changelog into the README.rst file with the list of changes since the last version
* python setup.py check --restructuredtext
* commit everything
* make sure tests pass!
* git push and make sure CI is green
* create a tagged release on GitHub, which will trigger deployment to PyPI
