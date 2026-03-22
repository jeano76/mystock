#!/usr/bin/env python3
"""Capture all major screens in English UI"""
import os, time, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "http://localhost:18765"
OUT  = "/home/hyuckjoolee/mystock/docs/screenshots"

os.makedirs(OUT, exist_ok=True)

def make_driver(w=1280, h=900):
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument(f'--window-size={w},{h}')
    opts.add_argument('--lang=en-US')
    opts.add_argument('--accept-lang=en-US,en;q=0.9')
    return webdriver.Chrome(options=opts)

def wait(d): return WebDriverWait(d, 12)

def set_english(driver):
    """Set app language to English via localStorage"""
    driver.execute_script("localStorage.setItem('pfm3_lang','en')")

def login(driver, user="helpuser"):
    driver.get(BASE)
    time.sleep(1.5)
    driver.execute_script("localStorage.clear()")
    driver.execute_script("localStorage.setItem('pfm3_lang','en')")
    driver.refresh()
    time.sleep(1.5)
    w = wait(driver)
    # Wait for landing page form
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".landing-overlay, .auth-card")))
    time.sleep(0.5)
    # Switch to "Create Account" tab if on landing page
    tabs = driver.find_elements(By.CSS_SELECTOR, ".landing-tab")
    if tabs:
        create_tab = next((t for t in tabs if 'create' in t.text.lower() or 'account' in t.text.lower()), tabs[-1])
        driver.execute_script("arguments[0].click()", create_tab)
        time.sleep(0.3)
    # Fill registration form
    inputs = driver.find_elements(By.CSS_SELECTOR, ".landing-field input, .auth-card input")
    inputs[0].send_keys(user)
    inputs[1].send_keys("Help1234!")
    if len(inputs) > 2:
        inputs[2].send_keys("Help1234!")
    btn = driver.find_element(By.CSS_SELECTOR, ".landing-form-btn, .auth-card .btn-primary")
    driver.execute_script("arguments[0].click()", btn)
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))
    time.sleep(1.0)

