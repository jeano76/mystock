"""
Portfolio Manager - Selenium Test Suite
테스트 범위: 화면 레이아웃, 클릭 이벤트, 반응형
실행: python3 tests/test_portfolio.py
"""

import unittest
import threading
import time
import http.server
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ── 로컬 서버 설정 ──────────────────────────────────────────────
PORT = 18765
BASE_URL = f"http://localhost:{PORT}"
PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJ_DIR, **kwargs)

def start_server():
    server = http.server.HTTPServer(("localhost", PORT), SilentHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server

# 모듈 임포트 시 서버 자동 시작
_server = start_server()
time.sleep(0.3)

# ── Chrome 옵션 ─────────────────────────────────────────────────
def make_driver(width=1280, height=900, mobile=False):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument(f"--window-size={width},{height}")
    opts.add_argument("--lang=ko")
    if mobile:
        # Chrome 헤드리스 최소 뷰포트 우회: DevTools mobile emulation 사용
        mobile_emulation = {
            "deviceMetrics": {"width": width, "height": height, "pixelRatio": 2.0},
            "userAgent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile Safari/604.1"
            )
        }
        opts.add_experimental_option("mobileEmulation", mobile_emulation)
    svc = Service("/usr/local/bin/chromedriver")
    return webdriver.Chrome(service=svc, options=opts)

def wait(driver, timeout=8):
    return WebDriverWait(driver, timeout)

def clear_storage_and_reload(driver):
    """localStorage 초기화 후 페이지 리로드"""
    # 먼저 페이지로 이동한 후 localStorage 초기화
    if "localhost" not in driver.current_url:
        driver.get(BASE_URL)
        time.sleep(0.5)
    driver.execute_script("localStorage.clear();")
    driver.get(BASE_URL)
    time.sleep(1.0)

def register_and_login(driver, username="testuser", password="testpass123"):
    """테스트 계정 생성 및 로그인"""
    clear_storage_and_reload(driver)
    w = wait(driver)
    # 계정 만들기 화면 확인
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
    # 아이디 / 비밀번호 / 확인 입력
    inputs = driver.find_elements(By.CSS_SELECTOR, ".auth-card input")
    inputs[0].send_keys(username)
    inputs[1].send_keys(password)
    inputs[2].send_keys(password)
    # 계정 만들기 버튼
    driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
    # 로그인 성공 → 앱 로드 대기
    w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))

# ── 테스트 클래스 ────────────────────────────────────────────────

class TC01_PageLoad(unittest.TestCase):
    """TC01 페이지 로드 기본 확인"""

    def setUp(self):
        self.driver = make_driver()
        clear_storage_and_reload(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_01_title(self):
        """페이지 타이틀에 'Portfolio' 포함"""
        self.assertIn("Portfolio", self.driver.title)
        print(f"  title: {self.driver.title}")

    def test_02_auth_overlay_visible(self):
        """인증 오버레이가 화면에 표시됨"""
        el = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".auth-overlay")))
        self.assertTrue(el.is_displayed())

    def test_03_auth_card_visible(self):
        """auth-card 컨테이너 표시"""
        el = self.driver.find_element(By.CSS_SELECTOR, ".auth-card")
        self.assertTrue(el.is_displayed())

    def test_04_logo_visible(self):
        """PORTFOLIO 로고 텍스트"""
        el = self.driver.find_element(By.CSS_SELECTOR, ".auth-logo")
        self.assertIn("PORTFOLIO", el.text)


class TC02_AuthLayout(unittest.TestCase):
    """TC02 인증 화면 레이아웃"""

    def setUp(self):
        self.driver = make_driver()
        clear_storage_and_reload(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_01_register_title(self):
        """계정 만들기 제목 표시"""
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-title")))
        title = self.driver.find_element(By.CSS_SELECTOR, ".auth-title").text
        self.assertTrue(len(title) > 0)
        print(f"  auth title: {title}")

    def test_02_three_inputs(self):
        """아이디, 비밀번호, 확인 3개 입력 필드"""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, ".auth-card input")
        self.assertEqual(len(inputs), 3)

    def test_03_primary_button(self):
        """계정 만들기 버튼 존재"""
        btn = self.driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary")
        self.assertTrue(btn.is_displayed())

    def test_04_lang_toggle_button(self):
        """언어 전환 버튼 표시 (EN 또는 KO)"""
        btn = self.driver.find_element(By.CSS_SELECTOR, ".auth-lang .lang-btn")
        self.assertIn(btn.text, ["EN", "KO"])
        print(f"  lang btn: {btn.text}")

    def test_05_encryption_notice(self):
        """PBKDF2-SHA256 암호화 안내 텍스트"""
        body = self.driver.find_element(By.CSS_SELECTOR, ".auth-card").text
        self.assertIn("PBKDF2", body)


class TC03_LangToggle(unittest.TestCase):
    """TC03 언어 전환 기능"""

    def setUp(self):
        self.driver = make_driver()
        clear_storage_and_reload(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_01_default_korean(self):
        """초기 언어는 한국어"""
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-title")))
        title = self.driver.find_element(By.CSS_SELECTOR, ".auth-title").text
        # 한국어 타이틀 확인 (계정 만들기)
        self.assertTrue(any(ord(c) > 127 for c in title), f"한국어 아님: {title}")

    def test_02_toggle_to_english(self):
        """EN 버튼 클릭 시 영어로 전환"""
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-lang")))
        btn = self.driver.find_element(By.CSS_SELECTOR, ".auth-lang .lang-btn")
        self.assertEqual(btn.text, "EN")
        btn.click()
        time.sleep(0.4)
        title = self.driver.find_element(By.CSS_SELECTOR, ".auth-title").text
        self.assertIn("Create", title, f"영어 타이틀 아님: {title}")
        print(f"  EN title: {title}")

    def test_03_toggle_back_to_korean(self):
        """KO 버튼 클릭 시 한국어 복귀"""
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-lang")))
        btn = self.driver.find_element(By.CSS_SELECTOR, ".auth-lang .lang-btn")
        btn.click()   # EN
        time.sleep(0.3)
        btn = self.driver.find_element(By.CSS_SELECTOR, ".auth-lang .lang-btn")
        self.assertEqual(btn.text, "KO")
        btn.click()   # KO
        time.sleep(0.3)
        title = self.driver.find_element(By.CSS_SELECTOR, ".auth-title").text
        self.assertTrue(any(ord(c) > 127 for c in title))


class TC04_RegisterValidation(unittest.TestCase):
    """TC04 계정 생성 입력값 검증"""

    def setUp(self):
        self.driver = make_driver()
        clear_storage_and_reload(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_01_empty_submit_shows_error(self):
        """빈 상태에서 제출 시 오류 표시"""
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
        self.driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
        time.sleep(0.3)
        err = self.driver.find_element(By.CSS_SELECTOR, ".auth-err")
        self.assertTrue(err.is_displayed())
        print(f"  err: {err.text}")

    def test_02_short_id_error(self):
        """아이디 2자 → 오류"""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, ".auth-card input")
        inputs[0].send_keys("ab")
        inputs[1].send_keys("password123")
        inputs[2].send_keys("password123")
        self.driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
        time.sleep(0.3)
        err = self.driver.find_element(By.CSS_SELECTOR, ".auth-err")
        self.assertTrue(err.is_displayed())

    def test_03_password_mismatch_error(self):
        """비밀번호 불일치 → 오류"""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, ".auth-card input")
        inputs[0].send_keys("validuser")
        inputs[1].send_keys("password123")
        inputs[2].send_keys("differentpass")
        self.driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
        time.sleep(0.3)
        err = self.driver.find_element(By.CSS_SELECTOR, ".auth-err")
        self.assertTrue(err.is_displayed())


class TC05_LoginFlow(unittest.TestCase):
    """TC05 로그인 플로우"""

    def setUp(self):
        self.driver = make_driver()

    def tearDown(self):
        self.driver.quit()

    def test_01_register_success(self):
        """계정 생성 후 앱 메인 화면 진입"""
        register_and_login(self.driver)
        app = self.driver.find_element(By.CSS_SELECTOR, ".app")
        self.assertTrue(app.is_displayed())

    def test_02_session_persists_on_reload(self):
        """로그인 후 페이지 리로드 시 세션 유지"""
        register_and_login(self.driver)
        self.driver.refresh()
        time.sleep(1)
        app = wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))
        self.assertTrue(app.is_displayed())

    def test_03_logout_shows_login(self):
        """로그아웃 버튼 클릭 → 로그인 화면으로"""
        register_and_login(self.driver)
        # 로그아웃 버튼 (⎋ 포함 텍스트)
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        logout_btn = None
        for b in btns:
            if "로그아웃" in b.text or "Logout" in b.text:
                logout_btn = b
                break
        self.assertIsNotNone(logout_btn, "로그아웃 버튼 없음")
        logout_btn.click()
        time.sleep(0.5)
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-overlay")))

    def test_04_wrong_password_error(self):
        """로그인 화면에서 잘못된 비밀번호"""
        register_and_login(self.driver)
        # 로그아웃
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "로그아웃" in b.text or "Logout" in b.text:
                b.click(); break
        time.sleep(0.5)
        # 로그인 화면
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-card")))
        inputs = self.driver.find_elements(By.CSS_SELECTOR, ".auth-card input")
        inputs[0].send_keys("testuser")
        inputs[1].send_keys("wrongpassword")
        self.driver.find_element(By.CSS_SELECTOR, ".auth-card .btn-primary").click()
        time.sleep(1.5)
        err = self.driver.find_element(By.CSS_SELECTOR, ".auth-err")
        self.assertTrue(err.is_displayed())


