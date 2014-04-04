import gevent


def start_servers(servers):
    greenlets = []
    for i in servers:
        if isinstance(i, gevent.Greenlet):
            i.start()
            greenlets.append(i)
        else:
            greenlet = gevent.Greenlet.spawn(i.start)
            greenlet.start()
            greenlets.append(greenlet)
    gevent.wait(greenlets)
