#!/usr/bin/python

'''Signal if coverage code dropped from a set threshold.

Assume coverage html has been run and was successful.'''

import re
import sys


def get_argv(index, default=None):
    '''get script argument at index defaulting to a specified value.'''
    try:
        retval = sys.argv[index]
    except IndexError:
        retval = default
    return retval

THRESHOLD = int(get_argv(1, 60))
REPORT_PATH = get_argv(2, '../reports')


try:
    report = open('{}/index.html'.format(REPORT_PATH)).read()
    current_coverage = int(re.sub(r".+<span class='pc_cov'>(\d+)\%</span>.+",
                                  r"\1", report, flags=re.DOTALL))
except Exception:
    print 'Warning: Coverage cutoff cannot be computed. Ignoring this test.'
    sys.exit(0)

exit_code = 0
if current_coverage < THRESHOLD:
    print 'Code coverage does not meet {}%. Please improve the tests.'.format(
        THRESHOLD)
    exit_code = 1
sys.exit(exit_code)