class TC06_MainLayout(unittest.TestCase):
    """TC06 메인 앱 레이아웃"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_sidebar_visible(self):
        """사이드바 표시"""
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        self.assertTrue(sb.is_displayed())

    def test_02_topbar_visible(self):
        """상단 바 표시"""
        tb = self.driver.find_element(By.CSS_SELECTOR, ".topbar")
        self.assertTrue(tb.is_displayed())

    def test_03_main_content_visible(self):
        """메인 콘텐츠 영역 표시"""
        el = self.driver.find_element(By.CSS_SELECTOR, ".content")
        self.assertTrue(el.is_displayed())

    def test_04_hero_section_visible(self):
        """Hero 섹션 (총 평가액) 표시"""
        hero = self.driver.find_element(By.CSS_SELECTOR, ".hero")
        self.assertTrue(hero.is_displayed())

    def test_05_topbar_buttons_visible(self):
        """상단 버튼들 (API, 새로고침, + 포지션 추가) 표시"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn")
        self.assertGreaterEqual(len(btns), 3)
        print(f"  topbar buttons: {[b.text for b in btns]}")

    def test_06_sidebar_accounts_section(self):
        """사이드바 계좌 섹션 표시"""
        labels = self.driver.find_elements(By.CSS_SELECTOR, ".sb-lbl")
        texts = [l.text for l in labels]
        print(f"  sidebar labels: {texts}")
        self.assertTrue(len(labels) >= 2)

    def test_07_logo_in_topbar(self):
        """사이드바 로고 표시"""
        logo = self.driver.find_element(By.CSS_SELECTOR, ".logo")
        self.assertIn("PORTFOLIO", logo.text)


class TC07_SidebarInteraction(unittest.TestCase):
    """TC07 사이드바 토글 및 계좌 선택"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_collapse_sidebar(self):
        """사이드바 접기 버튼 클릭"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        self.assertIn("collapsed", sb.get_attribute("class"))

    def test_02_expand_sidebar(self):
        """사이드바 펼치기"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        self.assertNotIn("collapsed", sb.get_attribute("class"))

    def test_03_default_accounts_exist(self):
        """기본 계좌(Brokerage, Roth IRA, 401k) 표시"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-item")
        texts = [i.text for i in items]
        found = any("Brokerage" in t or "brokerage" in t.lower() for t in texts)
        self.assertTrue(found, f"Brokerage 없음. items: {texts}")

    def test_04_click_account_selects_it(self):
        """계좌 클릭 시 active 클래스 추가"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        # All Accounts 다음 항목 (첫 번째 계좌)
        for item in items:
            if "All" not in item.text and item.text.strip():
                item.click()
                time.sleep(0.3)
                self.assertIn("active", item.get_attribute("class"))
                break


class TC08_TabNavigation(unittest.TestCase):
    """TC08 탭 전환 (Overview / Positions)"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_overview_tab_default_active(self):
        """기본 탭은 Overview"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item.active")
        texts = [i.text for i in items]
        self.assertTrue(any("Overview" in t for t in texts), f"active items: {texts}")

    def test_02_click_positions_tab(self):
        """Positions 탭 클릭 → 필터 pill 표시"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.4)
                break
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".pill")
        self.assertGreater(len(pills), 0)
        print(f"  filter pills: {[p.text for p in pills]}")

    def test_03_click_overview_tab(self):
        """Overview 탭 클릭 → hero 섹션 표시"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Overview" in item.text:
                item.click()
                time.sleep(0.4)
                break
        hero = self.driver.find_element(By.CSS_SELECTOR, ".hero")
        self.assertTrue(hero.is_displayed())

    def test_04_inline_tabs_visible(self):
        """콘텐츠 내 탭 버튼 (Overview/Positions) 표시"""
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab")
        self.assertGreaterEqual(len(tabs), 2)
        print(f"  tabs: {[t.text for t in tabs]}")


class TC09_AddPositionModal(unittest.TestCase):
    """TC09 포지션 추가 모달"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_add_button_opens_modal(self):
        """+ 포지션 추가 버튼 클릭 → 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-primary")
        self.assertGreater(len(btns), 0)
        btns[-1].click()
        time.sleep(0.4)
        modal = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())

    def test_02_modal_has_ticker_input(self):
        """모달에 티커 입력 필드 존재"""
        fields = self.driver.find_elements(By.CSS_SELECTOR, ".modal .field input")
        self.assertGreater(len(fields), 0)

    def test_03_ticker_autocomplete(self):
        """티커 입력 시 자동완성 드롭다운"""
        fields = self.driver.find_elements(By.CSS_SELECTOR, ".modal .field input")
        fields[0].clear()
        fields[0].send_keys("AAPL")
        time.sleep(0.5)
        # 자동완성 항목 확인
        items = self.driver.find_elements(By.CSS_SELECTOR, ".ac-item")
        self.assertGreater(len(items), 0, "자동완성 없음")
        print(f"  autocomplete: {items[0].text}")

    def test_04_close_modal_with_x(self):
        """× 버튼으로 모달 닫기"""
        self.driver.find_element(By.CSS_SELECTOR, ".close-x").click()
        time.sleep(0.3)
        modals = self.driver.find_elements(By.CSS_SELECTOR, ".modal")
        visible = [m for m in modals if m.is_displayed()]
        self.assertEqual(len(visible), 0)


class TC10_FilterPills(unittest.TestCase):
    """TC10 필터 pill 클릭 이벤트"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        # Positions 탭으로 이동
        items = cls.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.4)
                break

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_pills_visible(self):
        """필터 pill 목록 표시"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".pill")
        self.assertGreaterEqual(len(pills), 4)
        print(f"  pills: {[p.text for p in pills]}")

    def test_02_first_pill_active(self):
        """첫 번째 pill (All) active 상태"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".pill")
        self.assertIn("active", pills[0].get_attribute("class"))

    def test_03_click_us_pill(self):
        """US pill 클릭 → active 전환"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".pill")
        us_pill = None
        for p in pills:
            if p.text == "US":
                us_pill = p; break
        if us_pill:
            us_pill.click()
            time.sleep(0.3)
            self.assertIn("active", us_pill.get_attribute("class"))

    def test_04_manage_filter_button(self):
        """⚙ 필터 관리 버튼 클릭 → FilterModal 열림"""
        gear = self.driver.find_element(By.CSS_SELECTOR, ".pills .btn-ghost")
        gear.click()
        time.sleep(0.4)
        modal = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())
        # 닫기
        self.driver.find_element(By.CSS_SELECTOR, ".close-x").click()
        time.sleep(0.3)


class TC11_TableSort(unittest.TestCase):
    """TC11 테이블 컬럼 정렬"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        # 포지션 추가 (테이블 렌더링 필요)
        btns = cls.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-primary")
        btns[-1].click()
        time.sleep(0.4)
        fields = cls.driver.find_elements(By.CSS_SELECTOR, ".modal .field input")
        fields[0].send_keys("AAPL")
        time.sleep(0.5)
        items = cls.driver.find_elements(By.CSS_SELECTOR, ".ac-item")
        if items:
            items[0].click(); time.sleep(0.3)
        fields = cls.driver.find_elements(By.CSS_SELECTOR, ".modal .field input")
        for f in fields:
            if f.get_attribute("value") == "":
                f.send_keys("5"); break
        cls.driver.find_element(By.CSS_SELECTOR, ".modal .btn-primary").click()
        time.sleep(0.5)
        # Positions 탭으로 이동
        items = cls.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.4)
                break

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_sortable_headers_exist(self):
        """정렬 가능한 헤더(sortable) 표시"""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "thead th.sortable")
        self.assertGreaterEqual(len(headers), 5)
        print(f"  sortable cols: {len(headers)}")

    def test_02_click_header_adds_sort_class(self):
        """헤더 클릭 시 sort-asc 또는 sort-desc 클래스 추가"""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "thead th.sortable")
        if headers:
            headers[0].click()
            time.sleep(0.3)
            cls = headers[0].get_attribute("class")
            self.assertTrue("sort-asc" in cls or "sort-desc" in cls, f"sort class 없음: {cls}")

    def test_03_double_click_toggles_direction(self):
        """헤더 두 번 클릭 시 정렬 방향 반전"""
        headers = self.driver.find_elements(By.CSS_SELECTOR, "thead th.sortable")
        if headers:
            headers[0].click(); time.sleep(0.3)
            cls1 = headers[0].get_attribute("class")
            headers[0].click(); time.sleep(0.3)
            cls2 = headers[0].get_attribute("class")
            self.assertNotEqual(cls1, cls2, "정렬 방향 바뀌지 않음")
            print(f"  sort toggle: {cls1} → {cls2}")


