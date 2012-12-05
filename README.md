Warden
======

Warden is a Python application that monitors other Python applications running locally, and ships events to a Sentry instance and metrics to a Graphite instance.

Warden can tail log files, watch that processes are running, ping an HTTP url, and track memory and CPU usage.

It provides a plug-in architecture allowing custom checks to be implemented.

Finally, there is an API that can be used by the monitored application to publish events, and do some internal checks (e.g. for stuck threads).

Unit Tests
==========

Tests using Python's unittest module exist in the 'test' directory. They can be run individually as python scripts, but CANNOT be run using 'nose' because of the nature of the Twisted reactor.
