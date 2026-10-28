import hashlib
from io import BytesIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.uc001_granite_acquisition_proxy.proxy import BudgetLedger, CEILING
from scripts.uc001_granite_controller.controller import ControllerFailure, PhaseMonitor
from scripts.uc001_granite_controller.worker import Child, NativeRunner, WorkerFailure, run_acquisition
from tests.unit.test_granite_controller_worker import (
    AcquisitionRunner, ProxyApi, ProxyInput, acquisition_config, close_fixture,
)


class FlowApi(ProxyApi):
    def in_job(self, handle, job):
        assert job == 'private-proxy-job'
        return self.rows[handle]['member']
    def children_of(self, parents, timeout_seconds=1):
        return {(row['pid'],row['parent']) for row in self.rows.values()
                if row['exit'] is None and row['parent'] in parents}


class FlowBackend:
    handle = 'private-proxy-job'
    def validate_pid(self, pid, creation_time_100ns=None):
        for handle,row in self.api.rows.items():
            if row['pid']==pid and row['birth']==creation_time_100ns:
                return SimpleNamespace(pid=pid,creation_time_100ns=row['birth'],handle=handle)
        raise ControllerFailure('flow native identity missing')
    def process_exit(self, process):
        return self.api.exit_code(process.handle)


class FlowJournal:
    def __init__(self):
        self.events=[]
    def emit(self,event,**values):
        row=dict(event=event,**values)
        self.events.append(row)
        self.monitor.accept([row])


class FlowRunner(AcquisitionRunner):
    def __init__(self,root,journal,backend,monitor,*,split=True,ledger_launcher=False,extra=False):
        super().__init__(root,journal=journal)
        self.backend,self.monitor=backend,monitor
        self.split,self.ledger_launcher,self.extra=split,ledger_launcher,extra
        self.control=BytesIO()
        self.acknowledgements=[]
        self.fetched=False
    def acknowledge(self,token):
        assert self.monitor.proxy_bound
        assert self.acknowledgements==[]
        self.acknowledgements.append(token)
        self.control.write(token);self.control.seek(0)
    def start(self,argv,label,env=None,stdin=False):
        assert label=='proxy' and stdin
        self.commands.append((argv,label,env))
        self.api=FlowApi(self.split);self.backend.api=self.api
        if self.extra:
            self.api.rows['extra']=dict(pid=999,birth=902,parent=700,member=True,exit=None)
        interpreter=701 if self.split else 700
        ledger=self.root/'evidence/acquisition-proxy.jsonl'
        writer=BudgetLedger(ledger,CEILING,7)
        writer.record('listening',address=['127.0.0.1',12345],
                      pid=700 if self.ledger_launcher else interpreter)
        writer.record('end',status='closed_unqualified',sockets_closed=True);writer.close()
        self.ready_value=dict(pid=interpreter,proxy_url='http://127.0.0.1:12345',ledger=str(ledger),
                              prior_bytes=7,remaining_bytes=CEILING-7)
        identity=dict(pid=700,creation_time_100ns=900,parent_pid=42,in_any_job=True)
        process=SimpleNamespace(pid=700,_handle='launcher',stdin=ProxyInput(),
            poll=lambda:self.api.rows['launcher']['exit'],wait=lambda:self.api.rows['launcher']['exit'])
        out_path=self.root/'evidence/proxy.stdout.log';out=out_path.open('xb')
        err_path=self.root/'evidence/proxy.stderr.log';err=err_path.open('xb')
        self.proxy=Child(process,'proxy',out_path,err_path,out,err,identity)
        self.journal.emit('proxy_launcher_started',schema=1,launcher=identity)
        return self.proxy
    def bind_proxy(self,proxy,ready):
        self.native=NativeRunner(self.root,self.journal,{},api=self.api,control=self.control)
        return self.native.bind_proxy(proxy,ready)
    def run(self,argv,label,env=None,proxy=None):
        if label=='source-fetch':
            assert self.acknowledgements==[b'PROXY_BOUND\n']
            assert self.monitor.proxy_bound and self.monitor.proxy.pid==self.ready_value['pid']
            self.native.check_proxy(proxy)
            self.fetched=True
        return super().run(argv,label,env,proxy)
    def wait(self,proxy):
        assert proxy.process.stdin.value==b'CLOSE\n'
        ledger=self.root/'evidence/acquisition-proxy.jsonl'
        closed=dict(status='meter_closed_unqualified',cleanup_verified=True,cumulative_bytes=7,
                    ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest())
        proxy.stdout_file.write((json.dumps(self.ready_value)+'\n'+json.dumps(closed)+'\n').encode())
        proxy.stdout_file.flush()
        for row in self.api.rows.values():row['exit']=0
        return self.native.wait(proxy)