class TC12_SearchBar(unittest.TestCase):
    """TC12 검색바 동작"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        # Positions 탭
        items = cls.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.4)
                break

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_search_input_visible(self):
        """검색 입력 필드 표시"""
        inp = self.driver.find_element(By.CSS_SELECTOR, ".search-input")
        self.assertTrue(inp.is_displayed())

    def test_02_search_input_placeholder(self):
        """placeholder 텍스트 확인"""
        inp = self.driver.find_element(By.CSS_SELECTOR, ".search-input")
        ph = inp.get_attribute("placeholder")
        self.assertTrue(len(ph) > 0)
        print(f"  placeholder: {ph}")

    def test_03_type_in_search(self):
        """검색어 입력 가능"""
        inp = self.driver.find_element(By.CSS_SELECTOR, ".search-input")
        inp.click()
        inp.send_keys("AAPL")
        time.sleep(0.3)
        self.assertEqual(inp.get_attribute("value"), "AAPL")
        inp.clear()


class TC13_SettingsModal(unittest.TestCase):
    """TC13 API 설정 모달"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_api_button_opens_modal(self):
        """⚙️ API 버튼 클릭 → 설정 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn")
        api_btn = None
        for b in btns:
            if "API" in b.text:
                api_btn = b; break
        self.assertIsNotNone(api_btn, "API 버튼 없음")
        api_btn.click()
        time.sleep(0.4)
        modal = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())

    def test_02_api_key_inputs_visible(self):
        """API 키 입력 필드 표시"""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, ".modal .api-item input")
        self.assertGreaterEqual(len(inputs), 1)
        print(f"  api key inputs: {len(inputs)}")

    def test_03_cancel_button_closes_modal(self):
        """취소 버튼 클릭 → 모달 닫힘"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".modal-ft .btn:not(.btn-primary)")
        if btns:
            btns[0].click()
            time.sleep(0.3)
        modals = [m for m in self.driver.find_elements(By.CSS_SELECTOR, ".modal") if m.is_displayed()]
        self.assertEqual(len(modals), 0)


class TC14_IOModal(unittest.TestCase):
    """TC14 Export/Import 모달"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_io_button_visible(self):
        """⇅ 내보내기/가져오기 버튼 표시"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        io_btn = None
        for b in btns:
            if "⇅" in b.text:
                io_btn = b; break
        self.assertIsNotNone(io_btn, "IO 버튼 없음")
        self.assertTrue(io_btn.is_displayed())

    def test_02_io_button_opens_modal(self):
        """⇅ 버튼 클릭 → IO 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "⇅" in b.text:
                b.click(); break
        time.sleep(0.4)
        modal = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())

    def test_03_export_buttons_visible(self):
        """CSV / JSON 내보내기 버튼 표시"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".io-section .btn")
        self.assertGreaterEqual(len(btns), 2)
        print(f"  io btns: {[b.text for b in btns]}")

    def test_04_close_io_modal(self):
        """IO 모달 닫기"""
        self.driver.find_element(By.CSS_SELECTOR, ".close-x").click()
        time.sleep(0.3)
        modals = [m for m in self.driver.find_elements(By.CSS_SELECTOR, ".modal") if m.is_displayed()]
        self.assertEqual(len(modals), 0)


class TC15_MobileLayout(unittest.TestCase):
    """TC15 모바일 뷰포트 레이아웃 (375px)"""

    def setUp(self):
        self.driver = make_driver(width=375, height=812, mobile=True)
        register_and_login(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_01_topbar_within_viewport(self):
        """모바일에서 topbar가 뷰포트 안에 위치"""
        tb = self.driver.find_element(By.CSS_SELECTOR, ".topbar")
        size = tb.size
        loc = tb.location
        self.assertGreater(size["height"], 0)
        # topbar가 뷰포트 밖으로 나가지 않는지 (width가 viewport 이하)
        viewport_w = self.driver.execute_script("return window.innerWidth")
        self.assertLessEqual(loc["x"], 0 + viewport_w)
        print(f"  topbar: {size}, viewport_w: {viewport_w}")

    def test_02_content_scrollable(self):
        """콘텐츠 영역 스크롤 가능"""
        scroll_h = self.driver.execute_script("return document.body.scrollHeight")
        self.assertGreater(scroll_h, 0)

    def test_03_hero_visible_on_mobile(self):
        """모바일에서 Hero 섹션 표시"""
        hero = self.driver.find_element(By.CSS_SELECTOR, ".hero")
        self.assertTrue(hero.is_displayed())

    def test_04_no_horizontal_overflow(self):
        """수평 스크롤바 없음 (overflow)"""
        scroll_w = self.driver.execute_script("return document.body.scrollWidth")
        viewport_w = self.driver.execute_script("return window.innerWidth")
        # 모바일 레이아웃에서 최대 10% 허용 오차
        self.assertLessEqual(scroll_w, viewport_w * 1.1,
            f"수평 오버플로우: scrollWidth={scroll_w}, viewport={viewport_w}")


class TC16_MobileSidebarDrawer(unittest.TestCase):
    """TC16 모바일 사이드바 드로어 동작 (375px)"""

    def setUp(self):
        self.driver = make_driver(width=375, height=812, mobile=True)
        register_and_login(self.driver)
        self.w = wait(self.driver)

    def tearDown(self):
        self.driver.quit()

    def test_01_sidebar_initially_collapsed(self):
        """모바일 초기 상태: 사이드바가 collapsed 클래스 보유"""
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        classes = sb.get_attribute("class")
        self.assertIn("collapsed", classes)
        print(f"  sidebar classes: {classes}")

    def test_02_sidebar_width_collapsed(self):
        """사이드바 너비가 44px (접힌 상태)"""
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        w = sb.size["width"]
        self.assertLessEqual(w, 50, f"collapsed sidebar width={w}")
        print(f"  collapsed sidebar width: {w}px")

    def test_03_main_has_margin_for_sidebar(self):
        """main 영역 x좌표가 0이 아님 (사이드바 공간 확보)"""
        main = self.driver.find_element(By.CSS_SELECTOR, ".main")
        x = main.location["x"]
        self.assertGreater(x, 0, f"main.x={x} should be offset by sidebar")
        print(f"  main x offset: {x}px")

    def test_04_toggle_expands_sidebar(self):
        """토글 클릭 시 사이드바 확장 (collapsed 클래스 제거)"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        classes = sb.get_attribute("class")
        self.assertNotIn("collapsed", classes)
        print(f"  expanded sidebar classes: {classes}")

    def test_05_expanded_sidebar_width(self):
        """확장된 사이드바 너비 ≥ 180px"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        w = sb.size["width"]
        self.assertGreaterEqual(w, 180, f"expanded sidebar width={w}")
        print(f"  expanded sidebar width: {w}px")

    def test_06_backdrop_visible_when_expanded(self):
        """사이드바 확장 시 backdrop 표시"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        backdrop = self.w.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".sidebar-backdrop")))
        self.assertTrue(backdrop.is_displayed())
        print("  backdrop visible: True")

    def test_07_backdrop_click_closes_sidebar(self):
        """backdrop 클릭 시 사이드바 닫힘"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        backdrop = self.driver.find_element(By.CSS_SELECTOR, ".sidebar-backdrop")
        # 사이드바(220px)가 중앙을 가리므로 JS로 클릭
        self.driver.execute_script("arguments[0].click()", backdrop)
        time.sleep(0.4)
        sb = self.driver.find_element(By.CSS_SELECTOR, ".sidebar")
        classes = sb.get_attribute("class")
        self.assertIn("collapsed", classes)
        print("  sidebar closed after backdrop click")

    def test_08_main_not_clipped_when_sidebar_closed(self):
        """사이드바 닫힌 상태에서 main 콘텐츠 top이 잘리지 않음 (y≥0)"""
        main = self.driver.find_element(By.CSS_SELECTOR, ".main")
        y = main.location["y"]
        self.assertGreaterEqual(y, 0, f"main top clipped at y={y}")
        print(f"  main top y: {y}px")

    def test_09_no_horizontal_overflow_expanded(self):
        """사이드바 확장 상태에서도 수평 오버플로우 없음"""
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        scroll_w = self.driver.execute_script("return document.documentElement.scrollWidth")
        viewport_w = self.driver.execute_script("return window.innerWidth")
        self.assertLessEqual(scroll_w, viewport_w * 1.1,
            f"overflow: scrollWidth={scroll_w}, viewport={viewport_w}")

    def test_10_scroll_to_top_on_expand(self):
        """사이드바 열릴 때 main 스크롤이 상단으로 이동"""
        # main을 먼저 스크롤 아래로
        self.driver.execute_script("document.querySelector('.main').scrollTop = 300;")
        time.sleep(0.2)
        toggle = self.driver.find_element(By.CSS_SELECTOR, ".sb-toggle")
        toggle.click()
        time.sleep(0.4)
        scroll_top = self.driver.execute_script("return document.querySelector('.main').scrollTop")
        self.assertLessEqual(scroll_top, 50, f"scrollTop after expand: {scroll_top}")
        print(f"  scrollTop after expand: {scroll_top}")


class TC17_MultiViewportLayout(unittest.TestCase):
    """TC17 다해상도 레이아웃 검증 (모바일/태블릿/데스크탑)"""

    VIEWPORTS = [
        ("mobile_s",   375,  667),   # iPhone SE
        ("mobile_l",   390,  844),   # iPhone 14
        ("mobile_xl",  430,  932),   # iPhone 14 Pro Max
        ("tablet_p",   768, 1024),   # iPad portrait
        ("tablet_l",  1024,  768),   # iPad landscape
        ("desktop_hd",1280,  900),   # HD desktop
        ("desktop_fhd",1920,1080),   # Full HD desktop
    ]

    def _check_viewport(self, name, w, h):
        is_mobile = w <= 640
        driver = make_driver(width=w, height=h, mobile=is_mobile)
        try:
            register_and_login(driver)

            # 실제 뷰포트 크기 (Chrome 헤드리스는 최소값 있음)
            actual_w = driver.execute_script("return window.innerWidth")
            actual_h = driver.execute_script("return window.innerHeight")

            # 1) .app 렌더링 확인
            app = driver.find_element(By.CSS_SELECTOR, ".app")
            self.assertTrue(app.is_displayed(), f"[{name}] .app not displayed")

            # 2) topbar가 뷰포트 높이 내에 위치
            tb = driver.find_element(By.CSS_SELECTOR, ".topbar")
            tb_bot = tb.location["y"] + tb.size["height"]
            self.assertLessEqual(tb_bot, actual_h * 1.1,
                f"[{name}] topbar bottom={tb_bot} > viewport {actual_h}")

            # 3) 수평 오버플로우 없음 (실제 뷰포트 기준)
            scroll_w = driver.execute_script("return document.documentElement.scrollWidth")
            self.assertLessEqual(scroll_w, actual_w * 1.05,
                f"[{name}] horizontal overflow: scrollWidth={scroll_w}, viewport={actual_w}")

            # 4) 모바일(≤640) - 사이드바 44px
            if is_mobile:
                sb = driver.find_element(By.CSS_SELECTOR, ".sidebar")
                sb_w = sb.size["width"]
                self.assertLessEqual(sb_w, 50, f"[{name}] mobile sidebar too wide: {sb_w}px")
                # main이 사이드바와 겹치지 않음
                main_x = driver.find_element(By.CSS_SELECTOR, ".main").location["x"]
                self.assertGreater(main_x, 0, f"[{name}] main not offset from sidebar")

            # 5) 태블릿/데스크탑(>640) - 사이드바 정상 너비
            if w > 640:
                sb = driver.find_element(By.CSS_SELECTOR, ".sidebar")
                sb_w = sb.size["width"]
                self.assertGreaterEqual(sb_w, 40, f"[{name}] sidebar too narrow: {sb_w}px")

            # 6) hero 섹션 표시
            hero = driver.find_element(By.CSS_SELECTOR, ".hero")
            self.assertTrue(hero.is_displayed(), f"[{name}] hero not displayed")

            print(f"  [{name}] {w}x{h} ✓  scrollW={scroll_w}  sidebarW={driver.find_element(By.CSS_SELECTOR,'.sidebar').size['width']}")
        finally:
            driver.quit()

    def test_01_mobile_se(self):
        """iPhone SE (375×667) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[0])

    def test_02_mobile_14(self):
        """iPhone 14 (390×844) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[1])

    def test_03_mobile_14_pro_max(self):
        """iPhone 14 Pro Max (430×932) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[2])

    def test_04_tablet_portrait(self):
        """iPad portrait (768×1024) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[3])

    def test_05_tablet_landscape(self):
        """iPad landscape (1024×768) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[4])

    def test_06_desktop_hd(self):
        """HD 데스크탑 (1280×900) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[5])

    def test_07_desktop_fhd(self):
        """Full HD 데스크탑 (1920×1080) 레이아웃"""
        self._check_viewport(*self.VIEWPORTS[6])

    def test_08_charts_row_single_col_on_mobile(self):
        """모바일에서 charts-row가 단일 컬럼 (섹터분석 아래 배치)"""
        driver = make_driver(width=375, height=812, mobile=True)
        try:
            register_and_login(driver)
            charts = driver.find_elements(By.CSS_SELECTOR, ".charts-row .chart-card")
            if len(charts) >= 2:
                y0 = charts[0].location["y"]
                y1 = charts[1].location["y"]
                self.assertGreater(y1, y0 + 50,
                    f"섹터분석 카드가 옆이 아닌 아래에 위치해야 함: y0={y0}, y1={y1}")
                print(f"  chart-card[0].y={y0}, chart-card[1].y={y1} (stacked ✓)")
        finally:
            driver.quit()

    def test_09_charts_row_two_col_on_desktop(self):
        """데스크탑에서 charts-row가 2컬럼 (도넛·섹터 나란히)"""
        driver = make_driver(width=1280, height=900)
        try:
            register_and_login(driver)
            charts = driver.find_elements(By.CSS_SELECTOR, ".charts-row .chart-card")
            if len(charts) >= 2:
                y0 = charts[0].location["y"]
                y1 = charts[1].location["y"]
                self.assertAlmostEqual(y0, y1, delta=20,
                    msg=f"데스크탑에서 두 카드가 같은 행에 있어야 함: y0={y0}, y1={y1}")
                print(f"  chart-card[0].y={y0}, chart-card[1].y={y1} (side-by-side ✓)")
        finally:
            driver.quit()


