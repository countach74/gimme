.. Gimme documentation master file, created by
   sphinx-quickstart on Sat Feb  8 22:38:52 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Gimme's API Documentation
=========================

.. Contents:

.. .. toctree::
..    :maxdepth: 2

Application Creation
--------------------
.. autoclass:: gimme.app.App
   :members:

Requests, Responses, and Controllers
------------------------------------
Of course, one of the primary things that any web framework must do, is handle
requests and make responses. The MVC paradigm generally ties these two
elements together via the controller. Gimme is no different.

Typically, the application developer will create controllers and their
corresponding methods, then create routes to those methods. A very simple
application may do something like the following::

    app = gimme.App()

    class RootController(gimme.Controller):
        def index(self):
            self.response.headers['Some-Header'] = 'value'
            return {
                'today': datetime.datetime.now(),
                'user_name': self.request.session['user_name']
            }

    app.routes.get('/', RootController.index + '/path/to/template.html')

There's really not much more to it than that (although I do recommend checking
out the documentation for the :class:`gimme.request.Request` and
:class:`gimme.response.Response` classes).

*One important gotcha: controller methods that are to be bound to routes
should NEVER start with _*

.. autoclass:: gimme.controller.Controller
   :members:

.. autoclass:: gimme.controller.ControllerMethod
   :members:
   :special-members:

.. autoclass:: gimme.controller.MethodRenderer
   :members:
   :special-members:

.. autoclass:: gimme.request.Request
   :members:

.. autoclass:: gimme.response.Response
   :members:

Engines
-------
.. autoclass:: gimme.engines.Jinja2Engine
   :members:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

