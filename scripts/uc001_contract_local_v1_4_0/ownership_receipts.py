"""Recorded consistency uses the verified policy with labelled readers, never live-query credit."""

import ntpath

from scripts.uc001_contract_local_v1_4_0.harness_checks import HarnessStop, verify_python_ownership


def verify_server_receipt(receipt, bundle):
    try:
        server = receipt['python_ownership']['server']
        expected = ntpath.join(bundle['config']['reuse_root'], 'runtime', 'llama-server.exe')
        if (type(receipt['owned_pid']) is not int or type(receipt['owned_created']) is not int
                or server['pid'] != receipt['owned_pid'] or server['created'] != receipt['owned_created']
                or server['image'].casefold() != expected.casefold()):
            raise ValueError()
        return expected
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise HarnessStop('ownership', 'server_receipt_mismatch') from error


def verify_recorded_ownership(receipt, bundle):
    expected = verify_server_receipt(receipt, bundle)
    proof = receipt['python_ownership']
    identities = [proof[name] for name in ('supervisor', 'server', 'redirector', 'interpreter')] + proof['console_helpers']
    recorded = {identity['pid']: identity for identity in identities}
    verify_python_ownership(proof, reader=lambda pid: recorded[pid],
        self_pid=proof['interpreter']['pid'], self_parent=proof['redirector']['pid'],
        system_directory=lambda: bundle['local']['ownership_windows_system_directory'], server_executable=expected)
    return 'recorded_identity_consistency_only'


def verify_recorded_cleanup(receipt, cleanup, bundle):
    verify_recorded_ownership(receipt, bundle)
    proof = receipt['python_ownership']
    identities = [(proof[name], name) for name in ('server', 'redirector', 'interpreter')]
    identities += [(identity, 'console_helper') for identity in proof['console_helpers']]
    expected = {identity['pid']: (identity['created'], role) for identity, role in identities}
    exits = cleanup['owned_exits']
    if (cleanup['owned_job_closed'] is not True or cleanup['errors'] or cleanup.get('unidentified_job_pids')
            or len(exits) != len(expected)
            or any(type(row['pid']) is not int or type(row.get('created')) is not int or row['exit_confirmed'] is not True
                or expected.get(row['pid']) != (row['created'], row.get('role')) for row in exits)
            or len({row['pid'] for row in exits}) != len(expected)):
        raise HarnessStop('cleanup', 'recorded_identity_mismatch')
