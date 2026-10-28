import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import time

from common import HERE, ORIGINAL, append, required_clear_correct, write, load_context, deadline, worker_start

c = load_context()
RUN = Path(c["run_dir"])
EXP = ORIGINAL


def deny_network(event, args):
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system'}:
        raise RuntimeError('Detector worker forbids network and subprocesses: ' + event)


sys.addaudithook(deny_network)
freeze_sha = c['freeze_sha256']
assert hashlib.sha256((HERE / 'freeze.json').read_bytes()).hexdigest() == freeze_sha
assert sys.prefix == str(RUN / 'venv')
assert importlib.metadata.version('lingua-language-detector') == '2.2.0'
assert len(os.sched_getaffinity(0)) <= c['limits']['cpu_threads']
worker_start(c, 'detector')
start = time.perf_counter()
from lingua import LanguageDetectorBuilder
import_seconds = time.perf_counter() - start
start = time.perf_counter()
detector = LanguageDetectorBuilder.from_all_languages().build()
builder_seconds = time.perf_counter() - start
write(RUN / 'initialization.json', {'import_seconds': import_seconds, 'builder_seconds': builder_seconds,
      'accuracy_mode': 'default high', 'all_languages': True, 'relative_distance': 'default; unchanged',
      'model_loading': 'default lazy; cache occupancy/misses not exposed', 'classification_calls': 0})
cases = {c['id']: c for c in json.loads((EXP / 'cases.json').read_text())}
order = json.loads((EXP / 'order.json').read_text())
calls = 0
for item in order:
    deadline(c)
    case = cases[item['case']]
    record_start = time.perf_counter()
    outputs = {}
    times = {}
    for operation in item['operations']:
        deadline(c)
        calls += 1
        assert calls <= c['limits']['library_calls']
        append(RUN / 'calls.jsonl', {'call': calls, 'record': item['record'], 'case': case['id'],
               'operation': operation, 'status': 'started', 'monotonic': time.monotonic(),
               'freeze_sha256': freeze_sha})
        begin = time.perf_counter()
        if operation == 'compute_language_confidence_values':
            values = detector.compute_language_confidence_values(case['text'])
            elapsed = time.perf_counter() - begin
            outputs['ranked_languages'] = [{'language': v.language.iso_code_639_1.name.lower(),
                                          'score': v.value} for v in values]
            assert len(values) == 75
        elif operation == 'detect_multiple_languages_of':
            values = detector.detect_multiple_languages_of(case['text'])
            elapsed = time.perf_counter() - begin
            outputs['spans'] = [{'language': v.language.iso_code_639_1.name.lower(),
                                 'start': v.start_index, 'end': v.end_index,
                                 'text': case['text'][v.start_index:v.end_index]} for v in values]
        else:
            raise RuntimeError('Unknown frozen operation')
        times[operation] = elapsed
        append(RUN / 'calls.jsonl', {'call': calls, 'record': item['record'], 'operation': operation,
               'status': 'completed', 'seconds': elapsed, 'raw_output': outputs.get('ranked_languages')
               if operation == 'compute_language_confidence_values' else outputs['spans']})
    top = outputs['ranked_languages'][0]['language']
    record = {**item, 'text': case['text'], 'category': case['category'], 'freeze_sha256': freeze_sha,
              'raw_detector': outputs, 'raw_top_rank': top,
              'required_clear_correct': required_clear_correct(case, top),
              'seconds': times, 'record_seconds': time.perf_counter() - record_start,
              'review_reference': {'expected_route': case['expected_contract_route'],
                    'allowed_external_pairs': case['allowed_external_pairs'],
                    'context': {k: case[k] for k in ['country', 'existing_explanation_language', 'browser_language']},
                    'source': 'Frozen AI-assisted expectation, not detector-produced or observed application behaviour'},
              'application_executed': False, 'meaning_or_constraint_verification_executed': False,
              'classification_calls_so_far': calls,
              'worker_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
              'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    append(RUN / 'records.jsonl', record)
    write(RUN / 'progress.json', {'completed_records': item['record'], 'attempted_classification_calls': calls,
          'last_case': case['id'], 'status': 'running', 'worker_maxrss_bytes': record['worker_maxrss_bytes']})
    if record['worker_maxrss_bytes'] > c['limits']['owned_rss_bytes']:
        raise RuntimeError('worker RSS cap exceeded')
write(RUN / 'worker-exit.json', {'status': 'completed', 'records': len(order),
      'classification_calls': calls, 'exit_code': 0,
      'cold_initialization_plus_first_record_seconds': import_seconds + builder_seconds +
         json.loads((RUN / 'records.jsonl').read_text().splitlines()[0])['record_seconds'],
      'worker_maxrss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
      'utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
write(RUN / 'progress.json', {'status': 'completed', 'completed_records': len(order),
      'attempted_classification_calls': calls, 'worker_exit_code': 0})
