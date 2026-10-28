import hashlib
import json
from pathlib import Path

import pytest

from scripts.uc001_granite_controller.controller import ControllerFailure, HELPER_NAMES, validate_native_config


HELPERS = Path('scripts/uc001_granite_controller').resolve()


def configuration(tmp_path):
    from scripts.uc001_granite_acquisition_proxy.proxy import BUNDLE
    proxy = Path('scripts/uc001_granite_acquisition_proxy/proxy.py').resolve()
    frozen = Path('scripts/uc001_granite_contract_v1/config.json').resolve()
    prior = tmp_path/'prior.json'
    prior.write_text(json.dumps(dict(bundle_id=BUNDLE,owner='synthetic',accounting_complete=True,
                                    previously_charged_bytes=7)))
    return dict(execution_authorized=True,owner='synthetic',root=r'C:\Resolena\gn1-20261025',
                proxy_helper=str(proxy),prior_receipt=str(prior),
                prior_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
                frozen_config=str(frozen),
                helper_hashes={name:hashlib.sha256((HELPERS/name).read_bytes()).hexdigest()
                    for name in HELPER_NAMES})


def test_unapproved_template_cannot_launch_any_worker(tmp_path):
    cfg=configuration(tmp_path);cfg['execution_authorized']=False
    with pytest.raises(ControllerFailure):
        validate_native_config(cfg,HELPERS)


def test_native_config_preserves_fixed_root_and_requires_prior_accounting(tmp_path):
    cfg=configuration(tmp_path)
    validated=validate_native_config(cfg,HELPERS)
    assert validated['prior_bytes']==7
    cfg['root']=r'C:\unreviewed-alternate'
    with pytest.raises(ControllerFailure):
        validate_native_config(cfg,HELPERS)


def test_changed_controller_helper_is_not_silently_accepted(tmp_path):
    cfg=configuration(tmp_path);cfg['helper_hashes']['worker.py']='0'*64
    with pytest.raises(ControllerFailure):
        validate_native_config(cfg,HELPERS)


def test_prior_unknown_is_not_a_new_zero_budget(tmp_path):
    cfg=configuration(tmp_path)
    path=Path(cfg['prior_receipt']);row=json.loads(path.read_text());row['accounting_complete']=False
    path.write_text(json.dumps(row));cfg['prior_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ControllerFailure):
        validate_native_config(cfg,HELPERS)


def test_diagnostic_helper_cannot_expand_the_native_controller_manifest(tmp_path):
    cfg=configuration(tmp_path)
    cfg['helper_hashes']['proxy_no_network.py']=hashlib.sha256((HELPERS/'proxy_no_network.py').read_bytes()).hexdigest()
    with pytest.raises(ControllerFailure,match='controller_manifest_incomplete'):
        validate_native_config(cfg,HELPERS)
