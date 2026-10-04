/**
 * Pyodide Web Worker
 *
 * 기준:
 * - docs/ARCHITECTURE.md §11 (Python Runtime 계약 - "Runtime 준비 시간은 실제 Code 실행 제한과 분리한다")
 * - docs/ARCHITECTURE.md §12 (실행 제한: 작은 Function 3초, 출력 64 KiB)
 * - docs/PRD.md FR-09 (기초 Python Practice)
 */

const PYODIDE_CDN_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
const PYODIDE_INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/';
const RUNTIME_VERSION = '0.26.4';
const MAX_OUTPUT_BYTES = 64 * 1024; // 64 KiB 제한

let pyodide = null;
let pyodideInitPromise = null;

let stdoutBuffer = '';
let stderrBuffer = '';
let stdoutTruncated = false;
let stderrTruncated = false;

function appendToBuffer(text, isError = false) {
  const isTruncated = isError ? stderrTruncated : stdoutTruncated;
  if (isTruncated) return;

  const added = String(text);
  const currentBuffer = isError ? stderrBuffer : stdoutBuffer;
  const currentBytes = new TextEncoder().encode(currentBuffer).length;
  const addedBytes = new TextEncoder().encode(added).length;

  if (currentBytes + addedBytes > MAX_OUTPUT_BYTES) {
    const remaining = MAX_OUTPUT_BYTES - currentBytes;
    if (remaining > 0) {
      const truncatedSlice = added.slice(0, remaining);
      if (isError) {
        stderrBuffer += truncatedSlice + '\n[출력 제한(64 KiB)을 초과하여 오류 출력이 잘렸습니다]';
        stderrTruncated = true;
      } else {
        stdoutBuffer += truncatedSlice + '\n[출력 제한(64 KiB)을 초과하여 이후 출력이 잘렸습니다]';
        stdoutTruncated = true;
      }
    } else {
      if (isError) {
        stderrTruncated = true;
      } else {
        stdoutTruncated = true;
      }
    }
  } else {
    if (isError) {
      stderrBuffer += added;
    } else {
      stdoutBuffer += added;
    }
  }
}

async function initPyodide() {
  if (pyodide) return pyodide;
  if (pyodideInitPromise) return pyodideInitPromise;

  pyodideInitPromise = (async () => {
    importScripts(PYODIDE_CDN_URL);
    // @ts-ignore - loadPyodide is globally exposed by pyodide.js
    const loadedPyodide = await loadPyodide({
      indexURL: PYODIDE_INDEX_URL,
      stdout: (text) => appendToBuffer(text + '\n', false),
      stderr: (text) => appendToBuffer(text + '\n', true),
    });
    pyodide = loadedPyodide;
    return pyodide;
  })();

  return pyodideInitPromise;
}

function deepEqual(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (typeof a !== 'object' || typeof b !== 'object') return false;

  if (Array.isArray(a) !== Array.isArray(b)) return false;

  if (Array.isArray(a)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (!deepEqual(a[i], b[i])) return false;
    }
    return true;
  }

  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;

  for (const key of keysA) {
    if (!Object.prototype.hasOwnProperty.call(b, key)) return false;
    if (!deepEqual(a[key], b[key])) return false;
  }
  return true;
}

