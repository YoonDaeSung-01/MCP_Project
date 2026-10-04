/**
 * Python Runtime 및 Iframe 통신 프로토콜 타입 정의
 * 
 * 기준: docs/ARCHITECTURE.md §11 (Python Runtime 계약) 및 §12 (실행 제한)
 * PRD: docs/PRD.md FR-09 (기초 Python Practice)
 */

export const RUNTIME_VERSION = '0.26.4';
export const DEFAULT_TIMEOUT_MS = 3000; // 작은 Python Function 실행 제한: 3초
export const MAX_OUTPUT_BYTES = 64 * 1024; // Python 출력 제한: 64 KiB
export const MAX_PAYLOAD_BYTES = 100 * 1024; // 요청 크기 제한: 100 KiB

export interface TestCase {
  id: string;
  name?: string;
  function_name?: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
  expected: unknown;
}

export interface TestCaseResult {
  id: string;
  name?: string;
  passed: boolean;
  actual?: unknown;
  expected: unknown;
  error?: string;
}

export type ExecutionStatus = 'success' | 'error' | 'timeout' | 'cancelled';

export interface ExecuteCodePayload {
  code: string;
  entry_function?: string;
  test_cases?: TestCase[];
  timeout_ms?: number;
}

export interface ExecuteResultPayload {
  status: ExecutionStatus;
  stdout: string;
  stderr: string;
  error_message?: string;
  test_results?: TestCaseResult[];
  execution_time_ms: number;
}

// Parent -> Iframe 메시지
export type ParentToIframeMessage =
  | {
      type: 'RUNTIME_PING';
      request_id: string;
      runtime_version?: string;
    }
  | {
      type: 'EXECUTE_CODE';
      request_id: string;
      runtime_version: string;
      payload: ExecuteCodePayload;
    }
  | {
      type: 'CANCEL_EXECUTION';
      request_id: string;
      runtime_version: string;
    };

// Iframe -> Parent 메시지
export type IframeToParentMessage =
  | {
      type: 'RUNTIME_READY';
      runtime_version: string;
    }
  | {
      type: 'RUNTIME_PONG';
      request_id: string;
      runtime_version: string;
    }
  | {
      type: 'EXECUTE_RESULT';
      request_id: string;
      runtime_version: string;
      payload: ExecuteResultPayload;
    }
  | {
      type: 'CANCEL_ACK';
      request_id: string;
      runtime_version: string;
    }
  | {
      type: 'RUNTIME_ERROR';
      request_id?: string;
      runtime_version: string;
      error: string;
    };
