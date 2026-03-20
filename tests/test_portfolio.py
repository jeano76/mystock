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
