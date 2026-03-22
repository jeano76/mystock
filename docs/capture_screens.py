#!/usr/bin/env python3
"""모든 주요 화면을 Selenium으로 캡처"""
import os, time, sys
sys.path.insert(0, '/home/hyuckjoolee/mystock/tests')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

BASE = "http://localhost:18765"
OUT  = "/home/hyuckjoolee/mystock/docs/screenshots"

def make_driver(w=1280, h=900):
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument(f'--window-size={w},{h}')
    return webdriver.Chrome(options=opts)

def wait(d): return WebDriverWait(d, 10)

def login(driver, user="helpuser"):
    driver.get(BASE)
    time.sleep(1.5)
    driver.execute_script("localStorage.clear()")
    driver.refresh(); time.sleep(1.5)
    w = wait(driver)
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
    inp = driver.find_elements(By.CSS_SELECTOR, ".auth-card input")
    inp[0].send_keys(user); inp[1].send_keys("Help1234!"); inp[2].send_keys("Help1234!")
    driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))
    time.sleep(0.8)

def inject_positions(driver):
    driver.execute_script("""
        localStorage.setItem('pfm3_positions', JSON.stringify([
            {id:'1',ticker:'AAPL',shares:20,buyPrice:150,divYield:0.6,account:'Brokerage'},
            {id:'2',ticker:'SCHD',shares:50,buyPrice:26,divYield:3.4,account:'Brokerage'},
            {id:'3',ticker:'T',shares:100,buyPrice:17,divYield:6.5,account:'Brokerage'},
            {id:'4',ticker:'MO',shares:80,buyPrice:43,divYield:8.2,account:'Brokerage'},
            {id:'5',ticker:'DVY',shares:30,buyPrice:120,divYield:3.8,account:'Roth IRA'},
            {id:'6',ticker:'005930.KS',shares:10,buyPrice:70000,divYield:2.1,account:'Brokerage'}
        ]));
        localStorage.setItem('pfm3_snapshots', JSON.stringify([
            {date:'2025-12-01',val:85000,gain:5000,pct:6.2},
            {date:'2026-01-01',val:92000,gain:7000,pct:8.1},
            {date:'2026-02-01',val:98000,gain:8000,pct:8.9},
            {date:'2026-03-01',val:105000,gain:10000,pct:10.5}
        ]));
    """)
    driver.refresh()
    wait(driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))
    time.sleep(1.5)

def el_ss(driver, css, name, wait_ms=0):
    if wait_ms: time.sleep(wait_ms/1000)
    try:
        el = driver.find_element(By.CSS_SELECTOR, css)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
        time.sleep(0.3)
        el.screenshot(f"{OUT}/{name}.png")
        print(f"  ✓ {name}")
    except Exception as e:
        print(f"  ✗ {name}: {e}")

def full_ss(driver, name, scroll_to=None):
    if scroll_to:
        try:
            el = driver.find_element(By.CSS_SELECTOR, scroll_to)
            driver.execute_script("arguments[0].scrollIntoView({block:'start'})", el)
            time.sleep(0.4)
        except: pass
    driver.save_screenshot(f"{OUT}/{name}.png")
    print(f"  ✓ {name}")

def click_tab(driver, text):
    tabs = driver.find_elements(By.CSS_SELECTOR, '.tab')
    t = next((x for x in tabs if text in x.text), None)
    if t: d.execute_script("arguments[0].click()", t); time.sleep(0.8)

def click_sb(driver, text):
    items = driver.find_elements(By.CSS_SELECTOR, '.sb-item')
    t = next((x for x in items if text in x.text), None)
    if t: d.execute_script("arguments[0].click()", t); time.sleep(0.8)

print("=== 화면 캡처 시작 ===\n")

# ─── 01. 회원가입 화면 ───────────────────────────────────────
print("[01] 회원가입 화면")
d = make_driver(960, 700)
try:
    d.get(BASE); time.sleep(1.5)
    d.execute_script("localStorage.clear()"); d.refresh(); time.sleep(1.5)
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
    full_ss(d, "01_register")
    el_ss(d, ".auth-card", "01b_register_card")
finally: d.quit()

