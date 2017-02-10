"""
Basic set of smoke tests that literally just check for 200 return codes for
commonly used URLs.

To use, do::

  $ make test-smoketest

To specify a server to run against::

  $ SERVER_URL=http://example.com make test-smoketest

"""

import os
import sys

import requests


BASEURL = os.environ.get('SERVER_URL', 'http://web:8000')


def main():
    # Does the front page work?
    resp = requests.get(BASEURL)
    assert resp.status_code == 200

    # Do team pages work?
    resp = requests.get(BASEURL + '/team/sumo/')
    assert resp.status_code == 200

    # Do project pages work?
    resp = requests.get(BASEURL + '/project/input/')
    assert resp.status_code == 200

    # Does the weekly page work?
    resp = requests.get(BASEURL + '/weekly/?week=2017-02-06')
    assert resp.status_code == 200

    # Does search work?
    resp = requests.get(BASEURL + '/search/')
    assert resp.status_code == 200

    resp = requests.get(BASEURL + '/search/?query=asdf')
    assert resp.status_code == 200

    print('Done!')
    return 0


if __name__ == '__main__':
    sys.exit(main())