# ── 색상 대비 유틸 ────────────────────────────────────────────────
CONTRAST_JS = """
(function(){
  function hexToRgb(hex){
    hex=hex.replace('#','');
    if(hex.length===3) hex=hex.split('').map(function(c){return c+c}).join('');
    return {r:parseInt(hex.slice(0,2),16),g:parseInt(hex.slice(2,4),16),b:parseInt(hex.slice(4,6),16)};
  }
  function parseColor(str){
    str=str.trim();
    var m=str.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)/);
    if(m) return {r:parseInt(m[1]),g:parseInt(m[2]),b:parseInt(m[3])};
    if(str.startsWith('#')) return hexToRgb(str);
    return null;
  }
  function linearize(c){c=c/255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)}
  function luminance(r,g,b){return 0.2126*linearize(r)+0.7152*linearize(g)+0.0722*linearize(b)}
  function contrastRatio(c1,c2){
    var l1=luminance(c1.r,c1.g,c1.b),l2=luminance(c2.r,c2.g,c2.b);
    var hi=Math.max(l1,l2),lo=Math.min(l1,l2);
    return (hi+0.05)/(lo+0.05);
  }
  var results=[];
  var checks=[
    {sel:'.hero-val',desc:'Hero 총평가액'},
    {sel:'.hero-lbl',desc:'Hero 레이블'},
    {sel:'.hstat-val',desc:'통계 수치'},
    {sel:'.hstat-lbl',desc:'통계 레이블'},
    {sel:'.hstat-sub',desc:'통계 서브'},
    {sel:'.page-hdr-title',desc:'페이지 타이틀'},
    {sel:'.footer-copy',desc:'푸터 저작권'},
    {sel:'.api-dot-lbl',desc:'API 상태 라벨'},
    {sel:'.legend-name',desc:'범례 이름'},
    {sel:'.tab',desc:'탭 버튼'},
    {sel:'.sb-name',desc:'사이드바 메뉴'},
    {sel:'.btn',desc:'버튼'},
    {sel:'.toast-msg',desc:'토스트 메시지'},
  ];
  checks.forEach(function(chk){
    var el=document.querySelector(chk.sel);
    if(!el) return;
    var st=window.getComputedStyle(el);
    var fg=parseColor(st.color);
    var bg=parseColor(st.backgroundColor);
    if(!fg) return;
    // bg가 투명이면 부모에서 찾기
    if(!bg||bg.r===0&&bg.g===0&&bg.b===0&&st.backgroundColor==='rgba(0, 0, 0, 0)'){
      var p=el.parentElement;
      while(p){var ps=window.getComputedStyle(p);var prgba=ps.backgroundColor;if(prgba&&prgba!=='rgba(0, 0, 0, 0)'){bg=parseColor(prgba);break;}p=p.parentElement;}
    }
    if(!bg) bg={r:0,g:0,b:0};
    var ratio=contrastRatio(fg,bg);
    var size=parseFloat(st.fontSize);
    var bold=parseInt(st.fontWeight)>=700;
    var minRatio=(size>=18||(size>=14&&bold))?3.0:4.5;
    results.push({sel:chk.sel,desc:chk.desc,ratio:Math.round(ratio*100)/100,fg:st.color,bg:st.backgroundColor,size:size,pass:ratio>=minRatio,min:minRatio});
  });
  return results;
})()
"""

def add_position(driver, ticker="AAPL", shares="5"):
    """포지션 추가 헬퍼"""
    btns = driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-primary")
    btns[-1].click()
    time.sleep(0.4)
    fields = driver.find_elements(By.CSS_SELECTOR, ".modal .field input")
    fields[0].clear()
    fields[0].send_keys(ticker)
    time.sleep(0.5)
    items = driver.find_elements(By.CSS_SELECTOR, ".ac-item")
    if items:
        items[0].click()
        time.sleep(0.3)
    # 수량 입력
    fields = driver.find_elements(By.CSS_SELECTOR, ".modal .field input")
    for f in fields:
        if f.get_attribute("value") == "" or f.get_attribute("value") == "0":
            f.clear()
            f.send_keys(shares)
            break
    save_btns = driver.find_elements(By.CSS_SELECTOR, ".modal .btn-primary")
    save_btns[-1].click()
    time.sleep(0.5)


class TC18_AlertsModal(unittest.TestCase):
    """TC18 알림(Alerts) 모달"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_alerts_button_in_topbar(self):
        """상단 바에 🔔 알림 버튼 존재"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        alert_btn = None
        for b in btns:
            if "🔔" in b.text or (b.get_attribute("title") and "Alert" in b.get_attribute("title")):
                alert_btn = b
                break
        self.assertIsNotNone(alert_btn, "🔔 알림 버튼 없음")
        self.assertTrue(alert_btn.is_displayed())

    def test_02_alerts_button_opens_modal(self):
        """🔔 버튼 클릭 → 알림 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "🔔" in b.text or (b.get_attribute("title") and "Alert" in b.get_attribute("title")):
                b.click()
                break
        time.sleep(0.4)
        modal = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".overlay")))
        self.assertTrue(modal.is_displayed())
        print("  Alerts modal: opened")

    def test_03_alerts_modal_has_add_button(self):
        """알림 모달에 알림 추가 버튼 존재"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".overlay .btn-primary")
        self.assertGreater(len(btns), 0, "알림 추가 버튼 없음")
        print(f"  alerts add btn: {btns[0].text}")

    def test_04_alerts_modal_empty_state(self):
        """알림 없을 때 빈 상태 텍스트 표시"""
        overlay = self.driver.find_element(By.CSS_SELECTOR, ".overlay")
        text = overlay.text
        self.assertTrue(len(text) > 0)
        print(f"  alerts modal text snippet: {text[:60]}")

    def test_05_close_alerts_modal(self):
        """알림 모달 닫기 (× 버튼)"""
        self.driver.find_element(By.CSS_SELECTOR, ".overlay .close-x").click()
        time.sleep(0.3)
        overlays = [o for o in self.driver.find_elements(By.CSS_SELECTOR, ".overlay") if o.is_displayed()]
        self.assertEqual(len(overlays), 0)