def flow(tmp_path,monkeypatch,**options):
    import socket
    from scripts.uc001_granite_controller import worker
    def forbidden(*args,**kwargs):
        raise AssertionError('real process/network forbidden in injected flow')
    monkeypatch.setattr(worker.subprocess,'Popen',forbidden)
    monkeypatch.setattr(socket,'socket',forbidden)
    value=acquisition_config(tmp_path,monkeypatch);root=Path(value['root'])
    backend=FlowBackend();journal=FlowJournal();controller_events=[]
    plan=dict(name='acquisition',expected_prior_bytes=7,ledgerpath=root/'evidence/acquisition-proxy.jsonl')
    monitor=PhaseMonitor(plan,backend,lambda event,**values:controller_events.append(dict(event=event,**values)))
    runner=FlowRunner(root,journal,backend,monitor,**options)
    monitor.acknowledge=runner.acknowledge;journal.monitor=monitor
    return value,runner,journal,monitor,controller_events


@pytest.mark.parametrize('split',[True,False])
def test_worker_controller_flow_proves_roles_before_fetch_and_checks_interpreter_ledger(tmp_path,monkeypatch,split):
    value,runner,journal,monitor,observations=flow(tmp_path,monkeypatch,split=split)
    try:
        run_acquisition(value,journal,runner=runner)
        assert runner.fetched
        assert monitor.finish()==7
        assert monitor.proxy.pid==(701 if split else 700)
        assert set(monitor.proxy_role_exits)=={'launcher','interpreter'}
        cleanup=dict(verified=True,active_processes=0,owned_exits=[
            dict(pid=row['pid'],creation_time_100ns=row['birth'],exit_code=0)
            for row in runner.api.rows.values()])
        identity_cleanup=monitor.cleanup(cleanup)
        assert identity_cleanup['verified'] is True
        assert identity_cleanup['phase']=='acquisition'
        assert any(row['event']=='proxy_binding_verified' for row in observations)
    finally:
        if hasattr(runner,'proxy'):close_fixture(runner.proxy)


def test_worker_controller_flow_rejects_launcher_pid_in_listening_ledger(tmp_path,monkeypatch):
    value,runner,journal,monitor,observations=flow(tmp_path,monkeypatch,ledger_launcher=True)
    try:
        with pytest.raises((WorkerFailure,ControllerFailure)):
            run_acquisition(value,journal,runner=runner)
        assert runner.fetched
        assert not monitor.complete
    finally:
        if hasattr(runner,'proxy'):close_fixture(runner.proxy)


def test_worker_controller_flow_denies_extra_branch_before_ack_or_fetch(tmp_path,monkeypatch):
    value,runner,journal,monitor,observations=flow(tmp_path,monkeypatch,extra=True)
    try:
        with pytest.raises((WorkerFailure,ControllerFailure)):
            run_acquisition(value,journal,runner=runner)
        assert not runner.fetched and runner.acknowledgements==[]
        assert not any(row['event']=='proxy_listening' for row in journal.events)
    finally:
        if hasattr(runner,'proxy'):close_fixture(runner.proxy)


def test_proxy_role_events_are_rejected_outside_acquisition_phase():
    backend=FlowBackend();backend.api=FlowApi()
    monitor=PhaseMonitor(dict(name='build'),backend,lambda *args,**kwargs:None)
    with pytest.raises(ControllerFailure,match='non_acquisition'):
        monitor.accept([dict(event='phase_start',phase='build'),
            dict(event='proxy_launcher_started',schema=1,launcher=dict(
                pid=700,creation_time_100ns=900,parent_pid=42,in_any_job=True))])


@pytest.mark.parametrize('expected,observed',[(1,True),(1,1.0),(True,1),(1.0,1),(0,0)])
def test_controller_ledger_pid_requires_positive_integer_identity(tmp_path,expected,observed):
    from scripts.uc001_granite_controller.controller import validate_proxy_terminal
    ledger=tmp_path/'typed-ledger.jsonl';writer=BudgetLedger(ledger,CEILING,7)
    writer.record('listening',address=['127.0.0.1',12345],pid=observed)
    writer.record('end',status='closed_unqualified',sockets_closed=True);writer.close()
    with pytest.raises(ControllerFailure):validate_proxy_terminal(ledger,7,expected_pid=expected)
