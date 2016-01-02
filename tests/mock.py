from __future__ import absolute_import

import contextlib
import mock


@contextlib.contextmanager
def mock_signal_receiver(signal, wraps=None, **kwargs):
    """
    Taken from mock_django as importing mock_django created issues with Django
    1.9+

    Temporarily attaches a receiver to the provided ``signal`` within the scope
    of the context manager.

    The mocked receiver is returned as the ``as`` target of the ``with``
    statement.

    To have the mocked receiver wrap a callable, pass the callable as the
    ``wraps`` keyword argument. All other keyword arguments provided are passed
    through to the signal's ``connect`` method.
    """
    if wraps is None:
        def wraps(*args, **kwrags):
            return None

    receiver = mock.Mock(wraps=wraps)
    signal.connect(receiver, **kwargs)
    yield receiver
    signal.disconnect(receiver)
