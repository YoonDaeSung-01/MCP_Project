import React, { useEffect, useRef, useState } from 'react';
import { PythonRuntimeClient } from '../shared/runtime/python_runtime_client';
import { ExecuteResultPayload } from '../shared/runtime/types';

export default function App(): React.ReactElement {
  const [code, setCode] = useState<string>(
    `def solution(arr):\n    # 각 원소의 빈도수(Hash)를 계산하여 반환\n    count = {}\n    for x in arr:\n        count[x] = count.get(x, 0) + 1\n    print(f"계산 완료: 원소 개수 {len(count)}개")\n    return count\n`
  );
  const [stdout, setStdout] = useState<string>('');
  const [status, setStatus] = useState<string>('초기화 대기 중...');
  const [isReady, setIsReady] = useState<boolean>(false);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<ExecuteResultPayload | null>(null);

  const clientRef = useRef<PythonRuntimeClient | null>(null);

  useEffect(() => {
    const client = new PythonRuntimeClient({
      runtimeOrigin: 'http://127.0.0.1:5174',
      appOrigin: window.location.origin,
    });
    clientRef.current = client;

    const onMessage = (event: MessageEvent) => {
      if (event.origin === 'http://127.0.0.1:5174' && event.data?.type === 'RUNTIME_READY') {
        setIsReady(true);
        setStatus('Pyodide 런타임 준비 완료 (Origin: 127.0.0.1:5174)');
      }
    };
    window.addEventListener('message', onMessage);

    client
      .waitForReady(30000)
      .then(() => {
        setIsReady(true);
        setStatus('Pyodide 런타임 준비 완료 (Origin: 127.0.0.1:5174)');
      })
      .catch((err) => {
        setStatus(`런타임 연결 실패: ${err.message}`);
      });

    return () => {
      window.removeEventListener('message', onMessage);
      client.destroy();
      clientRef.current = null;
    };
  }, []);

  const handleRun = async () => {
    if (!clientRef.current || !isReady) return;

    setIsRunning(true);
    setStatus('실행 중...');
    setResult(null);

    const testCases = [
      {
        id: 'tc-1',
        name: '정수 배열 빈도수 계산',
        function_name: 'solution',
        args: [[1, 2, 2, 3, 3, 3]],
        expected: { 1: 1, 2: 2, 3: 3 },
      },
      {
        id: 'tc-2',
        name: '빈 배열 계산',
        function_name: 'solution',
        args: [[]],
        expected: {},
      },
    ];

    try {
      const res = await clientRef.current.executeCode(code, {
        entryFunction: 'solution',
        testCases,
        timeoutMs: 3000,
      });

      setResult(res);
      setStdout(res.stdout);
      if (res.status === 'success') {
        const allPassed = res.test_results?.every((tc) => tc.passed);
        setStatus(allPassed ? '실행 완료: 모든 테스트 케이스 통과' : '실행 완료: 일부 테스트 케이스 실패');
      } else if (res.status === 'timeout') {
        setStatus('실행 실패: 3초 타임아웃 초과');
      } else if (res.status === 'cancelled') {
        setStatus('실행 취소: 사용자에 의해 중단됨');
      } else {
        setStatus(`실행 오류: ${res.error_message || '알 수 없는 오류'}`);
      }
    } catch (e: any) {
      setStatus(`실행 예외: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleTimeoutTest = async () => {
    if (!clientRef.current || !isReady) return;
    setIsRunning(true);
    setStatus('무한 루프 실행 중 (3초 타임아웃 검증)...');
    try {
      const res = await clientRef.current.executeCode('while True: pass', {
        timeoutMs: 3000,
      });
      setResult(res);
      setStatus(`타임아웃 검증 결과: 상태=${res.status}, 메시지=${res.error_message}`);
    } catch (e: any) {
      setStatus(`예외 발생: ${e.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>개인 학습 App - R0 Python Runtime 검증</h1>
      <p style={{ color: '#555' }}>
        별도 Origin(<code>http://127.0.0.1:5174</code>)의 iframe + Pyodide Web Worker 격리 검증 화면
      </p>

      <div style={{ padding: '0.8rem', background: '#eef2ff', borderRadius: '4px', marginBottom: '1rem' }}>
        <strong>상태: </strong>
        <span id="runtime-status-label">{status}</span>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <h3>Python Code Draft (Function: solution)</h3>
        <textarea
          id="code-input"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={10}
          style={{ width: '100%', fontFamily: 'monospace', fontSize: '14px', padding: '8px' }}
        />
      </div>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem' }}>
        <button
          id="btn-run"
          onClick={handleRun}
          disabled={!isReady || isRunning}
          style={{
            padding: '8px 16px',
            backgroundColor: isReady && !isRunning ? '#2563eb' : '#9ca3af',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: isReady && !isRunning ? 'pointer' : 'not-allowed',
          }}
        >
          {isRunning ? '실행 중...' : '실행 및 테스트케이스 검증'}
        </button>

        <button
          id="btn-timeout-test"
          onClick={handleTimeoutTest}
          disabled={!isReady || isRunning}
          style={{
            padding: '8px 16px',
            backgroundColor: isReady && !isRunning ? '#dc2626' : '#9ca3af',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: isReady && !isRunning ? 'pointer' : 'not-allowed',
          }}
        >
          3초 타임아웃 검증 (무한루프)
        </button>
      </div>

      {result && (
        <div style={{ marginTop: '1.5rem', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '1rem' }}>
          <h3>실행 결과 (소요 시간: {result.execution_time_ms}ms)</h3>
          <p>
            <strong>상태: </strong>
            <span id="result-status" style={{ fontWeight: 'bold' }}>{result.status}</span>
          </p>

          {result.error_message && (
            <div style={{ color: '#b91c1c', background: '#fef2f2', padding: '8px', borderRadius: '4px' }}>
              <strong>오류 메시지: </strong>
              <span id="result-error-msg">{result.error_message}</span>
            </div>
          )}

          <div style={{ marginTop: '1rem' }}>
            <h4>표준 출력 (stdout)</h4>
            <pre
              id="result-stdout"
              style={{ background: '#f8fafc', padding: '8px', borderRadius: '4px', maxHeight: '150px', overflow: 'auto' }}
            >
              {stdout || '(출력 없음)'}
            </pre>
          </div>

          {result.test_results && result.test_results.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <h4>Test Case 결과 ({result.test_results.filter((t) => t.passed).length}/{result.test_results.length} 통과)</h4>
              <ul id="test-results-list" style={{ listStyle: 'none', paddingLeft: 0 }}>
                {result.test_results.map((tc) => (
                  <li
                    key={tc.id}
                    style={{
                      padding: '8px',
                      marginBottom: '4px',
                      backgroundColor: tc.passed ? '#f0fdf4' : '#fef2f2',
                      borderLeft: `4px solid ${tc.passed ? '#16a34a' : '#dc2626'}`,
                    }}
                  >
                    <strong>{tc.name || tc.id}: </strong>
                    <span style={{ color: tc.passed ? '#16a34a' : '#dc2626' }}>
                      {tc.passed ? 'PASS' : 'FAIL'}
                    </span>
                    {!tc.passed && tc.error && <div style={{ color: '#dc2626' }}>오류: {tc.error}</div>}
                    {!tc.passed && !tc.error && (
                      <div style={{ fontSize: '12px', color: '#666' }}>
                        기대값: {JSON.stringify(tc.expected)} | 실제값: {JSON.stringify(tc.actual)}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
