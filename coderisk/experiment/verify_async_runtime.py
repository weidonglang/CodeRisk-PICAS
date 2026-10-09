"""Local-service execution check on self-authored synthetic code; not an accuracy experiment."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]


def request(base,path,body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as response:
        return json.load(response)['data']


def upload(base,q,index):
    code=f'def sum_{index}(values):\n    result = {index}\n    for number in values:\n        result += number\n    return result\nprint(sum_{index}([1, 2, 3]))\n'
    boundary='CodeRisk'+uuid.uuid4().hex
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic_{index}.py"\r\nContent-Type: text/plain\r\n\r\n'+code+f'\r\n--{boundary}--\r\n').encode()
    req=urllib.request.Request(f'{base}/questions/{q}/submissions/upload',data=body,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(req,timeout=10) as response:
        return json.load(response)['data']


def terminal(base,task):
    samples=[]
    end=time.monotonic()+180
    while time.monotonic()<end:
        row=request(base,f'/tasks/{task}')
        samples.append({k:row[k] for k in ('status','finishedPairs','failedPairs','progress')})
        if row['status'] in {'FINISHED','PARTIAL','FAILED'}:
            return row,samples
        time.sleep(.1)
    raise TimeoutError('Synthetic task exceeded declared check budget')


def run(base,upload_root,output):
    if not base.startswith('http://127.0.0.1:'):
        raise ValueError('This check only targets an explicitly started localhost service')
    q=request(base,'/questions',{'title':'Synthetic asynchronous execution check','description':'Self-authored runtime fixtures, not research labels.'})['id']
    submissions=[upload(base,q,i) for i in range(50)]
    measurements=[]
    for n in (10,20,50):
        task=request(base,'/tasks',{'questionId':q,'taskName':f'Synthetic scale {n}','submissionIds':[s['id'] for s in submissions[:n]]})['id']
        begin=time.perf_counter()
        accepted=request(base,f'/tasks/{task}/start',{})
        start_seconds=time.perf_counter()-begin
        duplicate=request(base,f'/tasks/{task}/start',{})
        done,samples=terminal(base,task)
        total_seconds=time.perf_counter()-begin
        expected=n*(n-1)//2
        assert done['status']=='FINISHED' and done['finishedPairs']==expected and done['failedPairs']==0
        results=request(base,f'/tasks/{task}/results?page=1&pageSize=100')
        assert results['total']==expected and all(not r['isMock'] for r in results['items'])
        measurements.append({'submissions':n,'pairs':expected,'task_id':task,'start_response_seconds':start_seconds,
            'completion_observed_seconds':total_seconds,'accepted_status':accepted['status'],
            'duplicate_start_status':duplicate['status'],'final':{k:done[k] for k in ('status','finishedPairs','failedPairs','progress')},
            'progress_samples':samples,'score_accuracy_claimed':False})
        print(json.dumps({k:measurements[-1][k] for k in ('submissions','pairs','start_response_seconds','completion_observed_seconds')}),flush=True)
    task=request(base,'/tasks',{'questionId':q,'taskName':'Synthetic missing-file recovery','submissionIds':[s['id'] for s in submissions[:3]]})['id']
    source=Path(submissions[2]['rawCodePath']).resolve()
    if not source.is_relative_to(upload_root.resolve()):
        raise ValueError('Refuse to temporarily move files outside this isolated synthetic upload root')
    moved=source.with_suffix(source.suffix+'.synthetic-check-hidden')
    source.rename(moved)
    try:
        request(base,f'/tasks/{task}/start',{})
        partial,_=terminal(base,task)
        failures=request(base,f'/tasks/{task}/failures')
        assert partial['status']=='PARTIAL' and partial['finishedPairs']==1 and partial['failedPairs']==2
        assert len(failures)==2 and all(not f['resolved'] for f in failures)
        before=request(base,f'/tasks/{task}/results')['items'][0]['id']
    finally:
        moved.rename(source)
    request(base,f'/tasks/{task}/start',{})
    recovered,_=terminal(base,task)
    after=request(base,f'/tasks/{task}/results')['items']
    resolved=request(base,f'/tasks/{task}/failures')
    assert recovered['status']=='FINISHED' and recovered['finishedPairs']==3 and recovered['failedPairs']==0
    assert before in {r['id'] for r in after} and all(f['resolved'] for f in resolved)
    report=request(base,f'/tasks/{task}/reports',{'format':'HTML','includeLowRiskPairs':True,'includeCodeSnippets':True,'includeThresholdExplanation':True})
    fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
        ROOT/'backend-springboot/src/main/java/com/coderisk/task/TaskService.java',
        ROOT/'backend-springboot/src/main/java/com/coderisk/task/TaskRepository.java',
        ROOT/'analysis-service-python/app/analyzers/token_similarity.py']}
    value={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'data_kind':'SELF_AUTHORED_SYNTHETIC_RUNTIME_FIXTURES',
        'database':'isolated persistent H2, Flyway V1–V5','analysis_service':'real local FastAPI, not mocked',
        'python_version':platform.python_version(),'platform':platform.platform(),'implementation_sha256':fingerprints,
        'implementation_sha256_lf':{key:hashlib.sha256((ROOT/key).read_text(encoding='utf-8').encode()).hexdigest() for key in fingerprints},
        'hash_convention':'implementation_sha256 hashes local bytes; implementation_sha256_lf normalizes CRLF/CR to LF for Git/checkouts.',
        'scale_runs':measurements,'partial_recovery':{'task_id':task,'before':partial,'after':recovered,
            'successful_result_id_preserved':before,'failure_history':resolved,'report_generated':report['status']},
        'limitations':['One local machine; no throughput/SLA claim.', '50 synthetic Python submissions is an execution check, not a language accuracy or student-data benchmark.',
                       'Service restart recovery verified separately by backend integration tests; no distributed deployment support.']}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as handle:json.dump(value,handle,ensure_ascii=False,indent=2);handle.write('\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:18080/api')
    parser.add_argument('--upload-root',type=Path,default=ROOT.parent/'.tmp/async-live/uploads')
    parser.add_argument('--output',type=Path,default=ROOT/'experiment/evidence/async-execution-20261009/runtime.json')
    args=parser.parse_args()
    run(args.base_url,args.upload_root,args.output)
