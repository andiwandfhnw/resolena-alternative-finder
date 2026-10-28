"""Model-free owned Python check; never sends HTTP or creates a model attempt."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]

from app.infrastructure.llama_cpp_interpreter import strict_json
from scripts.uc001_contract_local_v1_2_2.capture import load_preparation, verify_windows_environment, write_json
from scripts.uc001_contract_local_v1_2_2.harness_checks import check_saved_receipt, verify_python_ownership, stop_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-receipt', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    stage = 'environment'
    try:
        verify_windows_environment()
        stage = 'bundle'; load_preparation()
        stage = 'ownership'
        proof = strict_json(sys.stdin.readline().encode())
        verify_python_ownership(proof)
        stage = 'saved_receipt'
        result = check_saved_receipt(strict_json(args.saved_receipt.read_bytes()))
        result.update(outcome='model_free_worker_checks_passed', ownership='verified_redirector_and_interpreter',
            startup_authorized=False, model_attempt_ledger_touched=False)
        write_json(args.result, result)
        # The supervisor deliberately exercises abort/job-close cleanup while both processes live.
        sys.stdin.readline()
    except Exception as error:
        record = stop_record(error)
        if record['stage'] == 'unknown': record.update(stage=stage, reason='check_failed')
        write_json(args.result, {'outcome': 'failed', **record, 'startup_authorized': False})
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
