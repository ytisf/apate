import sys
from apate.core.globals import *


class COLORS:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    ENDC = '\033[0m'

    INFO = BLUE + "[+]\t" + ENDC
    GOOD = GREEN + "[+]\t" + ENDC
    WARNING = RED + "[!]\t" + ENDC
    ERROR = RED + "[X]\t" + ENDC


INFORMATION = 6
SUCCESS = 5
WARNING = 9
ERROR = 8


def LogMe(caller, m_type, message):
    """
    This code was written in Jan 2016 as a part of an open source project and
    is only to be used with GPLv3 License used by tisf.
    """

    if m_type is INFORMATION:
        sys.stdout.write(COLORS.INFO + str(caller) + " : " + message + "\n")

    elif m_type is SUCCESS:
        sys.stdout.write(COLORS.GOOD + str(caller) + " : " + message + "\n")

    elif m_type is WARNING:
        sys.stderr.write(COLORS.WARNING + str(caller) + " : " + message + "\n")

    elif m_type is ERROR:
        sys.stderr.write(COLORS.ERROR + str(caller) + " : " + message + "\n")