# ─── 02. 로그인 화면 ───────────────────────────────────────
print("[02] 로그인 화면")
d = make_driver(960, 700)
try:
    d.get(BASE); time.sleep(1.5)
    d.execute_script("localStorage.clear()"); d.refresh(); time.sleep(1.5)
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
    # 계정 생성 후 로그아웃 → 로그인 화면
    inp = d.find_elements(By.CSS_SELECTOR, ".auth-card input")
    inp[0].send_keys("demouser2"); inp[1].send_keys("Demo1234!"); inp[2].send_keys("Demo1234!")
    d.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))
    time.sleep(0.5)
    # 로그아웃
    btns = d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
    logout_btn = next((b for b in btns if '로그아웃' in b.text or 'logout' in b.text.lower() or '⎋' in b.text), None)
    if logout_btn: d.execute_script('arguments[0].click()', logout_btn); time.sleep(0.8)
    else: d.execute_script("localStorage.removeItem('pfm3_session')"); d.refresh(); time.sleep(1.5)
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
    full_ss(d, "02_login")
finally: d.quit()

# ─── 03-12. 메인 앱 화면들 ───────────────────────────────────────
print("[03-16] 메인 앱 화면들")
d = make_driver(1280, 900)
try:
    login(d, "helpuser3"); inject_positions(d)
    
    # 03. Overview 전체
    print("[03] Overview")
    full_ss(d, "03_overview")
    
    # 04. Hero 섹션
    print("[04] Hero")
    el_ss(d, ".hero", "04_hero")
    
    # 05. 사이드바
    print("[05] 사이드바")
    el_ss(d, ".sidebar", "05_sidebar")
    
    # 06. 상단 바
    print("[06] 상단 바")
    el_ss(d, ".topbar", "06_topbar")

    # 07. Overview 차트 영역 (도넛+섹터)
    print("[07] 차트 영역")
    el_ss(d, ".charts-row", "07_charts_row")

    # 08. 배당 캘린더
    print("[08] 배당 캘린더")
    try:
        cal_card = next(c for c in d.find_elements(By.CSS_SELECTOR, '.chart-card') if c.find_elements(By.CSS_SELECTOR, '.div-cal'))
        d.execute_script("arguments[0].scrollIntoView({block:'center'})", cal_card)
        time.sleep(0.4); cal_card.screenshot(f"{OUT}/08_div_calendar.png"); print("  ✓ 08_div_calendar")
    except Exception as e: print(f"  ✗ 08_div_calendar: {e}")

    # 09. 포트폴리오 히스토리 (스냅샷)
    print("[09] 스냅샷 히스토리")
    try:
        snap_cards = d.find_elements(By.CSS_SELECTOR, '.snapshot-card, .bar-card')
        if snap_cards:
            d.execute_script("arguments[0].scrollIntoView({block:'center'})", snap_cards[0])
            time.sleep(0.4); snap_cards[0].screenshot(f"{OUT}/09_snapshot.png"); print("  ✓ 09_snapshot")
    except Exception as e: print(f"  ✗ 09_snapshot: {e}")

    # 10. Positions 탭
    print("[10] Positions 탭")
    click_tab(d, 'Positions')
    full_ss(d, "10_positions")

    # 11. 필터 pills
    print("[11] 필터")
    el_ss(d, ".filter-row", "11_filter_row")

    # 12. 포지션 추가 모달
    print("[12] 포지션 추가 모달")
    btns = d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-primary")
    if btns: d.execute_script('arguments[0].click()', btns[-1]); time.sleep(0.8)
    try:
        el_ss(d, ".modal", "12_add_modal")
        # 자동완성 입력
        inp = d.find_elements(By.CSS_SELECTOR, ".modal input")
        if inp:
            inp[0].send_keys("AAPL"); time.sleep(0.8)
            el_ss(d, ".modal", "12b_add_modal_autocomplete")
        esc = d.find_element(By.CSS_SELECTOR, ".close-x, .modal .btn-ghost")
        d.execute_script('arguments[0].click()', esc); time.sleep(0.5)
    except Exception as e: print(f"  ✗ 12_add_modal: {e}")

    # 13. API 설정 모달
    print("[13] API 설정")
    api_btn = next((b for b in d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn") if 'API' in b.text), None)
    if api_btn: d.execute_script('arguments[0].click()', api_btn); time.sleep(0.8)
    try:
        el_ss(d, ".modal", "13_api_modal")
        d.execute_script('arguments[0].click()', d.find_element(By.CSS_SELECTOR, '.close-x')); time.sleep(0.5)
    except Exception as e: print(f"  ✗ 13_api_modal: {e}")

    # 14. IO 모달 (내보내기/가져오기)
    print("[14] 내보내기/가져오기")
    io_btn = next((b for b in d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn") if '⇅' in b.text), None)
    if io_btn: d.execute_script('arguments[0].click()', io_btn); time.sleep(0.8)
    try:
        el_ss(d, ".modal", "14_io_modal")
        d.execute_script('arguments[0].click()', d.find_element(By.CSS_SELECTOR, '.close-x')); time.sleep(0.5)
    except Exception as e: print(f"  ✗ 14_io_modal: {e}")

    # 15. 알림 모달
    print("[15] 가격 알림")
    alert_btn = next((b for b in d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn") if '🔔' in b.text), None)
    if alert_btn: d.execute_script('arguments[0].click()', alert_btn); time.sleep(0.8)
    try:
        el_ss(d, ".modal", "15_alerts_modal")
        d.execute_script('arguments[0].click()', d.find_element(By.CSS_SELECTOR, '.close-x')); time.sleep(0.5)
    except Exception as e: print(f"  ✗ 15_alerts_modal: {e}")

    # 16. 매도 기록
    print("[16] 매도 기록")
    trade_btn = next((b for b in d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn") if '📊' in b.text), None)
    if trade_btn: d.execute_script('arguments[0].click()', trade_btn); time.sleep(0.8)
    try:
        el_ss(d, ".modal", "16_trades_modal")
        d.execute_script('arguments[0].click()', d.find_element(By.CSS_SELECTOR, '.close-x')); time.sleep(0.5)
    except Exception as e: print(f"  ✗ 16_trades_modal: {e}")

    # 17. 미래 예측 뷰
    print("[17] 미래 예측")
    click_tab(d, '미래 예측')
    time.sleep(0.5); full_ss(d, "17_forecast")

    # 18. 리포트 뷰
    print("[18] 리포트")
    click_tab(d, '리포트')
    time.sleep(0.5); full_ss(d, "18_report_top")
    # 세금 섹션 캡처
    try:
        tax = d.find_element(By.CSS_SELECTOR, ".tax-split")
        d.execute_script("arguments[0].scrollIntoView({block:'center'})", tax)
        time.sleep(0.4)
        # 부모 report-sec 캡처
        sec = tax.find_element(By.XPATH, "./..")
        sec.screenshot(f"{OUT}/18b_report_tax.png"); print("  ✓ 18b_report_tax")
    except Exception as e: print(f"  ✗ 18b_report_tax: {e}")
    # 건전성 섹션
    try:
        health = d.find_element(By.CSS_SELECTOR, ".health-grid")
        d.execute_script("arguments[0].scrollIntoView({block:'center'})", health)
        time.sleep(0.4)
        health.find_element(By.XPATH, "./..").screenshot(f"{OUT}/18c_report_health.png")
        print("  ✓ 18c_report_health")
    except Exception as e: print(f"  ✗ 18c_report_health: {e}")

finally: d.quit()

# ─── 19. 모바일 뷰 ───────────────────────────────────────
print("[19] 모바일 뷰")
d = make_driver(375, 812)
try:
    login(d, "mobuser"); inject_positions(d)
    full_ss(d, "19_mobile_overview")
    # 사이드바 확장
    toggle = d.find_elements(By.CSS_SELECTOR, ".sb-toggle, .sidebar-toggle")
    if toggle: d.execute_script('arguments[0].click()', toggle[0]); time.sleep(0.5)
    full_ss(d, "19b_mobile_sidebar")
finally: d.quit()

# ─── 20. 라이트 테마 ───────────────────────────────────────
print("[20] 라이트 테마")
d = make_driver(1280, 900)
try:
    login(d, "lightuser"); inject_positions(d)
    theme_btn = next((b for b in d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn") if '☀️' in b.text or '🌙' in b.text), None)
    if theme_btn: d.execute_script('arguments[0].click()', theme_btn); time.sleep(0.5)
    full_ss(d, "20_light_theme")
finally: d.quit()

print("\n=== 완료 ===")
files = sorted(os.listdir(OUT))
print(f"총 {len(files)}개 파일:")
for f in files: print(f"  {f}")
