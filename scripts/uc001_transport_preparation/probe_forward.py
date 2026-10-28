"""Prepared model-free transport check. No application/interpreter execution."""

import json
import signal
import sys

import httpx

from scripts.uc001_execution_v1_3_0.run import verify_forward_listener


def check_service(client, key):
    for token, expected in ((None, 401), ('deliberately-wrong', 401), (key, 200)):
        headers = {} if token is None else {'Authorization': 'Bearer ' + token}
        response = client.get('/probe', headers=headers)
        if response.status_code != expected:
            raise ValueError('Model-free protected probe rejected authentication policy')
        if expected == 200 and response.content != b'uc001-model-free-transport\n':
            raise ValueError('Forwarded probe identity differs')


def main():
    def expired(_signal, _frame):
        raise TimeoutError('Model-free remote probe deadline expired')

    signal.signal(signal.SIGALRM, expired)
    signal.alarm(30)
    key = None
    try:
        listeners = verify_forward_listener()
        key = sys.stdin.readline().strip()
        if len(key) < 32:
            raise ValueError('Ephemeral test authentication absent')
        with httpx.Client(base_url='http://127.0.0.1:49188', timeout=3, trust_env=False, follow_redirects=False) as client:
            check_service(client, key)
        print(json.dumps({'outcome': 'model_free_forwarding_passed', 'listeners': listeners,
                         'owned_gpu_counter_verified': False, 'model_readiness_verified': False}))
    finally:
        signal.alarm(0)
        key = None


if __name__ == '__main__':
    main()