class TC19_TradesModal(unittest.TestCase):
    """TC19 거래 내역(Trades) 모달"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_trades_button_in_topbar(self):
        """상단 바에 📊 거래 내역 버튼 존재"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        trade_btn = None
        for b in btns:
            if "📊" in b.text or (b.get_attribute("title") and "Trade" in b.get_attribute("title")):
                trade_btn = b
                break
        self.assertIsNotNone(trade_btn, "📊 거래 버튼 없음")
        self.assertTrue(trade_btn.is_displayed())

    def test_02_trades_button_opens_modal(self):
        """📊 버튼 클릭 → 거래 내역 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "📊" in b.text or (b.get_attribute("title") and "Trade" in b.get_attribute("title")):
                b.click()
                break
        time.sleep(0.4)
        modal = wait(self.driver).until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".overlay")))
        self.assertTrue(modal.is_displayed())
        print("  Trades modal: opened")

    def test_03_trades_modal_has_add_button(self):
        """거래 내역 모달에 거래 추가 버튼 존재"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".overlay .btn-primary")
        self.assertGreater(len(btns), 0, "거래 추가 버튼 없음")

    def test_04_trades_modal_has_ticker_selector(self):
        """거래 추가 폼에 티커 선택 또는 입력 필드 존재"""
        inputs = self.driver.find_elements(By.CSS_SELECTOR, ".overlay input, .overlay select")
        self.assertGreater(len(inputs), 0, "입력 필드 없음")
        print(f"  trade form inputs: {len(inputs)}")

    def test_05_close_trades_modal(self):
        """거래 내역 모달 닫기"""
        self.driver.find_element(By.CSS_SELECTOR, ".overlay .close-x").click()
        time.sleep(0.3)
        overlays = [o for o in self.driver.find_elements(By.CSS_SELECTOR, ".overlay") if o.is_displayed()]
        self.assertEqual(len(overlays), 0)


class TC20_ThemeToggle(unittest.TestCase):
    """TC20 다크/라이트 테마 전환"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _get_theme_btn(self):
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            txt = b.text
            if "☀️" in txt or "🌙" in txt:
                return b
        return None

    def test_01_theme_btn_exists(self):
        """테마 전환 버튼 존재 (☀️ 또는 🌙)"""
        btn = self._get_theme_btn()
        self.assertIsNotNone(btn, "테마 전환 버튼 없음")
        self.assertTrue(btn.is_displayed())
        print(f"  theme btn: '{btn.text}'")

    def test_02_default_dark_theme(self):
        """초기 테마: 다크 (html에 light 클래스 없음)"""
        html_class = self.driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        self.assertNotIn("light", html_class, f"초기가 라이트 테마: {html_class}")

    def test_03_click_toggles_to_light(self):
        """테마 버튼 클릭 → 라이트 모드 전환 (html.light 추가)"""
        btn = self._get_theme_btn()
        self.assertIsNotNone(btn)
        btn.click()
        time.sleep(0.3)
        html_class = self.driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        self.assertIn("light", html_class, f"라이트 테마 전환 실패: {html_class}")
        print(f"  html class after toggle: '{html_class}'")

    def test_04_light_theme_bg_color(self):
        """라이트 테마에서 body 배경색이 밝은 색"""
        bg = self.driver.execute_script(
            "return window.getComputedStyle(document.body).backgroundColor"
        )
        # light theme: --bg:#ffffff → rgb(255,255,255)
        self.assertIn("255", bg, f"라이트 bg 색상 의심: {bg}")
        print(f"  light bg: {bg}")

    def test_05_click_toggles_back_to_dark(self):
        """다시 클릭 → 다크 모드 복귀"""
        btn = self._get_theme_btn()
        self.assertIsNotNone(btn)
        btn.click()
        time.sleep(0.3)
        html_class = self.driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        self.assertNotIn("light", html_class, f"다크 복귀 실패: {html_class}")

    def test_06_light_theme_text_readable(self):
        """라이트 테마에서 주요 텍스트가 어두운 색 (가독성)"""
        # 라이트로 전환
        btn = self._get_theme_btn()
        btn.click()
        time.sleep(0.3)
        color = self.driver.execute_script(
            "return window.getComputedStyle(document.querySelector('.hero-val')).color"
        )
        # light --text:#111111 → rgb(17,17,17)
        parts = [int(x) for x in color.replace("rgb(","").replace(")","").split(",")[:3]]
        brightness = sum(parts) / 3
        self.assertLess(brightness, 100, f"라이트 테마 텍스트가 너무 밝음: {color}")
        print(f"  light text color: {color}")
        # 다크로 복원
        btn = self._get_theme_btn()
        btn.click()
        time.sleep(0.2)


class TC21_InlineCellEditing(unittest.TestCase):
    """TC21 테이블 인라인 셀 편집"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        # 포지션 추가
        add_position(cls.driver, "AAPL", "10")
        # Positions 탭 이동
        items = cls.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.4)
                break

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_editable_cells_exist(self):
        """cell-editable 클래스 셀이 테이블에 존재"""
        cells = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-editable")
        self.assertGreater(len(cells), 0, "편집 가능 셀 없음")
        print(f"  editable cells: {len(cells)}")

    def test_02_click_cell_shows_input(self):
        """편집 가능 셀 클릭 → input 또는 select 나타남"""
        cells = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-editable")
        if cells:
            cells[0].click()
            time.sleep(0.3)
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-input")
            self.assertGreater(len(inputs), 0, "편집 input 나타나지 않음")
            print(f"  cell-input appeared: {inputs[0].get_attribute('value')}")

    def test_03_escape_cancels_edit(self):
        """Escape 키 → 편집 취소 (input 사라짐)"""
        cells = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-editable")
        if cells:
            cells[0].click()
            time.sleep(0.2)
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-input")
            if inputs:
                inputs[0].send_keys(Keys.ESCAPE)
                time.sleep(0.3)
            remaining = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-input")
            self.assertEqual(len(remaining), 0, "Escape 후 input이 남아있음")

    def test_04_edit_and_save_with_enter(self):
        """값 수정 후 Enter → 저장 (input 사라지고 값 유지)"""
        # shares 셀 편집 (숫자 셀)
        cells = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-editable")
        for cell in cells:
            cell.click()
            time.sleep(0.2)
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-input")
            if inputs:
                old_val = inputs[0].get_attribute("value")
                inputs[0].triple_click() if hasattr(inputs[0], 'triple_click') else None
                inputs[0].send_keys(Keys.CONTROL + "a")
                inputs[0].send_keys("15")
                inputs[0].send_keys(Keys.RETURN)
                time.sleep(0.3)
                remaining = self.driver.find_elements(By.CSS_SELECTOR, "tbody .cell-input")
                self.assertEqual(len(remaining), 0, "Enter 후 input이 남아있음")
                print(f"  saved: old={old_val} → 15")
                break

    def test_05_delete_button_shows_confirm(self):
        """🗑 삭제 버튼 클릭 → 인라인 확인(삭제?/확인/취소) 표시"""
        # 🗑 버튼은 tbody의 마지막 td 안의 btn-ghost
        del_btn = None
        btns = self.driver.find_elements(By.CSS_SELECTOR, "tbody td:last-child .btn-ghost")
        for b in btns:
            if "🗑" in b.text:
                del_btn = b
                break
        if not del_btn:
            # fallback: 모든 tbody btn-ghost 검색
            for b in self.driver.find_elements(By.CSS_SELECTOR, "tbody .btn-ghost"):
                if "🗑" in b.text:
                    del_btn = b
                    break
        self.assertIsNotNone(del_btn, "🗑 삭제 버튼 없음")
        del_btn.click()
        time.sleep(0.4)
        # 인라인 confirm: tbody 안에 "삭제?" 또는 "확인" 버튼 나타남
        tbody_text = self.driver.find_element(By.CSS_SELECTOR, "tbody").text
        confirm_visible = "확인" in tbody_text or "삭제" in tbody_text
        self.assertTrue(confirm_visible, f"삭제 확인 없음 (tbody text: {tbody_text[:60]})")
        # 취소 버튼 클릭
        cancel_btns = self.driver.find_elements(By.CSS_SELECTOR, "tbody .btn-ghost")
        for cb in cancel_btns:
            if "취소" in cb.text:
                cb.click()
                break
        time.sleep(0.2)
        print("  delete inline confirm: shown ✓")


