"""
Utilities for debugging a python application/process.  This is not specifically related testing, but related more to
just debugging of code and process which could be in production.
"""
import signal
import sys


def enable_thread_dump_signal(signum=signal.SIGUSR1, dump_file=sys.stderr):
    """Turns on the ability to dump all of the threads to

    Currently this is just a wrapper around the faulthandler module

    :param signum: The OS signal to listen for and when signalled the thread dump should be outputted to `dump_file`.
        The default is the SIGUSR1 signal
    :type signum: int
    :param dump_file: The dump_file to output the threaddump to upon the signal being sent to the process.
    :type dump_file: file
    """
    import faulthandler
    faulthandler.register(signum, file=dump_file, all_threads=True, chain=True)
