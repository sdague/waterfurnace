============
waterfurnace
============


.. image:: https://img.shields.io/pypi/v/waterfurnace.svg
   :target: https://pypi.python.org/pypi/waterfurnace

.. image:: https://img.shields.io/travis/sdague/waterfurnace.svg
   :target: https://travis-ci.org/sdague/waterfurnace

.. image:: https://readthedocs.org/projects/waterfurnace/badge/?version=latest
   :target: https://waterfurnace.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://pyup.io/repos/github/sdague/waterfurnace/shield.svg
   :target: https://pyup.io/repos/github/sdague/waterfurnace/
   :alt: Updates


Python interface for waterfurnace geothermal systems.

This provides basic sensor readings for waterfurnace geothermal systems by
using the websocket interface that exists for the symphony website. This is not
a documented or stable interface, so don't use this for critical
systems. However, it is useful to record historical usage of your waterfurnace
system.

Usage
=====

.. code-block:: python

   from waterfurnace.waterfurnace import WaterFurnace
   wf = WaterFurnace(user, pass)
   wf.login()
   data = wf.read()

The waterfurnace symphony service websocket monitors it's usage, so you need to
do a data reading at least every 30 seconds otherwise the websocket is closed
on the server side for resource constraints. The symphony website does a poll
on the websocket every 5 seconds.

Known Issues / limitations
==========================

* The python websocket code goes into a blocked state after long periods of
  usage (always takes days to get to this state). I've yet to discover
  why. Help welcome.
* If you have multiple waterfurnace units on one account, this will only use
  the first.


License
=======

* Free software: Apache Software License 2.0
.. * Documentation: https://waterfurnace.readthedocs.io.


Credits
=======

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
