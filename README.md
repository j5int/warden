Warden
======

Warden is a Python application that monitors other Python applications running locally, and ships events to a Sentry instance and metrics to a Graphite instance.

Warden can currently:
- Track memory and cpu usage of given processes
- Display metrics using Graphite render
- Send events from applications to Sentry

Warden will be able to:
- tail log files
- ping urls
- watch running processes

Unit Tests
==========

Tests using Python's unittest module exist in the 'test' directory. They can be run individually as python scripts, but CANNOT be run using 'nose' because of the nature of the Twisted reactor.
# Most of the tests are currently broken