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

The Routing System
------------------

.. autoclass:: gimme.routes.Routes
   :members:

.. autoclass:: gimme.routes.RouteMapping
   :members:

.. autoclass:: gimme.routes.Route
   :members:
   :special-members:

.. autoclass:: gimme.routes.RouteList
   :members:

Sessions
--------

If :func:`gimme.middleware.session` is in use, a session object is made
available at :attr:`Request.session`. Typical usage is something like::

    class SomeController(gimme.Controller):
        def some_method(self):
            if 'user_name' not in self.request.session:
                self.request.session['user_name'] = get_user_name()
            return {'user_name': self.request.session['user_name']}

.. autoclass:: gimme.ext.session.Session
   :members:
   :special-members:

Engines
-------
Gimme makes it very easy to implement adapters to interface with your favorite
template engine (I call these adapters "engines", terminology taken from
Express JS).

All that is needed is to subclass of the :class:`gimme.engines.BaseEngine`
(abstract base) class and implement the :meth:`render` method.

Example::

    class SomeEngine(gimme.engines.BaseEngine):
        def render(self, template, data):
            return fetch_template(template, data)

Now, to use your new engine, simply pass it to your app on instantiation::

    app = App(engine=SomeEngine())

.. autoclass:: gimme.engines.BaseEngine
   :members:

.. autoclass:: gimme.engines.Jinja2Engine
   :members:

Middleware
----------
.. autoclass:: gimme.middleware.Middleware
   :members:

.. autofunction:: gimme.middleware.static

.. autofunction:: gimme.middleware.cookie_parser

.. autofunction:: gimme.middleware.session

.. autofunction:: gimme.middleware.json

.. autofunction:: gimme.middleware.urlencoded

.. autofunction:: gimme.middleware.multipart

.. autofunction:: gimme.middleware.body_parser

.. autofunction:: gimme.middleware.compress


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