def inject_positions(driver):
    driver.execute_script("""
        localStorage.setItem('pfm3_lang','en');
        localStorage.setItem('pfm3_positions', JSON.stringify([
            {id:'1',ticker:'AAPL',shares:20,buyPrice:150,divYield:0.6,account:'Brokerage'},
            {id:'2',ticker:'SCHD',shares:50,buyPrice:26,divYield:3.4,account:'Brokerage'},
            {id:'3',ticker:'T',shares:100,buyPrice:17,divYield:6.5,account:'Brokerage'},
            {id:'4',ticker:'MO',shares:80,buyPrice:43,divYield:8.2,account:'Brokerage'},
            {id:'5',ticker:'DVY',shares:30,buyPrice:120,divYield:3.8,account:'Roth IRA'},
            {id:'6',ticker:'JEPI',shares:40,buyPrice:54,divYield:7.1,account:'Roth IRA'}
        ]));
        localStorage.setItem('pfm3_accounts', JSON.stringify(['Brokerage','Roth IRA']));
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

def el_ss(driver, css, name):
    try:
        el = driver.find_element(By.CSS_SELECTOR, css)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
        time.sleep(0.35)
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
    t = next((x for x in tabs if text.lower() in x.text.lower()), None)
    if t:
        driver.execute_script("arguments[0].click()", t)
        time.sleep(0.8)
    else:
        print(f"  ! tab not found: {text}")

def click_sb_action(driver, icon_or_label):
    """Click a sidebar action button by its icon or label text"""
    btns = driver.find_elements(By.CSS_SELECTOR, '.sb-action-btn')
    t = next((b for b in btns if icon_or_label in b.text), None)
    if t:
        driver.execute_script("arguments[0].click()", t)
        time.sleep(0.8)
    else:
        print(f"  ! sidebar action not found: {icon_or_label}")

def close_modal(driver):
    try:
        x = driver.find_element(By.CSS_SELECTOR, '.close-x')
        driver.execute_script("arguments[0].click()", x)
        time.sleep(0.5)
    except: pass

print("=== Screenshot Capture (English UI) ===\n")

# ─── 01. Landing / Register ──────────────────────────────────
print("[01] Landing page / Register")
d = make_driver(1280, 800)
try:
    d.get(BASE); time.sleep(1.5)
    d.execute_script("localStorage.clear()")
    d.execute_script("localStorage.setItem('pfm3_lang','en')")
    d.refresh(); time.sleep(1.5)
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".landing-overlay, .auth-card")))
    full_ss(d, "01_register")
    # Register card only
    try:
        card = d.find_element(By.CSS_SELECTOR, ".landing-right, .auth-card")
        card.screenshot(f"{OUT}/01b_register_card.png")
        print("  ✓ 01b_register_card")
    except Exception as e: print(f"  ✗ 01b_register_card: {e}")
finally: d.quit()

# ─── 02. Login screen ───────────────────────────────────────
print("[02] Login screen")
d = make_driver(1280, 800)
try:
    d.get(BASE); time.sleep(1.5)
    d.execute_script("localStorage.clear()")
    d.execute_script("localStorage.setItem('pfm3_lang','en')")
    d.refresh(); time.sleep(1.5)
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".landing-overlay, .auth-card")))
    # Create account first
    tabs = d.find_elements(By.CSS_SELECTOR, ".landing-tab")
    if tabs:
        create_tab = next((t for t in tabs if 'account' in t.text.lower()), tabs[-1])
        d.execute_script("arguments[0].click()", create_tab); time.sleep(0.3)
    inputs = d.find_elements(By.CSS_SELECTOR, ".landing-field input, .auth-card input")
    inputs[0].send_keys("demouser2"); inputs[1].send_keys("Demo1234!")
    if len(inputs) > 2: inputs[2].send_keys("Demo1234!")
    btn = d.find_element(By.CSS_SELECTOR, ".landing-form-btn, .auth-card .btn-primary")
    d.execute_script("arguments[0].click()", btn)
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app"))); time.sleep(0.5)
    # Logout via sidebar
    logout_btns = d.find_elements(By.CSS_SELECTOR, ".sb-action-btn.sb-logout, .sb-actions .sb-logout")
    if logout_btns:
        d.execute_script("arguments[0].click()", logout_btns[0]); time.sleep(1.0)
    else:
        d.execute_script("localStorage.removeItem('pfm3_session')"); d.refresh(); time.sleep(1.5)
        d.execute_script("localStorage.setItem('pfm3_lang','en')")
    wait(d).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".landing-overlay, .auth-card")))
    # Switch to Login tab
    tabs = d.find_elements(By.CSS_SELECTOR, ".landing-tab")
    if tabs:
        login_tab = next((t for t in tabs if 'login' in t.text.lower()), tabs[0])
        d.execute_script("arguments[0].click()", login_tab); time.sleep(0.3)
    full_ss(d, "02_login")
finally: d.quit()

# ─── 03-18. Main app ────────────────────────────────────────
print("[03-18] Main app screens")
d = make_driver(1280, 900)
try:
    login(d, "helpuser3")
    inject_positions(d)

    # 03. Overview full
    print("[03] Overview")
    full_ss(d, "03_overview")

    # 04. Hero section
    print("[04] Hero")
    el_ss(d, ".hero", "04_hero")

    # 05. Sidebar
    print("[05] Sidebar")
    el_ss(d, ".sidebar", "05_sidebar")

    # 06. Topbar
    print("[06] Topbar")
    el_ss(d, ".topbar", "06_topbar")

    # 07. Charts row
    print("[07] Charts row")
    el_ss(d, ".charts-row", "07_charts_row")

    # 08. Dividend calendar
    print("[08] Dividend calendar")
    try:
        chart_cards = d.find_elements(By.CSS_SELECTOR, '.chart-card')
        cal_card = next((c for c in chart_cards if c.find_elements(By.CSS_SELECTOR, '.div-cal,.div-cal-bars')), None)
        if cal_card:
            d.execute_script("arguments[0].scrollIntoView({block:'center'})", cal_card)
            time.sleep(0.4); cal_card.screenshot(f"{OUT}/08_div_calendar.png"); print("  ✓ 08_div_calendar")
        else: print("  ✗ 08_div_calendar: card not found")
    except Exception as e: print(f"  ✗ 08_div_calendar: {e}")

    # 09. Snapshot history
    print("[09] Snapshot")
    try:
        snap = d.find_elements(By.CSS_SELECTOR, '.snapshot-card,.bar-card,.chart-card')
        if snap:
            d.execute_script("arguments[0].scrollIntoView({block:'center'})", snap[-1])
            time.sleep(0.4); snap[-1].screenshot(f"{OUT}/09_snapshot.png"); print("  ✓ 09_snapshot")
    except Exception as e: print(f"  ✗ 09_snapshot: {e}")

    # 10. Positions tab
    print("[10] Positions tab")
    click_tab(d, 'Positions')
    full_ss(d, "10_positions")

    # 11. Filter row
    print("[11] Filter row")
    el_ss(d, ".filter-row,.pills", "11_filter_row")

    # 12. Add position modal
    print("[12] Add position modal")
    btns = d.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-primary")
    if btns: d.execute_script('arguments[0].click()', btns[-1]); time.sleep(0.8)
    try:
        el_ss(d, ".modal", "12_add_modal")
        inp = d.find_elements(By.CSS_SELECTOR, ".modal input")
        if inp:
            inp[0].send_keys("AAPL"); time.sleep(0.8)
            el_ss(d, ".modal", "12b_add_modal_autocomplete")
        close_modal(d)
    except Exception as e: print(f"  ✗ 12_add_modal: {e}")

    # 13. API settings (sidebar action)
    print("[13] API settings")
    click_sb_action(d, '⚙️')
    try:
        el_ss(d, ".modal", "13_api_modal")
        close_modal(d)
    except Exception as e: print(f"  ✗ 13_api_modal: {e}")

    # 14. Import/Export (sidebar action)
    print("[14] Import / Export")
    click_sb_action(d, '⇅')
    try:
        el_ss(d, ".modal", "14_io_modal")
        close_modal(d)
    except Exception as e: print(f"  ✗ 14_io_modal: {e}")

    # 15. Alerts (sidebar action)
    print("[15] Alerts")
    click_sb_action(d, '🔔')
    try:
        el_ss(d, ".modal", "15_alerts_modal")
        close_modal(d)
    except Exception as e: print(f"  ✗ 15_alerts_modal: {e}")

    # 16. Trades (sidebar action)
    print("[16] Trades")
    click_sb_action(d, '📊')
    try:
        el_ss(d, ".modal", "16_trades_modal")
        close_modal(d)
    except Exception as e: print(f"  ✗ 16_trades_modal: {e}")

    # 17. Forecast view
    print("[17] Forecast")
    click_tab(d, 'Forecast')
    time.sleep(0.5); full_ss(d, "17_forecast")

    # 18. Report view
    print("[18] Report")
    click_tab(d, 'Report')
    time.sleep(0.5); full_ss(d, "18_report_top")
    try:
        tax = d.find_element(By.CSS_SELECTOR, ".tax-split")
        d.execute_script("arguments[0].scrollIntoView({block:'center'})", tax)
        time.sleep(0.4)
        tax.find_element(By.XPATH, "./..").screenshot(f"{OUT}/18b_report_tax.png")
        print("  ✓ 18b_report_tax")
    except Exception as e: print(f"  ✗ 18b_report_tax: {e}")
    try:
        health = d.find_element(By.CSS_SELECTOR, ".health-grid")
        d.execute_script("arguments[0].scrollIntoView({block:'center'})", health)
        time.sleep(0.4)
        health.find_element(By.XPATH, "./..").screenshot(f"{OUT}/18c_report_health.png")
        print("  ✓ 18c_report_health")
    except Exception as e: print(f"  ✗ 18c_report_health: {e}")

finally: d.quit()

# ─── 19. Mobile view ────────────────────────────────────────
print("[19] Mobile view")
d = make_driver(375, 812)
try:
    login(d, "mobuser")
    inject_positions(d)
    full_ss(d, "19_mobile_overview")
    toggle = d.find_elements(By.CSS_SELECTOR, ".sb-toggle")
    if toggle: d.execute_script('arguments[0].click()', toggle[0]); time.sleep(0.5)
    full_ss(d, "19b_mobile_sidebar")
finally: d.quit()

# ─── 20. Light theme ────────────────────────────────────────
print("[20] Light theme")
d = make_driver(1280, 900)
try:
    login(d, "lightuser")
    inject_positions(d)
    # Toggle theme via sidebar action button
    theme_btns = d.find_elements(By.CSS_SELECTOR, ".sb-action-btn")
    theme_btn = next((b for b in theme_btns if '☀️' in b.text or '🌙' in b.text), None)
    if theme_btn: d.execute_script('arguments[0].click()', theme_btn); time.sleep(0.5)
    full_ss(d, "20_light_theme")
finally: d.quit()

print("\n=== Done ===")
files = sorted(os.listdir(OUT))
print(f"{len(files)} files captured:")
for f in files: print(f"  {f}")
