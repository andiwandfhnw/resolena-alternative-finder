"""Technical-run authorization is separate from qualified semantic acceptance."""

from hashlib import sha256
from pathlib import Path

from app.infrastructure.llama_cpp_interpreter import strict_json


HERE = Path(__file__).resolve().parent


def require_technical_review(path, bundle):
    if path is None:
        raise ValueError('Original partial review is required for the technical decision')
    return verify_technical_review(strict_json(Path(path).read_bytes()), bundle)


def verify_technical_review(review, bundle):
    records = {}
    for name in ('technical-decision.json', 'partial-expectations-review.json', 'previous-freeze.json'):
        raw = (HERE / name).read_bytes()
        if sha256(raw).hexdigest() != bundle['freeze']['files'][name]:
            raise ValueError('Frozen technical decision/review provenance changed')
        records[name] = strict_json(raw)
    decision = bundle.get('technical_decision')
    if decision != records['technical-decision.json']:
        raise ValueError('Recorded owner technical decision is required')
    previous = records['previous-freeze.json']
    old_hash = sha256((HERE / 'previous-freeze.json').read_bytes()).hexdigest()
    inputs = {name: bundle['parent_hashes'][name] for name in ('prompt.txt', 'schema.json', 'cases.json', 'config.json')}
    if (decision.get('purpose') != 'technical_feasibility_only'
            or decision.get('technical_execution_permitted') is not True
            or decision.get('semantic_acceptance_permitted') is not False
            or decision.get('expected_meanings_approved') is not False
            or decision.get('allowance_reset') is not False
            or decision.get('owner') != {'role': 'project owner', 'github_account': 'andiwandfhnw'}
            or decision.get('attempt_identity') != bundle['freeze']['attempt_identity']
            or decision.get('previous_freeze_sha256') != old_hash
            or bundle['freeze']['previous_freeze_sha256'] != old_hash
            or previous['parent_freeze_sha256'] != bundle['parent_freeze_sha256']
            or previous['attempt_identity'] != bundle['freeze']['attempt_identity']
            or decision.get('unchanged_inputs') != inputs
            or decision.get('partial_review_sha256') != sha256((HERE / 'partial-expectations-review.json').read_bytes()).hexdigest()):
        raise ValueError('Owner decision does not cover these unchanged inputs and original allowance')
    if (review != records['partial-expectations-review.json'] or review.get('status') != 'pending'
            or review.get('expected_meanings_approved') is not False or review.get('freeze_sha256') != old_hash):
        raise ValueError('Original partial review/confirmation must remain unchanged and pending')
    return review


def review_status():
    return {'execution_purpose': 'technical_feasibility_only', 'semantic_review': 'pending',
        'expected_meanings_approved': False, 'expectations': 'provisional',
        'interpreter_suitability_verified': False, 'multilingual_acceptance_verified': False}
