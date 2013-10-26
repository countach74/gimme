#!/usr/bin/env python

import gimme
import routes


app = gimme.App()

app.use(gimme.middleware.static('public'))
app.use(gimme.middleware.method_override())
{%- if config.session %}
app.use(gimme.middleware.cookie_parser())
app.use(gimme.middleware.session())
{%- endif %}
app.use(gimme.middleware.body_parser())

routes.setup(app)


if __name__ == '__main__':
    app.listen()