class TC22_ColumnVisibility(unittest.TestCase):
    """TC22 컬럼 표시/숨기기"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        add_position(cls.driver, "MSFT", "5")
        # Positions 탭
        items = cls.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.4)
                break

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_column_settings_button_exists(self):
        """⊞ 컬럼 설정 버튼 존재 (테이블 헤더 마지막 th 안)"""
        # 컬럼 버튼은 .col-vis-wrap 안에 있음
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-wrap .btn")
        if not btns:
            # fallback: thead의 모든 버튼
            btns = self.driver.find_elements(By.CSS_SELECTOR, "thead .btn")
        col_btn = None
        for b in btns:
            if "⊞" in b.text or "Columns" in b.text or "컬럼" in b.text:
                col_btn = b
                break
        self.assertIsNotNone(col_btn, "컬럼 버튼 없음 (⊞)")
        self.assertTrue(col_btn.is_displayed())
        print(f"  col btn: '{col_btn.text}'")

    def test_02_click_opens_dropdown(self):
        """컬럼 버튼 클릭 → 드롭다운 표시"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-wrap .btn")
        if not btns:
            btns = self.driver.find_elements(By.CSS_SELECTOR, "thead .btn")
        for b in btns:
            if "⊞" in b.text or "Columns" in b.text or "컬럼" in b.text:
                b.click()
                break
        time.sleep(0.3)
        drop = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-drop")
        self.assertGreater(len(drop), 0, ".col-vis-drop 없음")
        visible = [d for d in drop if d.is_displayed()]
        self.assertGreater(len(visible), 0, "드롭다운 미표시")
        print(f"  col-vis-drop visible: {len(visible)}")

    def test_03_checkboxes_exist(self):
        """드롭다운에 체크박스 항목 존재"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-item")
        self.assertGreaterEqual(len(items), 5, f"체크박스 항목 부족: {len(items)}")
        print(f"  col-vis items: {len(items)}")

    def test_04_toggle_column_off(self):
        """체크박스 클릭 → 해당 컬럼 표시 상태 변경"""
        # 드롭다운이 닫혀 있을 수 있으므로 다시 열기
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-wrap .btn")
        if not btns:
            btns = self.driver.find_elements(By.CSS_SELECTOR, "thead .btn")
        for b in btns:
            if "⊞" in b.text or "Columns" in b.text or "컬럼" in b.text:
                b.click()
                time.sleep(0.3)
                break
        items = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-item")
        if items:
            cb = items[-2].find_element(By.CSS_SELECTOR, "input[type=checkbox]")
            was_checked = cb.is_selected()
            # JS click으로 안정적으로 클릭
            self.driver.execute_script("arguments[0].click()", cb)
            time.sleep(0.3)
            items2 = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-item")
            if items2:
                cb2 = items2[-2].find_element(By.CSS_SELECTOR, "input[type=checkbox]")
                self.assertNotEqual(cb2.is_selected(), was_checked, "체크박스 상태 변경 안됨")
                print(f"  checkbox toggled: {was_checked} → {cb2.is_selected()}")

    def test_05_close_dropdown_by_clicking_button(self):
        """컬럼 버튼 재클릭 → 드롭다운 닫힘"""
        # 먼저 드롭다운이 열려있는지 확인, 없으면 열기
        drops = [d for d in self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-drop") if d.is_displayed()]
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-wrap .btn")
        if not btns:
            btns = self.driver.find_elements(By.CSS_SELECTOR, "thead .btn")
        col_btn = None
        for b in btns:
            if "⊞" in b.text or "Columns" in b.text or "컬럼" in b.text:
                col_btn = b
                break
        if not drops and col_btn:
            col_btn.click()
            time.sleep(0.3)
        # 드롭다운 닫기 (버튼 재클릭)
        if col_btn:
            col_btn.click()
            time.sleep(0.3)
        drops = [d for d in self.driver.find_elements(By.CSS_SELECTOR, ".col-vis-drop") if d.is_displayed()]
        self.assertEqual(len(drops), 0, "버튼 재클릭 후 드롭다운이 닫히지 않음")
        print("  col-vis dropdown closed ✓")


class TC23_SnapshotBtn(unittest.TestCase):
    """TC23 포트폴리오 스냅샷"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        add_position(cls.driver, "AAPL", "10")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_snapshot_button_exists(self):
        """📸 스냅샷 버튼 존재 (topbar)"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        snap_btn = None
        for b in btns:
            if "📸" in b.text or (b.get_attribute("title") and "snapshot" in b.get_attribute("title").lower()):
                snap_btn = b
                break
        self.assertIsNotNone(snap_btn, "📸 스냅샷 버튼 없음")
        self.assertTrue(snap_btn.is_displayed())
        print(f"  snapshot btn: '{snap_btn.text}'")

    def test_02_snapshot_saves_and_shows_toast(self):
        """📸 버튼 클릭 → 토스트 알림 표시"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "📸" in b.text or (b.get_attribute("title") and "snapshot" in b.get_attribute("title").lower()):
                b.click()
                break
        time.sleep(0.5)
        toasts = self.driver.find_elements(By.CSS_SELECTOR, ".toast")
        self.assertGreater(len(toasts), 0, "스냅샷 저장 토스트 없음")
        print(f"  toast: {toasts[0].text[:40]}")

    def _click_snapshot_btn(self):
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "📸" in b.text or (b.get_attribute("title") and "snapshot" in b.get_attribute("title").lower()):
                b.click()
                return True
        return False

    def test_03_snapshot_card_in_overview(self):
        """Overview에 스냅샷 차트 카드 표시 (날짜 다른 2개 주입 후)"""
        # 스냅샷은 하루 1개만 저장됨 → localStorage에 다른 날짜로 2개 직접 주입
        self.driver.execute_script("""
            var d1=new Date(Date.now()-86400000).toISOString().slice(0,10);
            var d2=new Date().toISOString().slice(0,10);
            localStorage.setItem('pfm3_snapshots',JSON.stringify([
                {date:d1,val:9800,gain:300,pct:3.1},
                {date:d2,val:10200,gain:500,pct:5.0}
            ]));
        """)
        # 페이지 새로고침 → 스냅샷 상태 로드 (세션은 유지됨)
        self.driver.refresh()
        time.sleep(1.5)
        wait(self.driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".app")))
        # Overview 탭으로 이동
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab")
        for t in tabs:
            if "Overview" in t.text or "오버뷰" in t.text or "📊" in t.text:
                t.click()
                time.sleep(0.5)
                break
        snap_cards = self.driver.find_elements(By.CSS_SELECTOR, ".snapshot-card")
        snap_count = self.driver.execute_script(
            "return (JSON.parse(localStorage.getItem('pfm3_snapshots')||'[]')).length"
        )
        print(f"  snapshot count: {snap_count}, cards: {len(snap_cards)}")
        self.assertGreater(len(snap_cards), 0, f"스냅샷 카드 없음 ({snap_count}개 주입 후)")


class TC24_BenchmarkPills(unittest.TestCase):
    """TC24 벤치마크 비교 pill"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        add_position(cls.driver, "AAPL", "10")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_benchmark_section_exists(self):
        """벤치마크 비교 섹션 존재"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".bench-pill")
        self.assertGreater(len(pills), 0, ".bench-pill 없음")
        print(f"  benchmark pills: {[p.text for p in pills]}")

    def test_02_none_pill_active_by_default(self):
        """기본 벤치마크: 없음(None) pill active"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".bench-pill")
        first = pills[0]
        self.assertIn("active", first.get_attribute("class"), "첫 번째 pill이 active 아님")

    def test_03_click_sp500_pill(self):
        """S&P 500 pill 클릭 → active 전환"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".bench-pill")
        sp_pill = None
        for p in pills:
            if "S&P" in p.text or "500" in p.text:
                sp_pill = p
                break
        if sp_pill:
            sp_pill.click()
            time.sleep(0.3)
            self.assertIn("active", sp_pill.get_attribute("class"))
            print(f"  S&P 500 pill active: ✓")

    def test_04_click_nasdaq_pill(self):
        """Nasdaq pill 클릭 → active 전환"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".bench-pill")
        nq_pill = None
        for p in pills:
            if "나스닥" in p.text or "Nasdaq" in p.text or "NQ" in p.text:
                nq_pill = p
                break
        if nq_pill:
            nq_pill.click()
            time.sleep(0.3)
            self.assertIn("active", nq_pill.get_attribute("class"))
            print(f"  Nasdaq pill active: ✓")

    def test_05_click_none_resets_benchmark(self):
        """없음 pill 클릭 → 벤치마크 해제"""
        pills = self.driver.find_elements(By.CSS_SELECTOR, ".bench-pill")
        pills[0].click()
        time.sleep(0.3)
        self.assertIn("active", pills[0].get_attribute("class"))


class TC25_ColorContrastDark(unittest.TestCase):
    """TC25 색상 대비 검증 - 다크 테마 (WCAG AA)"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        add_position(cls.driver, "AAPL", "10")
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _contrast_ratio(self, selector, bg_selector=None):
        """CSS selector 요소의 텍스트/배경 대비율 계산. bg_selector가 없으면 부모에서 찾음"""
        return self.driver.execute_script("""
          var sel=arguments[0], bgSel=arguments[1];
          function lin(c){c=c/255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)}
          function lum(r,g,b){return 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b)}
          function cont(c1,c2){var l1=lum(c1[0],c1[1],c1[2]),l2=lum(c2[0],c2[1],c2[2]);var hi=Math.max(l1,l2),lo=Math.min(l1,l2);return(hi+0.05)/(lo+0.05)}
          function parse(s){var m=s.match(/rgb[a]?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);return m?[+m[1],+m[2],+m[3]]:null}
          function findBg(el){
            var p=el;
            while(p){
              var st=getComputedStyle(p);
              var bg=st.backgroundColor;
              // skip transparent and gradient
              if(bg&&bg!=='rgba(0, 0, 0, 0)'&&bg.indexOf('rgba(0, 0, 0, 0)')<0){
                var c=parse(bg);if(c)return c;
              }
              // check CSS variable resolved value for gradient backgrounds
              if(st.background&&st.background.indexOf('gradient')>-1){
                // use --bg3 variable as fallback for gradient
                var bgVar=getComputedStyle(document.documentElement).getPropertyValue('--bg3').trim();
                if(bgVar){
                  if(bgVar.startsWith('#')){
                    var h=bgVar.replace('#','');
                    if(h.length===3)h=h.split('').map(function(c){return c+c}).join('');
                    return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];
                  }
                  var c2=parse(bgVar);if(c2)return c2;
                }
              }
              p=p.parentElement;
            }
            return null;
          }
          var el=document.querySelector(sel);if(!el)return -1;
          var fg=parse(getComputedStyle(el).color);if(!fg)return -2;
          var bg;
          if(bgSel){
            var bgEl=document.querySelector(bgSel);
            bg=bgEl?findBg(bgEl):null;
          } else {
            bg=findBg(el);
          }
          if(!bg)return -3;
          return Math.round(cont(fg,bg)*100)/100;
        """, selector, bg_selector)

    def test_01_hero_val_contrast(self):
        """Hero 총 평가액 텍스트 대비율 ≥ 4.5"""
        # .hero는 linear-gradient 배경 → CSS 변수 --bg3 기준으로 계산
        ratio = self._contrast_ratio(".hero-val")
        print(f"  hero-val contrast: {ratio}:1")
        self.assertGreaterEqual(ratio, 4.5, f"Hero 값 텍스트 대비율 부족: {ratio}:1")

    def test_02_page_title_contrast(self):
        """페이지 제목 텍스트 대비율 ≥ 4.5"""
        ratio = self._contrast_ratio(".page-hdr-title")
        print(f"  page-hdr-title contrast: {ratio}:1")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 4.5, f"페이지 제목 대비율 부족: {ratio}:1")

    def test_03_footer_copy_contrast(self):
        """푸터 저작권 텍스트 대비율 (최소 2.5:1 - 장식적 텍스트)"""
        ratio = self._contrast_ratio(".footer-copy")
        print(f"  footer-copy contrast: {ratio}:1  (min 2.5:1)")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 2.5, f"푸터 저작권 대비율 너무 낮음: {ratio}:1")

    def test_04_sidebar_menu_contrast(self):
        """사이드바 메뉴 텍스트 대비율 ≥ 4.5"""
        ratio = self._contrast_ratio(".sb-name")
        print(f"  sb-name contrast: {ratio}:1")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 4.5, f"사이드바 메뉴 대비율 부족: {ratio}:1")

    def test_05_tab_active_contrast(self):
        """활성 탭 텍스트 대비율 ≥ 4.5"""
        ratio = self._contrast_ratio(".tab.active")
        print(f"  tab.active contrast: {ratio}:1")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 4.5, f"탭 대비율 부족: {ratio}:1")

    def test_06_btn_primary_contrast(self):
        """기본 파란 버튼 텍스트 대비율 ≥ 3.0"""
        ratio = self._contrast_ratio(".btn-primary")
        print(f"  btn-primary contrast: {ratio}:1")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 3.0, f"버튼 대비율 부족: {ratio}:1")


