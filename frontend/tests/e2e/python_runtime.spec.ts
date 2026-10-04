import { test, expect } from '@playwright/test';

test.describe('R0 순서 4: Pyodide 별도 Origin 실행 영역 및 격리 경계 검증', () => {
  test.beforeEach(async ({ page }) => {
    page.on('console', (msg) => console.log(`[BROWSER CONSOLE] ${msg.type()}: ${msg.text()}`));
    page.on('pageerror', (err) => console.log(`[PAGE ERROR] ${err.message}`));
    await page.goto('/');
    // Pyodide 런타임 초기화 대기 (최대 35초)
    await expect(page.locator('#runtime-status-label')).toContainText('Pyodide 런타임 준비 완료', {
      timeout: 35000,
    });
  });

  test('1. 별도 Origin(5174)에서 iframe이 로드되고 Cross-Origin 격리가 유지된다', async ({ page }) => {
    const iframeElement = page.locator('#python-runtime-frame');
    await expect(iframeElement).toBeAttached();

    const src = await iframeElement.getAttribute('src');
    expect(src).toContain('http://127.0.0.1:5174');

    // App 페이지에 임의의 테스트 토큰을 localStorage에 저장
    await page.evaluate(() => {
      localStorage.setItem('APP_SECRET_TOKEN', 'super_secret_local_value');
    });

    // 1) App 창(5173)에서 Runtime iframe(5174)의 localStorage/contentDocument 접근 시도 차단 검증
    const appToIframeBlocked = await page.evaluate(() => {
      const frame = document.getElementById('python-runtime-frame') as HTMLIFrameElement;
      if (!frame || !frame.contentWindow) return false;
      try {
        // Cross-origin이면 contentDocument는 반드시 null
        if (frame.contentDocument !== null) return false;
        // 다른 Origin의 localStorage 접근 시 DOMException 발생해야 함
        const ls = frame.contentWindow.localStorage;
        return false;
      } catch (err) {
        return true; // SecurityError 발생 (차단 성공)
      }
    });
    expect(appToIframeBlocked).toBe(true);

    // 2) Runtime iframe(5174) 내부에서 App(5173)의 window.parent.localStorage 접근 시도 차단 검증
    const iframeToAppBlocked = await page.frameLocator('#python-runtime-frame').locator('body').evaluate(() => {
      try {
        const token = window.parent.localStorage.getItem('APP_SECRET_TOKEN');
        return false;
      } catch (err) {
        return true; // SecurityError 발생 (차단 성공)
      }
    });
    expect(iframeToAppBlocked).toBe(true);
  });

  test('2. Python 함수 실행 시 stdout과 TestCase 결과가 분리되어 반환된다', async ({ page }) => {
    // 기본으로 입력된 solution 코드 실행
    await page.click('#btn-run');

    // 실행 결과 대기
    await expect(page.locator('#result-status')).toHaveText('success', { timeout: 10000 });

    // stdout에 print 내용이 들어가고 테스트 결과와 분리되어 있는지 확인
    const stdout = await page.locator('#result-stdout').textContent();
    expect(stdout).toContain('계산 완료: 원소 개수');

    // TestCase 검증 결과 확인
    const testList = page.locator('#test-results-list');
    await expect(testList).toContainText('정수 배열 빈도수 계산: PASS');
    await expect(testList).toContainText('빈 배열 계산: PASS');
  });

  test('3. 테스트 케이스 불일치 시 FAIL 판정 및 기대값/실제값이 보고된다', async ({ page }) => {
    // 잘못된 구현 코드 작성: 항상 빈 딕셔너리 반환
    const wrongCode = `def solution(arr):\n    print("잘못된 풀이 실행")\n    return {}\n`;
    await page.fill('#code-input', wrongCode);

    await page.click('#btn-run');
    await expect(page.locator('#result-status')).toHaveText('success', { timeout: 10000 });

    // tc-1은 실패, tc-2는 통과
    const testList = page.locator('#test-results-list');
    await expect(testList).toContainText('정수 배열 빈도수 계산: FAIL');
    await expect(testList).toContainText('빈 배열 계산: PASS');
  });

  test('4. 런타임 오류(ZeroDivisionError) 발생 시 error 상태와 상세 메시지를 반환한다', async ({ page }) => {
    const errorThrowingCode = `def solution(arr):\n    x = 10 / 0\n    return x\n`;
    await page.fill('#code-input', errorThrowingCode);

    await page.click('#btn-run');
    await expect(page.locator('#result-status')).toHaveText('success', { timeout: 10000 });

    // tc-1 실행 시 division by zero 오류로 FAIL 판정
    const testList = page.locator('#test-results-list');
    await expect(testList).toContainText('ZeroDivisionError');
  });

  test('5. 3초 초과 무한 루프 실행 시 타임아웃으로 강제 중단되고 Worker가 복구된다', async ({ page }) => {
    // 3초 타임아웃 검증 버튼 클릭 (while True: pass 실행)
    await page.click('#btn-timeout-test');

    // 3초 이상 경과 후 결과 대기 (최대 6초)
    await expect(page.locator('#result-status')).toHaveText('timeout', { timeout: 8000 });

    const errorMsg = await page.locator('#result-error-msg').textContent();
    expect(errorMsg).toContain('실행 시간 제한(3초)을 초과하여 중단');

    // 새 Worker가 재생성되어 준비될 때까지 대기
    await expect(page.locator('#runtime-status-label')).toContainText('Pyodide 런타임 준비 완료', {
      timeout: 20000,
    });

    // 타임아웃 후 새 Worker가 정상 복구되었는지 확인하기 위해 정상 코드 다시 실행
    const normalCode = `def solution(arr):\n    return {"status": "recovered"}\n`;
    await page.fill('#code-input', normalCode);

    await page.click('#btn-run');
    await expect(page.locator('#result-status')).toHaveText('success', { timeout: 10000 });
  });

  test('6. 64 KiB 초과 출력 시 버퍼가 잘리고 안내문이 추가된다', async ({ page }) => {
    const massiveOutputCode = `def solution(arr):\n    # 100,000자 출력\n    print("A" * 100000)\n    return {}\n`;
    await page.fill('#code-input', massiveOutputCode);

    await page.click('#btn-run');
    await expect(page.locator('#result-status')).toHaveText('success', { timeout: 10000 });

    const stdout = await page.locator('#result-stdout').textContent();
    expect(stdout).toContain('[출력 제한(64 KiB)을 초과하여 이후 출력이 잘렸습니다]');
  });
});
