"""A proposed additional allowance is separate from the two consumed predecessors."""

from hashlib import sha256
from pathlib import Path

from app.infrastructure.llama_cpp_interpreter import strict_json
from scripts.uc001_contract_local_v1_4_0.harness_checks import HarnessStop


HERE = Path(__file__).resolve().parent


def verify_execution_approval(approval, bundle):
    raw = (HERE / 'execution-proposal.json').read_bytes()
    proposal = strict_json(raw)
    freeze = bundle['freeze']
    previous = strict_json((HERE / 'previous-execution-freeze.json').read_bytes())
    expected = strict_json((HERE / 'approval.pending.json').read_bytes())
    if (sha256(raw).hexdigest() != freeze['files']['execution-proposal.json']
            or proposal['attempt_identity'] != freeze['attempt_identity']
            or proposal['original_attempt_identity'] != freeze['original_attempt_identity']
            or freeze['previous_startup_allowance_consumed'] is not True
            or proposal['previous_startup_allowance_consumed'] is not True
            or proposal['previous_attempt_identity'] != freeze['previous_attempt_identity']
            or previous['attempt_identity'] != freeze['previous_attempt_identity']
            or previous['original_attempt_identity'] != freeze['original_attempt_identity']
            or proposal['prior_consumed_attempt_identities'] != [freeze['original_attempt_identity'], freeze['previous_attempt_identity']]
            or len({freeze[name] for name in ('attempt_identity','original_attempt_identity','previous_attempt_identity')}) != 3
            or sha256((HERE / 'previous-execution-freeze.json').read_bytes()).hexdigest() != freeze['files']['previous-execution-freeze.json']
            or freeze['original_startup_allowance_consumed'] is not True
            or proposal['original_startup_allowance_consumed'] is not True
            or proposal['attempt_identity'] == proposal['original_attempt_identity']
            or bundle['config']['limits']['startup_count'] != 1
            or proposal['additional_startups'] != 1 or proposal['generations'] != 14
            or bundle['config']['limits']['generations'] != 14
            or proposal['cases_sha256'] != bundle['parent_hashes']['cases.json']
            or expected['approved'] is not False):
        raise HarnessStop('startup', 'approval_proposal_mismatch')
    expected.update(approved=True, freeze_sha256=bundle['freeze_sha256'], approval_reference=approval.get('approval_reference') if isinstance(approval, dict) else None)
    if (not isinstance(approval, dict) or approval != expected or approval.get('approved') is not True
            or type(approval.get('additional_startups')) is not int or type(approval.get('generations')) is not int
            or not isinstance(approval.get('approval_reference'), str) or not approval['approval_reference'].strip()):
        raise HarnessStop('startup', 'approval_required')
    return approval


def require_execution_approval(path, bundle):
    if path is None:
        raise HarnessStop('startup', 'approval_required')
    return verify_execution_approval(strict_json(Path(path).read_bytes()), bundle)