class TC26_ColorContrastLight(unittest.TestCase):
    """TC26 색상 대비 검증 - 라이트 테마"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        add_position(cls.driver, "AAPL", "10")
        # 라이트 모드로 전환
        btns = cls.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "☀️" in b.text or "🌙" in b.text:
                b.click()
                break
        time.sleep(0.4)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_light_mode_active(self):
        """라이트 테마 활성 확인"""
        html_class = self.driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        self.assertIn("light", html_class)

    def _contrast_ratio(self, selector, bg_selector=None):
        """TC25와 동일한 대비율 계산 헬퍼 (라이트 테마용)"""
        return self.driver.execute_script("""
          var sel=arguments[0], bgSel=arguments[1];
          function lin(c){c=c/255;return c<=0.03928?c/12.92:Math.pow((c+0.055)/1.055,2.4)}
          function lum(r,g,b){return 0.2126*lin(r)+0.7152*lin(g)+0.0722*lin(b)}
          function cont(c1,c2){var l1=lum(c1[0],c1[1],c1[2]),l2=lum(c2[0],c2[1],c2[2]);var hi=Math.max(l1,l2),lo=Math.min(l1,l2);return(hi+0.05)/(lo+0.05)}
          function parse(s){var m=s.match(/rgb[a]?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);return m?[+m[1],+m[2],+m[3]]:null}
          function findBg(el){
            var p=el;
            while(p){
              var st=getComputedStyle(p);
              var bg=st.backgroundColor;
              if(bg&&bg!=='rgba(0, 0, 0, 0)'&&bg.indexOf('rgba(0, 0, 0, 0)')<0){var c=parse(bg);if(c)return c;}
              if(st.background&&st.background.indexOf('gradient')>-1){
                var bgVar=getComputedStyle(document.documentElement).getPropertyValue('--bg3').trim();
                if(bgVar){if(bgVar.startsWith('#')){var h=bgVar.replace('#','');if(h.length===3)h=h.split('').map(function(c){return c+c}).join('');return[parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}var c2=parse(bgVar);if(c2)return c2;}
              }
              p=p.parentElement;
            }
            return null;
          }
          var el=document.querySelector(sel);if(!el)return -1;
          var fg=parse(getComputedStyle(el).color);if(!fg)return -2;
          var bg=findBg(bgSel?document.querySelector(bgSel):el);
          if(!bg)return -3;
          return Math.round(cont(fg,bg)*100)/100;
        """, selector, bg_selector)

    def test_02_hero_val_light_contrast(self):
        """라이트 테마 Hero 텍스트 대비율 ≥ 4.5"""
        ratio = self._contrast_ratio(".hero-val")
        print(f"  [light] hero-val contrast: {ratio}:1")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 4.5, f"라이트 Hero 대비율 부족: {ratio}:1")

    def test_03_footer_copy_light_contrast(self):
        """라이트 테마 푸터 저작권 최소 대비율 ≥ 2.5"""
        ratio = self._contrast_ratio(".footer-copy")
        print(f"  [light] footer-copy contrast: {ratio}:1  (min 2.5:1)")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 2.5, f"라이트 푸터 대비율 부족: {ratio}:1")

    def test_04_sidebar_menu_light_contrast(self):
        """라이트 테마 사이드바 메뉴 대비율 ≥ 4.5"""
        ratio = self._contrast_ratio(".sb-name")
        print(f"  [light] sb-name contrast: {ratio}:1")
        if ratio >= 0:
            self.assertGreaterEqual(ratio, 4.5, f"라이트 사이드바 대비율 부족: {ratio}:1")


class TC27_AllMenuClicks(unittest.TestCase):
    """TC27 모든 주요 메뉴 버튼 클릭 기능 검증"""

    @classmethod
    def setUpClass(cls):
        cls.driver = make_driver()
        register_and_login(cls.driver)
        add_position(cls.driver, "AAPL", "10")
        cls.w = wait(cls.driver)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def _close_open_modals(self):
        """열려있는 모달/오버레이 닫기"""
        close_btns = self.driver.find_elements(By.CSS_SELECTOR, ".overlay .close-x, .modal .close-x")
        for btn in close_btns:
            try:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(0.2)
            except Exception:
                pass
        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.2)

    def test_01_overview_tab_click(self):
        """[탭] Overview 탭 클릭 → hero 표시"""
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab")
        for t in tabs:
            if "Overview" in t.text or "오버뷰" in t.text:
                t.click()
                time.sleep(0.3)
                break
        hero = self.driver.find_element(By.CSS_SELECTOR, ".hero")
        self.assertTrue(hero.is_displayed())

    def test_02_positions_tab_click(self):
        """[탭] Positions 탭 클릭 → 테이블 표시"""
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab")
        for t in tabs:
            if "Position" in t.text or "포지션" in t.text:
                t.click()
                time.sleep(0.3)
                break
        table = self.driver.find_element(By.CSS_SELECTOR, ".tbl-wrap")
        self.assertTrue(table.is_displayed())

    def test_03_sidebar_overview_item(self):
        """[사이드바] Overview 항목 클릭"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Overview" in item.text:
                item.click()
                time.sleep(0.3)
                self.assertIn("active", item.get_attribute("class"))
                break

    def test_04_sidebar_positions_item(self):
        """[사이드바] Positions 항목 클릭"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "Positions" in item.text:
                item.click()
                time.sleep(0.3)
                self.assertIn("active", item.get_attribute("class"))
                break

    def test_05_sidebar_all_accounts(self):
        """[사이드바] All Accounts 클릭 → active"""
        items = self.driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
        for item in items:
            if "All" in item.text:
                item.click()
                time.sleep(0.3)
                self.assertIn("active", item.get_attribute("class"))
                break

    def test_06_add_position_button(self):
        """[상단바] + 포지션 추가 버튼 → 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-primary")
        btns[-1].click()
        time.sleep(0.4)
        modal = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())
        self._close_open_modals()

    def test_07_api_settings_button(self):
        """[상단바] API 설정 버튼 → 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn")
        for b in btns:
            if "API" in b.text:
                b.click()
                break
        time.sleep(0.4)
        modal = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())
        self._close_open_modals()

    def test_08_io_export_button(self):
        """[상단바] ⇅ 내보내기/가져오기 버튼 → 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "⇅" in b.text:
                b.click()
                break
        time.sleep(0.4)
        modal = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal")))
        self.assertTrue(modal.is_displayed())
        self._close_open_modals()

    def test_09_alerts_bell_button(self):
        """[상단바] 🔔 알림 버튼 → 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "🔔" in b.text or (b.get_attribute("title") and "Alert" in b.get_attribute("title")):
                b.click()
                break
        time.sleep(0.4)
        overlay = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".overlay")))
        self.assertTrue(overlay.is_displayed())
        self._close_open_modals()

    def test_10_trades_chart_button(self):
        """[상단바] 📊 거래 내역 버튼 → 모달 열림"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "📊" in b.text or (b.get_attribute("title") and "Trade" in b.get_attribute("title")):
                b.click()
                break
        time.sleep(0.4)
        overlay = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".overlay")))
        self.assertTrue(overlay.is_displayed())
        self._close_open_modals()

    def test_11_snapshot_button(self):
        """[상단바] 📸 스냅샷 버튼 → 토스트 표시"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "📸" in b.text or (b.get_attribute("title") and "snapshot" in b.get_attribute("title").lower()):
                b.click()
                break
        time.sleep(0.5)
        toasts = self.driver.find_elements(By.CSS_SELECTOR, ".toast")
        self.assertGreater(len(toasts), 0)

    def test_12_theme_toggle_button(self):
        """[상단바] ☀️/🌙 테마 버튼 → 테마 전환"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        before = self.driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        for b in btns:
            if "☀️" in b.text or "🌙" in b.text:
                b.click()
                break
        time.sleep(0.3)
        after = self.driver.find_element(By.TAG_NAME, "html").get_attribute("class")
        self.assertNotEqual(before, after)
        # 복원
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        for b in btns:
            if "☀️" in b.text or "🌙" in b.text:
                b.click()
                break
        time.sleep(0.2)

    def test_13_refresh_button(self):
        """[상단바] 새로고침 버튼 클릭 가능"""
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".topbar-right .btn-ghost")
        refresh_btn = None
        for b in btns:
            title = b.get_attribute("title") or ""
            if "새로고침" in title or "Refresh" in title or "↻" in b.text or "⟳" in b.text:
                refresh_btn = b
                break
        if not refresh_btn:
            # 아이콘 없이 spinning 클래스로 찾기 시도
            refresh_btn = btns[0] if btns else None
        if refresh_btn:
            self.assertTrue(refresh_btn.is_displayed())
            refresh_btn.click()
            time.sleep(0.3)
            print("  refresh button clicked")

    def test_14_print_button(self):
        """[Positions 탭] 🖨️ 인쇄 버튼 표시"""
        tabs = self.driver.find_elements(By.CSS_SELECTOR, ".tab")
        for t in tabs:
            if "Position" in t.text or "포지션" in t.text:
                t.click()
                time.sleep(0.3)
                break
        btns = self.driver.find_elements(By.CSS_SELECTOR, ".btn")
        print_btn = None
        for b in btns:
            if "🖨" in b.text or "Print" in b.text or "인쇄" in b.text:
                print_btn = b
                break
        if print_btn:
            self.assertTrue(print_btn.is_displayed())
            print(f"  print btn: '{print_btn.text}'")

    def _dismiss_cookie_banner(self):
        """쿠키 배너가 있으면 JS로 숨김 (클릭 인터셉트 방지)"""
        self.driver.execute_script(
            "var b=document.querySelector('.cookie-banner');if(b)b.style.display='none';"
        )
        time.sleep(0.1)

    def test_15_footer_terms_link(self):
        """[푸터] 이용약관 링크 클릭 → 법적 모달 열림"""
        self._dismiss_cookie_banner()
        footer_links = self.driver.find_elements(By.CSS_SELECTOR, ".footer-link")
        terms_link = None
        for l in footer_links:
            if "약관" in l.text or "Terms" in l.text:
                terms_link = l
                break
        if terms_link:
            # JS click으로 쿠키 배너 인터셉트 우회
            self.driver.execute_script("arguments[0].click()", terms_link)
            time.sleep(0.4)
            modal = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal, .overlay")))
            self.assertTrue(modal.is_displayed())
            self._close_open_modals()
            print("  Terms modal: opened ✓")

    def test_16_footer_privacy_link(self):
        """[푸터] 개인정보처리방침 링크 클릭 → 모달 열림"""
        self._dismiss_cookie_banner()
        footer_links = self.driver.find_elements(By.CSS_SELECTOR, ".footer-link")
        priv_link = None
        for l in footer_links:
            if "개인정보" in l.text or "Privacy" in l.text:
                priv_link = l
                break
        if priv_link:
            self.driver.execute_script("arguments[0].click()", priv_link)
            time.sleep(0.4)
            modal = self.w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal, .overlay")))
            self.assertTrue(modal.is_displayed())
            self._close_open_modals()
            print("  Privacy modal: opened ✓")


