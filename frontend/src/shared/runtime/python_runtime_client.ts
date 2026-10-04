/**
 * Python Runtime Client (Parent App -> Runtime Iframe 통신)
 *
 * 기준:
 * - docs/ARCHITECTURE.md §11 (Python Runtime 계약)
 * - docs/ARCHITECTURE.md §12 (실행 제한: 작은 Function 3초, 출력 64 KiB)
 * - docs/PRD.md FR-09 (기초 Python Practice)
 */

import {
  DEFAULT_TIMEOUT_MS,
  ExecuteCodePayload,
  ExecuteResultPayload,
  IframeToParentMessage,
  ParentToIframeMessage,
  RUNTIME_VERSION,
  TestCase,
} from './types';

export interface PythonRuntimeClientOptions {
  runtimeOrigin?: string;
  runtimePath?: string;
  appOrigin?: string;
  container?: HTMLElement;
}

interface PendingExecution {
  resolve: (result: ExecuteResultPayload) => void;
  reject: (reason: unknown) => void;
  clientTimeoutTimer: ReturnType<typeof setTimeout>;
}

export class PythonRuntimeClient {
  private readonly runtimeOrigin: string;
  private readonly runtimePath: string;
  private readonly appOrigin: string;
  private iframe: HTMLIFrameElement | null = null;
  private isReady = false;
  private readyPromise: Promise<void> | null = null;
  private readyResolve: (() => void) | null = null;
  private pendingExecutions = new Map<string, PendingExecution>();
  private messageListener: ((event: MessageEvent) => void) | null = null;

  constructor(options: PythonRuntimeClientOptions = {}) {
    this.runtimeOrigin = options.runtimeOrigin || 'http://127.0.0.1:5174';
    this.runtimePath = options.runtimePath || '/';
    this.appOrigin = options.appOrigin || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:5173');

    if (typeof window !== 'undefined') {
      this.initIframe(options.container);
    }
  }

  private initIframe(container?: HTMLElement): void {
    this.readyPromise = new Promise((resolve) => {
      this.readyResolve = resolve;
    });

    const iframe = document.createElement('iframe');
    iframe.id = 'python-runtime-frame';
    iframe.style.position = 'absolute';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.opacity = '0';
    iframe.style.pointerEvents = 'none';
    iframe.style.border = 'none';

    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');

    const url = new URL(this.runtimePath, this.runtimeOrigin);
    url.searchParams.set('parent_origin', this.appOrigin);
    iframe.src = url.toString();

    this.messageListener = (event: MessageEvent) => {
      this.handleMessage(event);
    };
    window.addEventListener('message', this.messageListener);

    iframe.onload = () => {
      this.ping();
    };

    const target = container || document.body;
    target.appendChild(iframe);
    this.iframe = iframe;
  }

  private handleMessage(event: MessageEvent): void {
    if (event.origin !== this.runtimeOrigin) {
      return;
    }

    if (this.iframe && event.source !== this.iframe.contentWindow) {
      return;
    }

    const data = event.data as IframeToParentMessage;
    if (!data || typeof data !== 'object') {
      return;
    }

    if (data.type === 'RUNTIME_READY' || data.type === 'RUNTIME_PONG') {
      this.isReady = true;
      if (this.readyResolve) {
        this.readyResolve();
        this.readyResolve = null;
      }
      return;
    }

    if (data.type === 'EXECUTE_RESULT') {
      const pending = this.pendingExecutions.get(data.request_id);
      if (pending) {
        clearTimeout(pending.clientTimeoutTimer);
        this.pendingExecutions.delete(data.request_id);
        pending.resolve(data.payload);
      }
      return;
    }

    if (data.type === 'CANCEL_ACK') {
      return;
    }

    if (data.type === 'RUNTIME_ERROR') {
      if (data.request_id) {
        const pending = this.pendingExecutions.get(data.request_id);
        if (pending) {
          clearTimeout(pending.clientTimeoutTimer);
          this.pendingExecutions.delete(data.request_id);
          pending.reject(new Error(data.error));
        }
      }
    }
  }

  private ping(): void {
    if (!this.iframe?.contentWindow) return;
    const msg: ParentToIframeMessage = {
      type: 'RUNTIME_PING',
      request_id: 'ping_' + Date.now(),
      runtime_version: RUNTIME_VERSION,
    };
    this.iframe.contentWindow.postMessage(msg, this.runtimeOrigin);
  }

  public async waitForReady(timeoutMs = 25000): Promise<void> {
    if (this.isReady) return;

    const timeout = new Promise<void>((_, reject) => {
      setTimeout(() => {
        if (!this.isReady) {
          reject(new Error(`Runtime failed to initialize within ${timeoutMs}ms.`));
        }
      }, timeoutMs);
    });

    return Promise.race([this.readyPromise as Promise<void>, timeout]);
  }

  public async executeCode(
    code: string,
    options: {
      entryFunction?: string;
      testCases?: TestCase[];
      timeoutMs?: number;
    } = {}
  ): Promise<ExecuteResultPayload> {
    await this.waitForReady();

    if (!this.iframe?.contentWindow) {
      throw new Error('Runtime iframe is not available.');
    }

    const requestId = 'exec_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8);
    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

    const payload: ExecuteCodePayload = {
      code,
      entry_function: options.entryFunction,
      test_cases: options.testCases,
      timeout_ms: timeoutMs,
    };

    const msg: ParentToIframeMessage = {
      type: 'EXECUTE_CODE',
      request_id: requestId,
      runtime_version: RUNTIME_VERSION,
      payload,
    };

    return new Promise<ExecuteResultPayload>((resolve, reject) => {
      const clientTimeoutTimer = setTimeout(() => {
        if (this.pendingExecutions.has(requestId)) {
          this.pendingExecutions.delete(requestId);
          this.cancelExecution(requestId);
          resolve({
            status: 'timeout',
            stdout: '',
            stderr: '',
            error_message: `클라이언트 제한 시간(${timeoutMs + 4000}ms) 초과로 중단되었습니다.`,
            execution_time_ms: timeoutMs,
          });
        }
      }, timeoutMs + 4000);

      this.pendingExecutions.set(requestId, {
        resolve,
        reject,
        clientTimeoutTimer,
      });

      this.iframe!.contentWindow!.postMessage(msg, this.runtimeOrigin);
    });
  }

  public cancelExecution(requestId: string): void {
    if (!this.iframe?.contentWindow) return;

    const msg: ParentToIframeMessage = {
      type: 'CANCEL_EXECUTION',
      request_id: requestId,
      runtime_version: RUNTIME_VERSION,
    };

    this.iframe.contentWindow.postMessage(msg, this.runtimeOrigin);
  }

  public destroy(): void {
    if (this.messageListener) {
      window.removeEventListener('message', this.messageListener);
      this.messageListener = null;
    }

    this.pendingExecutions.forEach((pending) => {
      clearTimeout(pending.clientTimeoutTimer);
      pending.reject(new Error('PythonRuntimeClient destroyed'));
    });
    this.pendingExecutions.clear();

    if (this.iframe && this.iframe.parentNode) {
      this.iframe.parentNode.removeChild(this.iframe);
      this.iframe = null;
    }

    this.isReady = false;
  }
}
