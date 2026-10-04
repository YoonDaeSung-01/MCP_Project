/**
 * Python Runtime Host Script (Iframe 내부 실행)
 *
 * 기준:
 * - docs/ARCHITECTURE.md §11 (Python Runtime 계약 - "Runtime 준비 시간은 실제 Code 실행 제한과 분리한다")
 * - docs/ARCHITECTURE.md §12 (실행 제한: 작은 Function 3초, 출력 64 KiB)
 * - docs/PRD.md FR-09 (기초 Python Practice)
 */

(function () {
  const RUNTIME_VERSION = '0.26.4';
  const MAX_TIMEOUT_MS = 3000; // 작은 Python Function 실행 제한: 3초
  const MAX_PAYLOAD_BYTES = 100 * 1024; // 100 KiB

  const ALLOWED_APP_ORIGINS = new Set([
    'http://127.0.0.1:5173',
    'http://localhost:5173',
  ]);

  let explicitParentOrigin = null;
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const parentOriginParam = urlParams.get('parent_origin');
    if (parentOriginParam) {
      const parsed = new URL(parentOriginParam);
      if (parsed.hostname === '127.0.0.1' || parsed.hostname === 'localhost') {
        ALLOWED_APP_ORIGINS.add(parsed.origin);
        explicitParentOrigin = parsed.origin;
      }
    }
  } catch (e) {
    console.warn('[Runtime] Failed to parse parent_origin param:', e);
  }

  let currentWorker = null;
  let activeRequestId = null;
  let activeTimeoutMs = MAX_TIMEOUT_MS;
  let executionTimer = null;
  let isWorkerReady = false;

  const statusEl = document.getElementById('status');

  function updateStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function notifyParent(msg) {
    if (!window.parent || window.parent === window) return;
    if (explicitParentOrigin) {
      window.parent.postMessage(msg, explicitParentOrigin);
      return;
    }
    ALLOWED_APP_ORIGINS.forEach((origin) => {
      try {
        window.parent.postMessage(msg, origin);
      } catch (e) {
        // ignore
      }
    });
  }

  function createWorker() {
    if (currentWorker) {
      try {
        currentWorker.terminate();
      } catch (e) {
        console.error('[Runtime] Error terminating worker:', e);
      }
    }

    isWorkerReady = false;
    updateStatus('Creating worker...');

    currentWorker = new Worker('./worker.js');

    currentWorker.onmessage = function (event) {
      const data = event.data || {};
      const { type, request_id, payload, error } = data;

      if (type === 'INIT_SUCCESS') {
        isWorkerReady = true;
        updateStatus('Runtime Ready');
        notifyParent({
          type: 'RUNTIME_READY',
          runtime_version: RUNTIME_VERSION,
        });
        return;
      }

      if (type === 'INIT_ERROR') {
        isWorkerReady = false;
        updateStatus('Init Error: ' + error);
        notifyParent({
          type: 'RUNTIME_ERROR',
          request_id,
          runtime_version: RUNTIME_VERSION,
          error: 'Failed to initialize Pyodide: ' + error,
        });
        return;
      }

      if (type === 'PONG') {
        notifyParent({
          type: 'RUNTIME_PONG',
          request_id,
          runtime_version: RUNTIME_VERSION,
        });
        return;
      }

      // 실제 코드 실행 개시 알림 수신 시 3초 타이머 시작 (준비 시간과 실행 시간 분리)
      if (type === 'EXECUTE_STARTED') {
        if (activeRequestId === request_id) {
          clearTimeout(executionTimer);
          executionTimer = setTimeout(() => {
            if (activeRequestId === request_id) {
              const timedOutId = activeRequestId;
              activeRequestId = null;
              executionTimer = null;

              // Worker 강제 중단 및 즉시 재생성 (Worker recreate)
              createWorker();

              notifyParent({
                type: 'EXECUTE_RESULT',
                request_id: timedOutId,
                runtime_version: RUNTIME_VERSION,
                payload: {
                  status: 'timeout',
                  stdout: '',
                  stderr: '',
                  error_message: `실행 시간 제한(${activeTimeoutMs / 1000}초)을 초과하여 중단되었습니다.`,
                  execution_time_ms: activeTimeoutMs,
                },
              });
            }
          }, activeTimeoutMs);
        }
        return;
      }

      if (type === 'EXECUTE_RESULT') {
        if (activeRequestId === request_id) {
          clearTimeout(executionTimer);
          executionTimer = null;
          activeRequestId = null;
          updateStatus('Idle');

          notifyParent({
            type: 'EXECUTE_RESULT',
            request_id,
            runtime_version: RUNTIME_VERSION,
            payload,
          });
        }
      }
    };

    currentWorker.onerror = function (err) {
      console.error('[Runtime Worker Error]', err);
      if (activeRequestId) {
        clearTimeout(executionTimer);
        executionTimer = null;
        const reqId = activeRequestId;
        activeRequestId = null;

        notifyParent({
          type: 'EXECUTE_RESULT',
          request_id: reqId,
          runtime_version: RUNTIME_VERSION,
          payload: {
            status: 'error',
            stdout: '',
            stderr: '',
            error_message: 'Worker execution error: ' + (err.message || 'Unknown error'),
            execution_time_ms: 0,
          },
        });
      }
      createWorker();
    };

    currentWorker.postMessage({
      type: 'INIT',
      request_id: 'init_' + Date.now(),
      runtime_version: RUNTIME_VERSION,
    });
  }

  window.addEventListener('message', function (event) {
    if (!ALLOWED_APP_ORIGINS.has(event.origin)) {
      console.warn('[Runtime] Rejected message from untrusted origin:', event.origin);
      return;
    }

    const data = event.data;
    if (!data || typeof data !== 'object') return;

    const { type, request_id, runtime_version, payload } = data;

    try {
      const rawLength = JSON.stringify(data).length;
      if (rawLength > MAX_PAYLOAD_BYTES) {
        event.source.postMessage({
          type: 'EXECUTE_RESULT',
          request_id: request_id || 'unknown',
          runtime_version: RUNTIME_VERSION,
          payload: {
            status: 'error',
            stdout: '',
            stderr: '',
            error_message: `Payload size (${rawLength} bytes) exceeds limit (${MAX_PAYLOAD_BYTES} bytes).`,
            execution_time_ms: 0,
          },
        }, event.origin);
        return;
      }
    } catch (e) {
      // ignore
    }

    if (type === 'RUNTIME_PING') {
      if (isWorkerReady) {
        event.source.postMessage({
          type: 'RUNTIME_READY',
          runtime_version: RUNTIME_VERSION,
        }, event.origin);
      }
      event.source.postMessage({
        type: 'RUNTIME_PONG',
        request_id: request_id || 'ping',
        runtime_version: RUNTIME_VERSION,
      }, event.origin);
      return;
    }

    if (type === 'CANCEL_EXECUTION') {
      if (activeRequestId && activeRequestId === request_id) {
        clearTimeout(executionTimer);
        executionTimer = null;
        const cancelledId = activeRequestId;
        activeRequestId = null;

        createWorker();

        event.source.postMessage({
          type: 'CANCEL_ACK',
          request_id: cancelledId,
          runtime_version: RUNTIME_VERSION,
        }, event.origin);

        event.source.postMessage({
          type: 'EXECUTE_RESULT',
          request_id: cancelledId,
          runtime_version: RUNTIME_VERSION,
          payload: {
            status: 'cancelled',
            stdout: '',
            stderr: '',
            error_message: '사용자에 의해 실행이 중단되었습니다.',
            execution_time_ms: 0,
          },
        }, event.origin);
      } else {
        event.source.postMessage({
          type: 'CANCEL_ACK',
          request_id: request_id,
          runtime_version: RUNTIME_VERSION,
        }, event.origin);
      }
      return;
    }

    if (type === 'EXECUTE_CODE') {
      if (!payload || typeof payload.code !== 'string') {
        event.source.postMessage({
          type: 'EXECUTE_RESULT',
          request_id,
          runtime_version: RUNTIME_VERSION,
          payload: {
            status: 'error',
            stdout: '',
            stderr: '',
            error_message: 'Invalid payload: code is required.',
            execution_time_ms: 0,
          },
        }, event.origin);
        return;
      }

      if (activeRequestId) {
        event.source.postMessage({
          type: 'EXECUTE_RESULT',
          request_id,
          runtime_version: RUNTIME_VERSION,
          payload: {
            status: 'error',
            stdout: '',
            stderr: '',
            error_message: 'Runtime is busy with another execution.',
            execution_time_ms: 0,
          },
        }, event.origin);
        return;
      }

      activeRequestId = request_id;
      activeTimeoutMs = Math.min(
        typeof payload.timeout_ms === 'number' && payload.timeout_ms > 0
          ? payload.timeout_ms
          : MAX_TIMEOUT_MS,
        MAX_TIMEOUT_MS
      );

      updateStatus(`Running (${request_id})...`);

      // Worker 초기화/준비 지연에 대비한 20초 안전 타이머 (EXECUTE_STARTED 시 3초 타이머로 전환됨)
      clearTimeout(executionTimer);
      executionTimer = setTimeout(() => {
        if (activeRequestId === request_id) {
          const timedOutId = activeRequestId;
          activeRequestId = null;
          executionTimer = null;
          createWorker();
          notifyParent({
            type: 'EXECUTE_RESULT',
            request_id: timedOutId,
            runtime_version: RUNTIME_VERSION,
            payload: {
              status: 'timeout',
              stdout: '',
              stderr: '',
              error_message: '초기화 준비 시간 초과(20초)로 중단되었습니다.',
              execution_time_ms: 20000,
            },
          });
        }
      }, 20000);

      // Worker에게 실행 위임
      currentWorker.postMessage({
        type: 'EXECUTE',
        request_id,
        runtime_version: RUNTIME_VERSION,
        payload,
      });
    }
  });

  createWorker();
})();