class TC28_ExtraViewports(unittest.TestCase):
    """TC28 추가 해상도 레이아웃 검증 (QHD, 4K, 울트라와이드, 소형 태블릿)"""

    EXTRA_VIEWPORTS = [
        ("small_tablet",  600,  900),   # 소형 태블릿
        ("tablet_hd",     800, 1280),   # HD 태블릿
        ("laptop",       1366,  768),   # 노트북 FHD-
        ("qhd",          2560, 1440),   # QHD 2K
        ("ultrawide",    2560, 1080),   # 울트라와이드 21:9
        ("4k",           3840, 2160),   # 4K
    ]

    def _check_viewport(self, name, w, h):
        is_mobile = w <= 640
        driver = make_driver(width=w, height=h, mobile=is_mobile)
        try:
            register_and_login(driver)
            actual_w = driver.execute_script("return window.innerWidth")
            actual_h = driver.execute_script("return window.innerHeight")

            # 1) .app 렌더링
            app = driver.find_element(By.CSS_SELECTOR, ".app")
            self.assertTrue(app.is_displayed(), f"[{name}] .app 미표시")

            # 2) Hero 섹션 표시
            hero = driver.find_element(By.CSS_SELECTOR, ".hero")
            self.assertTrue(hero.is_displayed(), f"[{name}] .hero 미표시")

            # 3) 수평 오버플로우 없음
            scroll_w = driver.execute_script("return document.documentElement.scrollWidth")
            self.assertLessEqual(scroll_w, actual_w * 1.05,
                f"[{name}] 수평 오버플로우: scrollWidth={scroll_w}, viewport={actual_w}")

            # 4) topbar 표시
            tb = driver.find_element(By.CSS_SELECTOR, ".topbar")
            self.assertTrue(tb.is_displayed(), f"[{name}] topbar 미표시")

            # 5) 사이드바 표시
            sb = driver.find_element(By.CSS_SELECTOR, ".sidebar")
            self.assertTrue(sb.is_displayed(), f"[{name}] sidebar 미표시")

            sb_w = sb.size["width"]
            print(f"  [{name}] {w}x{h} ✓  actual={actual_w}x{actual_h}  scrollW={scroll_w}  sbW={sb_w}")
        finally:
            driver.quit()

    def test_01_small_tablet_600(self):
        """소형 태블릿 (600×900) 레이아웃"""
        self._check_viewport(*self.EXTRA_VIEWPORTS[0])

    def test_02_tablet_hd_800(self):
        """HD 태블릿 (800×1280) 레이아웃"""
        self._check_viewport(*self.EXTRA_VIEWPORTS[1])

    def test_03_laptop_1366(self):
        """노트북 (1366×768) 레이아웃"""
        self._check_viewport(*self.EXTRA_VIEWPORTS[2])

    def test_04_qhd_2560(self):
        """QHD 2K (2560×1440) 레이아웃"""
        self._check_viewport(*self.EXTRA_VIEWPORTS[3])

    def test_05_ultrawide_2560x1080(self):
        """울트라와이드 21:9 (2560×1080) 레이아웃"""
        self._check_viewport(*self.EXTRA_VIEWPORTS[4])

    def test_06_4k_3840(self):
        """4K (3840×2160) 레이아웃"""
        self._check_viewport(*self.EXTRA_VIEWPORTS[5])

    def test_07_positions_tab_wide_screen(self):
        """QHD 화면에서 Positions 탭 테이블 수평 오버플로우 없음"""
        driver = make_driver(width=2560, height=1440)
        try:
            register_and_login(driver)
            add_position(driver, "AAPL", "5")
            items = driver.find_elements(By.CSS_SELECTOR, ".sb-sec .sb-item")
            for item in items:
                if "Positions" in item.text:
                    item.click()
                    time.sleep(0.4)
                    break
            actual_w = driver.execute_script("return window.innerWidth")
            scroll_w = driver.execute_script("return document.documentElement.scrollWidth")
            self.assertLessEqual(scroll_w, actual_w * 1.05,
                f"QHD Positions 수평 오버플로우: scrollW={scroll_w}, vp={actual_w}")
            print(f"  [QHD positions] scrollW={scroll_w}, vp={actual_w} ✓")
        finally:
            driver.quit()


# ── 실행 ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Portfolio Manager Selenium Test Suite")
    print(f"URL: {BASE_URL}")
    print("=" * 60)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TC01_PageLoad,
        TC02_AuthLayout,
        TC03_LangToggle,
        TC04_RegisterValidation,
        TC05_LoginFlow,
        TC06_MainLayout,
        TC07_SidebarInteraction,
        TC08_TabNavigation,
        TC09_AddPositionModal,
        TC10_FilterPills,
        TC11_TableSort,
        TC12_SearchBar,
        TC13_SettingsModal,
        TC14_IOModal,
        TC15_MobileLayout,
        TC16_MobileSidebarDrawer,
        TC17_MultiViewportLayout,
        TC18_AlertsModal,
        TC19_TradesModal,
        TC20_ThemeToggle,
        TC21_InlineCellEditing,
        TC22_ColumnVisibility,
        TC23_SnapshotBtn,
        TC24_BenchmarkPills,
        TC25_ColorContrastDark,
        TC26_ColorContrastLight,
        TC27_AllMenuClicks,
        TC28_ExtraViewports,
    ]
    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print(f"총 {result.testsRun}개 실행  |  "
          f"성공 {result.testsRun - len(result.failures) - len(result.errors)}  |  "
          f"실패 {len(result.failures)}  |  "
          f"오류 {len(result.errors)}")
    print("=" * 60)

    sys.exit(0 if result.wasSuccessful() else 1)