self.onmessage = async (event) => {
  const { type, request_id, runtime_version, payload } = event.data || {};

  if (type === 'PING') {
    self.postMessage({
      type: 'PONG',
      request_id,
      runtime_version: RUNTIME_VERSION,
    });
    return;
  }

  if (type === 'INIT') {
    try {
      await initPyodide();
      self.postMessage({
        type: 'INIT_SUCCESS',
        request_id,
        runtime_version: RUNTIME_VERSION,
      });
    } catch (err) {
      self.postMessage({
        type: 'INIT_ERROR',
        request_id,
        runtime_version: RUNTIME_VERSION,
        error: String(err && err.message ? err.message : err),
      });
    }
    return;
  }

  if (type === 'EXECUTE') {
    try {
      // 1. Pyodide 준비 보장 (준비 시간은 실행 제한 시간과 분리)
      const py = await initPyodide();

      // 준비 완료 후 실제 코드 실행 개시 알림 (타이머 시작 기준)
      self.postMessage({
        type: 'EXECUTE_STARTED',
        request_id,
        runtime_version: RUNTIME_VERSION,
      });

      const startTime = performance.now();
      stdoutBuffer = '';
      stderrBuffer = '';
      stdoutTruncated = false;
      stderrTruncated = false;

      const { code, entry_function, test_cases } = payload || {};
      if (typeof code !== 'string') {
        throw new Error('Code must be a string');
      }

      // 2. 매 실행마다 새 Namespace 생성 (ARCHITECTURE §11)
      const ns = py.globals.get('dict')();

      // 3. 사용자 Python 코드 실행
      py.runPython(code, { globals: ns });

      // 4. 테스트 케이스 실행 (제공된 경우)
      let testResults = undefined;

      if (Array.isArray(test_cases) && test_cases.length > 0) {
        testResults = [];
        for (const tc of test_cases) {
          const fnName = tc.function_name || entry_function;
          if (!fnName) {
            testResults.push({
              id: tc.id,
              name: tc.name,
              passed: false,
              expected: tc.expected,
              error: '호출할 함수 이름(entry_function 또는 function_name)이 지정되지 않았습니다.',
            });
            continue;
          }

          const pyFn = ns.get(fnName);
          if (!pyFn || typeof pyFn !== 'function') {
            testResults.push({
              id: tc.id,
              name: tc.name,
              passed: false,
              expected: tc.expected,
              error: `함수 '${fnName}'을(를) 찾을 수 없습니다.`,
            });
            continue;
          }

          try {
            const args = Array.isArray(tc.args) ? tc.args : [];
            let pyResult = null;
            if (tc.kwargs && typeof tc.kwargs === 'object') {
              const pyKwargs = py.toPy(tc.kwargs);
              pyResult = pyFn.callKwargs(...args, pyKwargs);
              if (pyKwargs && typeof pyKwargs.destroy === 'function') {
                pyKwargs.destroy();
              }
            } else {
              pyResult = pyFn(...args);
            }

            let jsResult = pyResult;
            if (pyResult && typeof pyResult.toJs === 'function') {
              jsResult = pyResult.toJs({ dict_converter: Object.fromEntries });
              if (typeof pyResult.destroy === 'function') {
                pyResult.destroy();
              }
            }

            const passed = deepEqual(jsResult, tc.expected);

            testResults.push({
              id: tc.id,
              name: tc.name,
              passed,
              actual: jsResult,
              expected: tc.expected,
            });
          } catch (callErr) {
            testResults.push({
              id: tc.id,
              name: tc.name,
              passed: false,
              expected: tc.expected,
              error: String(callErr && callErr.message ? callErr.message : callErr),
            });
          }
        }
      }

      // Namespace 정리
      if (ns && typeof ns.destroy === 'function') {
        ns.destroy();
      }

      const executionTimeMs = Math.round(performance.now() - startTime);

      self.postMessage({
        type: 'EXECUTE_RESULT',
        request_id,
        runtime_version: RUNTIME_VERSION,
        payload: {
          status: 'success',
          stdout: stdoutBuffer,
          stderr: stderrBuffer,
          test_results: testResults,
          execution_time_ms: executionTimeMs,
        },
      });
    } catch (err) {
      self.postMessage({
        type: 'EXECUTE_RESULT',
        request_id,
        runtime_version: RUNTIME_VERSION,
        payload: {
          status: 'error',
          stdout: stdoutBuffer,
          stderr: stderrBuffer,
          error_message: String(err && err.message ? err.message : err),
          execution_time_ms: 0,
        },
      });
    }
  }
};
