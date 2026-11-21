"""육아 퀘스트 v6 검증 — 🧒 36개월+ 유아기 3구간 추가 + 임신/영유아 회귀

python3 qa/test-todd.py [index.html 경로]
"""
import os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "index.html")
URL = "file://" + os.path.abspath(TARGET)
OUT = os.path.join(HERE, "shots")
os.makedirs(OUT, exist_ok=True)

FAIL = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)

def no_overflow(pg, tag):
    over = pg.evaluate("""() => {
      const a = document.getElementById('app');
      const ar = a.getBoundingClientRect();
      const bad = [];
      const scrollable = (el) => {
        let n = el.parentElement;
        while (n && n !== document.body) {
          const ox = getComputedStyle(n).overflowX;
          if (ox === 'auto' || ox === 'scroll') return true;
          n = n.parentElement;
        }
        return false;
      };
      document.querySelectorAll('#app *').forEach(el=>{
        const r = el.getBoundingClientRect();
        if (r.width > 0 && (r.right > ar.right + 1.5) && !scrollable(el)) bad.push(el.className||el.tagName);
      });
      return {scroll: a.scrollWidth > a.clientWidth + 1, bad: bad.slice(0,5),
              doc: document.documentElement.scrollWidth > window.innerWidth + 1};
    }""")
    check(not over["scroll"] and not over["bad"] and not over["doc"], "%s 가로 넘침 없음 %s" % (tag, over["bad"]))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 430, "height": 932}, locale="ko-KR")
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda m: errs.append("CONSOLE " + m.text) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_timeout(400)

    # ---------- 1. 첫 화면 ----------
    check(pg.is_visible("#opIntro"), "첫 화면 인트로 표시")
    check(pg.locator("#opMonthList [data-preg]").count() == 1, "임신 허브 카드 1개")
    tod = pg.locator("#opMonthList [data-todd]")
    check(tod.count() == 1, "유아기 허브 카드 1개")
    ttxt = tod.inner_text()
    check("🧒 36개월+ · 유아기" in ttxt, "유아기 허브 제목 (%s)" % ttxt.replace("\n", " / "))
    check("유치원 입학부터 초등 준비까지" in ttxt, "유아기 허브 부제")
    check("3개 구간" in ttxt, "유아기 허브 구간 수")
    check(pg.locator("#opMonthList .m-pick-card").count() == 12, "카드 총 12개 (허브2 + 월령10) %d" % pg.locator("#opMonthList .m-pick-card").count())
    check(pg.locator("#opMonthList .m-pick-card:not([data-preg]):not([data-todd])").count() == 10, "기존 월령 카드 10개 유지")
    check("18개 구간" in pg.inner_text("#opIntro .op-meta"), "구간 수 18개 표기")
    check("임신 5 · 영유아 10 · 유아기 3" in pg.inner_text("#opIntro .op-meta"), "구간 구성 표기")
    check("72개월+" in pg.inner_text("#opIntro .sub2"), "인트로 배지 문구")
    check("72개월+" in pg.title(), "title 문구 (%s)" % pg.title())
    check("구간별 5문항" in pg.inner_text("#opIntro .sub2"), "'구간별 5문항' 표현 유지")
    no_overflow(pg, "첫 화면 430px")
    pg.screenshot(path=os.path.join(OUT, "01-step1-430.png"))

    # 허브 카드가 맨 끝에 있는지
    order = pg.evaluate("""() => Array.from(document.querySelectorAll('#opMonthList .m-pick-card')).map(e=>e.getAttribute('data-todd')?'todd':(e.getAttribute('data-preg')?'preg':'month'))""")
    check(order[-1] == "todd", "유아기 허브가 맨 끝 (%s)" % order)

    # ---------- 2. 허브 클릭 -> 3구간 ----------
    tod.click(); pg.wait_for_timeout(250)
    check(pg.is_visible("#opTodd"), "유아기 3구간 선택 화면 표시")
    cards = pg.locator("#opToddList .m-pick-card")
    check(cards.count() == 3, "유아기 카드 3개 (%d)" % cards.count())
    txt = pg.inner_text("#opToddList")
    for label in ["37~48개월", "(만 3세)", "49~60개월", "(만 4세)", "61~72개월+", "(만 5세+)"]:
        check(label in txt, "구간 라벨 %s" % label)
    check("유치원 입학" in txt and "또래 갈등" in txt, "k0 주제 문구")
    check("자기주장" in txt and "편식" in txt and "한글" in txt, "k1 주제 문구")
    check("초등 입학 준비" in txt and "규칙" in txt and "독립심" in txt, "k2 주제 문구")
    no_overflow(pg, "유아기 선택 430px")
    pg.screenshot(path=os.path.join(OUT, "02-todd-stages-430.png"))

    pg.set_viewport_size({"width": 360, "height": 740}); pg.wait_for_timeout(200)
    no_overflow(pg, "유아기 선택 360px")
    pg.screenshot(path=os.path.join(OUT, "03-todd-stages-360.png"))
    pg.set_viewport_size({"width": 430, "height": 932}); pg.wait_for_timeout(200)

    # ---------- 3. 49~60개월(k1) 성향 테스트 ----------
    cards.nth(1).click(); pg.wait_for_timeout(350)
    check(pg.is_visible("#opTest"), "성향 테스트 표시")
    check(pg.inner_text("#tMonthChip").strip() == "49~60개월", "테스트 상단 구간 칩 (%s)" % pg.inner_text("#tMonthChip"))
    check("우리 아이 49~60개월" in pg.inner_text("#opTest .note"), "테스트 안내가 아이 기준")
    check("기관 소통" in pg.inner_text("#tQno"), "Q1 = 기관 소통 (%s)" % pg.inner_text("#tQno"))
    n = pg.locator("#tChoices .t-choice").count()
    check(n == 2, "Q1 선택지 2개 (%d)" % n)
    pg.screenshot(path=os.path.join(OUT, "04-todd-test-q1-430.png"))
    pg.click("#tChoices .t-choice >> nth=0"); pg.wait_for_timeout(300)
    check("훈육·협상" in pg.inner_text("#tQno"), "Q2 = 훈육·협상")
    check(pg.locator("#tChoices .t-choice").count() == 2, "Q2 선택지 2개")
    pg.click("#tChoices .t-choice >> nth=1"); pg.wait_for_timeout(300)
    check("또래 갈등" in pg.inner_text("#tQno"), "Q3 = 또래 갈등")
    pg.click("#tChoices .t-choice >> nth=0"); pg.wait_for_timeout(300)
    check("학습·놀이" in pg.inner_text("#tQno"), "Q4 = 학습·놀이")
    pg.click("#tChoices .t-choice >> nth=0"); pg.wait_for_timeout(300)
    check("결정타" in pg.inner_text("#tQno"), "Q5 = 결정타")
    check(pg.locator("#tChoices .t-choice").count() == 4, "Q5 보너스 선택지 4개")
    pg.click("#tChoices .t-choice >> nth=3"); pg.wait_for_timeout(500)
    check(pg.is_visible("#opChar"), "성향 결과 화면 표시")
    cname = pg.inner_text("#charName")
    check(any(k in cname for k in ["기록 집착 전략가", "혼자 다 하는 열정맘", "눈치 백단 즉흥맘", "체력 안배 생존가"]), "4유형 중 하나 (%s)" % cname)
    check("우리 아이 49~60개월" in pg.inner_text("#charMonth"), "결과에 아이 구간 표기 (%s)" % pg.inner_text("#charMonth"))
    check("+5문항" in pg.inner_text("#opMomBtn"), "엄마 챙기기 버튼 (+5문항)")
    pg.screenshot(path=os.path.join(OUT, "05-todd-char-430.png"))

    # ---------- 4. +5문항 (유아기 컨디션 체크) ----------
    pg.click("#opMomBtn"); pg.wait_for_timeout(250)
    check(pg.is_visible("#opMom"), "엄마 컨디션 체크 표시")
    check("몇 시간 자나요" in pg.inner_text("#mText"), "유아기 M1 (수면)")
    pg.click("#mChoices .t-choice >> nth=1"); pg.wait_for_timeout(320)
    check("허리·어깨·손목" in pg.inner_text("#mText"), "유아기 M2 (%s)" % pg.inner_text("#mText"))
    pg.click("#mChoices .t-choice >> nth=1"); pg.wait_for_timeout(320)
    check("물은 몇 번" in pg.inner_text("#mText"), "유아기 M3 (식사·물)")
    pg.click("#mChoices .t-choice >> nth=1"); pg.wait_for_timeout(320)
    check("아이 없이 보낸 시간" in pg.inner_text("#mText"), "유아기 M4 (자유시간)")
    pg.click("#mChoices .t-choice >> nth=1"); pg.wait_for_timeout(320)
    check("소리 지르고" in pg.inner_text("#mText"), "유아기 M5 (마음)")
    pg.click("#mChoices .t-choice >> nth=1"); pg.wait_for_timeout(400)
    check(pg.is_visible("#opMomResult"), "엄마 컨디션 결과 표시")
    check(pg.locator("#momTips li").count() == 3, "회복 팁 3개")
    pg.click("#opMomGo"); pg.wait_for_timeout(450)
    check(pg.is_visible("#tab-quest"), "퀘스트 탭 진입")
    check("49~60개월" in pg.inner_text("#headSub"), "헤더 구간 표기 (%s)" % pg.inner_text("#headSub"))

    # ---------- 5. 퀘스트 완주 도우미 ----------
    def run_stage(idx, label, shot=None):
        pg.click("#monthRow .mchip >> nth=%d" % idx); pg.wait_for_timeout(320)
        if pg.is_visible("#careSheet"):
            pg.click("#careSheet [data-care-pick='daycare']"); pg.wait_for_timeout(250)
        header = pg.inner_text("#headSub")
        check(label in header, "%s 헤더 (%s)" % (label, header))
        check(pg.inner_text("#progAll") == "5", "%s 5문항 표시" % label)
        tags = []
        for q in range(5):
            tags.append(pg.inner_text("#qTag"))
            nc = pg.locator("#choiceList .choice").count()
            if nc != 3:
                check(False, "%s Q%d 선택지 %d" % (label, q + 1, nc))
            pg.click("#choiceList .choice >> nth=0"); pg.wait_for_timeout(150)
            if not pg.is_visible("#fbBox"):
                check(False, "%s Q%d 피드백 없음" % (label, q + 1))
            if q == 0 and shot:
                pg.screenshot(path=os.path.join(OUT, shot))
            pg.click("#nextBtn"); pg.wait_for_timeout(200)
            if pg.is_visible("#rescueView"):
                break
        if pg.is_visible("#rescueView"):
            check(False, "%s 1번 선택지 경로에서 SOS" % label)
            return None, tags
        check(pg.is_visible("#resultView"), "%s 결과 화면" % label)
        res = pg.inner_text("#resultView")
        check("💛 이 시기 엄마 챙기기" in res, "%s 엔딩 엄마 챙기기 박스" % label)
        check("Lv." in res, "%s 결과 레벨" % label)
        check(len(set(tags)) == 5, "%s 태그 5개 모두 다름 (%s)" % (label, " / ".join(tags)))
        return res, tags

    res, tags = run_stage(16, "49~60개월", "06-todd-quest-430.png")
    check(res is not None and "이 구간 도감 열기" in pg.inner_text("#resultView"), "유아기 결과의 도감 버튼 문구")
    check("우리 아이 49~60개월" in pg.inner_text("#resultView"), "결과에 '우리 아이' 표기")
    pg.screenshot(path=os.path.join(OUT, "07-todd-result-430.png"))
    for i, lab in [(15, "37~48개월"), (17, "61~72개월+")]:
        run_stage(i, lab)

    # ---------- 6. 유아기 도감 ----------
    pg.click(".tab[data-tab='dex']"); pg.wait_for_timeout(320)
    for i, lab in [(15, "37~48개월"), (16, "49~60개월"), (17, "61~72개월+")]:
        pg.click("#dexMonthRow .mchip >> nth=%d" % i); pg.wait_for_timeout(250)
        plays = pg.locator("#dexPlays .dex-card").count()
        checks = pg.locator("#dexChecks .check-item").count()
        shop = pg.locator("#dexShop .shop-item").count()
        check(plays == 5, "%s 도감 놀이 5개 (%d)" % (lab, plays))
        check(checks == 4, "%s 체크리스트 4개 (%d)" % (lab, checks))
        check(shop == 3, "%s 아이템 자리 3개 (%d)" % (lab, shop))
    check("🧒" in pg.inner_text("#dexPlayTitle"), "유아기 도감 제목 (%s)" % pg.inner_text("#dexPlayTitle"))
    check("유치원" in pg.inner_text("#dexCheckTitle"), "유아기 체크리스트 제목 (%s)" % pg.inner_text("#dexCheckTitle"))
    body = pg.inner_text("#tab-dex").replace("국민건강보험공단", "")
    check("보험" not in body, "도감에 보험·상품 영업 문구 없음")
    check("영유아검진" in pg.inner_text("#dexChecks") or "검진" in pg.inner_text("#dexChecks"), "검진 체크 항목 존재")
    pg.click("#dexPlays .dex-card >> nth=0 >> .dex-toggle"); pg.wait_for_timeout(200)
    check(pg.inner_text("#dexCnt").strip().startswith("1 /"), "도감 발견 토글 (%s)" % pg.inner_text("#dexCnt"))
    pg.screenshot(path=os.path.join(OUT, "08-todd-dex-430.png"))

    # ---------- 7. 기존 임신·영유아 회귀 ----------
    pg.click(".tab[data-tab='quest']"); pg.wait_for_timeout(200)
    pg.click("#homeBtn"); pg.wait_for_timeout(300)
    check(pg.is_visible("#opIntro"), "🏠 홈 → 첫 화면")
    pg.click("#opMonthList [data-preg]"); pg.wait_for_timeout(250)
    check(pg.is_visible("#opPreg"), "임신 허브 정상")
    check(pg.locator("#opPregList .m-pick-card").count() == 5, "임신 5구간 카드")
    pg.click("#opPregList .m-pick-card >> nth=2"); pg.wait_for_timeout(320)
    check(pg.is_visible("#opTest"), "임신 구간 → 성향 테스트")
    check("20~27주" in pg.inner_text("#tMonthChip"), "임신 테스트 칩")
    check("지금 20~27주" in pg.inner_text("#opTest .note"), "임신 테스트 안내 문구")
    pg.click("#tSkip"); pg.wait_for_timeout(300)
    check(pg.is_visible("#tab-quest"), "테스트 건너뛰기 동작")
    res, _ = run_stage(2, "20~27주")
    check(res is not None and "이 주수 도감 열기" in pg.inner_text("#resultView"), "임신 결과 도감 버튼 유지")
    for i, lab in [(5, "~30일"), (11, "13~18개월"), (14, "31~36개월+")]:
        run_stage(i, lab)
    pg.click(".tab[data-tab='dex']"); pg.wait_for_timeout(300)
    pg.click("#dexMonthRow .mchip >> nth=%d" % 2); pg.wait_for_timeout(250)
    check("🌸" in pg.inner_text("#dexPlayTitle"), "임신 도감 제목 복귀")
    check("산전검사" in pg.inner_text("#dexCheckTitle"), "임신 체크리스트 제목 복귀")
    pg.click("#dexMonthRow .mchip >> nth=%d" % 14); pg.wait_for_timeout(250)
    check("영유아검진" in pg.inner_text("#dexCheckTitle"), "월령 체크리스트 제목 복귀 (%s)" % pg.inner_text("#dexCheckTitle"))

    # 기관 분기 시트 회귀 (새 컨텍스트)
    pg3 = b.new_context(viewport={"width": 430, "height": 932}, locale="ko-KR").new_page()
    pg3.on("pageerror", lambda e: errs.append("PAGEERROR3 " + str(e)))
    pg3.goto(URL); pg3.wait_for_timeout(350)
    pg3.click("#opMonthList .m-pick-card:not([data-preg]):not([data-todd]) >> nth=0"); pg3.wait_for_timeout(300)
    pg3.click("#tSkip"); pg3.wait_for_timeout(300)
    pg3.click("#monthRow .mchip >> nth=%d" % 11); pg3.wait_for_timeout(400)
    check(pg3.is_visible("#careSheet"), "13~18개월 기관 선택 시트")
    pg3.click("#careSheet [data-care-pick='daycare']"); pg3.wait_for_timeout(350)
    check(pg3.is_visible("#playView"), "기관 선택 후 퀘스트 진행")

    # 유아기 구간은 기관 시트를 띄우지 않아야 함
    pg3.click("#monthRow .mchip >> nth=16"); pg3.wait_for_timeout(400)
    check(not pg3.is_visible("#careSheet"), "유아기 구간은 기관 시트 없음")
    check("49~60개월" in pg3.inner_text("#headSub"), "유아기 칩 전환 헤더")

    # ---------- 8. 새로고침 후 저장 상태 (유아기 구간을 마지막으로 선택) ----------
    pg.click(".tab[data-tab='quest']"); pg.wait_for_timeout(200)
    pg.click("#homeBtn"); pg.wait_for_timeout(300)
    pg.click("#opMonthList [data-todd]"); pg.wait_for_timeout(250)
    pg.click("#opToddList .m-pick-card >> nth=1"); pg.wait_for_timeout(320)
    check("49~60개월" in pg.inner_text("#tMonthChip"), "유아기 재선택 → 테스트")
    pg.click("#tSkip"); pg.wait_for_timeout(300)
    pg.reload(); pg.wait_for_timeout(450)
    check(pg.is_visible("#opIntro"), "새로고침 후 인트로")
    last = pg.inner_text("#opMonthList [data-todd]")
    check("지난번" in last, "유아기 구간이 지난번 선택으로 표시 (%s)" % last.replace("\n", " / "))
    pg.click("#opMonthList [data-todd]"); pg.wait_for_timeout(250)
    tt = pg.inner_text("#opToddList")
    check("지난번 선택" in tt, "유아기 목록에 지난번 선택 표시")
    check(pg.locator("#opToddList .m-pick-card[aria-pressed='true']").count() == 1, "선택 구간 aria-pressed")
    pg.click("#opToddBack"); pg.wait_for_timeout(250)
    check(pg.is_visible("#opIntro"), "유아기 → 월령·구간 다시 고르기")

    # ---------- 9. 360px 전 화면 ----------
    pg2 = b.new_context(viewport={"width": 360, "height": 740}, locale="ko-KR").new_page()
    pg2.on("pageerror", lambda e: errs.append("PAGEERROR360 " + str(e)))
    pg2.goto(URL); pg2.wait_for_timeout(400)
    no_overflow(pg2, "360 첫 화면")
    pg2.click("#opMonthList [data-todd]"); pg2.wait_for_timeout(250)
    no_overflow(pg2, "360 유아기 선택")
    pg2.click("#opToddList .m-pick-card >> nth=2"); pg2.wait_for_timeout(300)
    no_overflow(pg2, "360 성향 테스트")
    pg2.screenshot(path=os.path.join(OUT, "09-todd-test-360.png"))
    for _ in range(5):
        pg2.click("#tChoices .t-choice >> nth=0"); pg2.wait_for_timeout(280)
    check(pg2.is_visible("#opChar"), "360 성향 결과")
    no_overflow(pg2, "360 캐릭터 결과")
    pg2.screenshot(path=os.path.join(OUT, "10-todd-char-360.png"))
    pg2.click("#opGo"); pg2.wait_for_timeout(400)
    no_overflow(pg2, "360 퀘스트")
    pg2.screenshot(path=os.path.join(OUT, "11-todd-quest-360.png"))
    for _ in range(5):
        pg2.click("#choiceList .choice >> nth=0"); pg2.wait_for_timeout(150)
        pg2.click("#nextBtn"); pg2.wait_for_timeout(200)
    check(pg2.is_visible("#resultView"), "360 결과 화면")
    no_overflow(pg2, "360 결과")
    pg2.screenshot(path=os.path.join(OUT, "12-todd-result-360.png"))
    pg2.click(".tab[data-tab='dex']"); pg2.wait_for_timeout(300)
    no_overflow(pg2, "360 도감")

    check(not errs, "콘솔/페이지 에러 0 (%s)" % errs[:3])
    b.close()

print("\n==== SUMMARY ====")
print("FAILURES:", len(FAIL))
for f in FAIL:
    print(" -", f)
sys.exit(1 if FAIL else 0)
