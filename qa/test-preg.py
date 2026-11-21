"""육아 퀘스트 v5 검증 — 🤰 출산 전·임신 준비 5구간 추가 + 기존 10개 월령 회귀

python3 qa/test-preg.py [index.html 경로]
"""
import os, sys, json
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

PREG_IDS = ["p0", "p1", "p2", "p3", "p4"]

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
    hub = pg.locator("#opMonthList [data-preg]")
    check(hub.count() == 1, "임신 준비 허브 카드 1개")
    hub_txt = hub.inner_text()
    check("🤰 출산 전 · 임신 준비" in hub_txt, "허브 카드 제목 (%s)" % hub_txt.replace("\n", " / "))
    check("주수별 5문항" in hub_txt, "허브 카드 부제에 주수별 5문항")
    check(pg.locator("#opMonthList .m-pick-card:not([data-preg])").count() == 10,
          "기존 월령 카드 10개 유지 (%d)" % pg.locator("#opMonthList .m-pick-card:not([data-preg])").count())
    check("임신 준비~36개월+" in pg.inner_text("#opIntro .sub2"), "인트로 배지 문구")
    check("임신 준비~36개월+" in pg.title(), "title 문구 (%s)" % pg.title())
    no_overflow(pg, "첫 화면 430px")
    pg.screenshot(path=os.path.join(OUT, "01-step1-430.png"))

    # ---------- 2. 허브 클릭 -> 주수 5구간 ----------
    hub.click(); pg.wait_for_timeout(250)
    check(pg.is_visible("#opPreg"), "주수 5구간 선택 화면 표시")
    cards = pg.locator("#opPregList .m-pick-card")
    check(cards.count() == 5, "주수 카드 5개 (%d)" % cards.count())
    txt = pg.inner_text("#opPregList")
    for label in ["~12주", "13~19주", "20~27주", "28~35주", "36주~출산"]:
        check(label in txt, "주수 라벨 %s" % label)
    for kw in ["임신 확인·입덧·엽산·1차 기형아검사", "조리원 예약·성별 확인", "태동·정밀초음파·임당 검사", "백일해 주사·출산용품", "막달검사·출산가방"]:
        found = any(kw.split("·")[0] in txt for _ in [0])
        check(found, "주수 설명 키워드 %s" % kw)
    no_overflow(pg, "주수 선택 430px")
    pg.screenshot(path=os.path.join(OUT, "02-preg-stages-430.png"))

    # 360px 확인
    pg.set_viewport_size({"width": 360, "height": 740}); pg.wait_for_timeout(200)
    no_overflow(pg, "주수 선택 360px")
    pg.screenshot(path=os.path.join(OUT, "03-preg-stages-360.png"))
    pg.set_viewport_size({"width": 430, "height": 932}); pg.wait_for_timeout(200)

    # ---------- 3. 20~27주(p2) 선택 -> 성향 테스트 5문항 ----------
    cards.nth(2).click(); pg.wait_for_timeout(300)
    check(pg.is_visible("#opTest"), "성향 테스트 표시")
    check(pg.inner_text("#tMonthChip").strip() == "20~27주", "테스트 상단 주수 칩 (%s)" % pg.inner_text("#tMonthChip"))
    check("지금 20~27주" in pg.inner_text("#opTest .note"), "테스트 안내 문구가 주수 기준")
    qt = pg.inner_text("#tText")
    check("출산준비물" in pg.inner_text("#tQno"), "Q1 = 출산준비물 (%s)" % pg.inner_text("#tQno"))
    pg.screenshot(path=os.path.join(OUT, "04-preg-test-q1-430.png"))
    # Q2 에 남편 분담 문항
    pg.click("#tChoices .t-choice >> nth=0"); pg.wait_for_timeout(300)
    check("남편 분담" in pg.inner_text("#tQno"), "Q2 = 남편 분담 (%s)" % pg.inner_text("#tQno"))
    check("남편" in pg.inner_text("#tText"), "Q2 문항에 남편 언급")
    pg.screenshot(path=os.path.join(OUT, "05-preg-test-q2-husband-430.png"))
    # 나머지 3문항 (S,F,A,B 조합 -> SA 유형 목표: 1=S,2=A,3=S,4=A,5=bonus0=S)
    pg.click("#tChoices .t-choice >> nth=1"); pg.wait_for_timeout(300)  # q2 -> B
    pg.click("#tChoices .t-choice >> nth=1"); pg.wait_for_timeout(300)  # q3 -> F
    pg.click("#tChoices .t-choice >> nth=0"); pg.wait_for_timeout(300)  # q4 -> A
    pg.click("#tChoices .t-choice >> nth=0"); pg.wait_for_timeout(500)  # q5 bonus -> S
    check(pg.is_visible("#opChar"), "성향 결과 화면 표시")
    cname = pg.inner_text("#charName")
    check(any(n in cname for n in ["기록 집착 전략가", "혼자 다 하는 열정맘", "눈치 백단 즉흥맘", "체력 안배 생존가"]),
          "4유형 중 하나 (%s)" % cname)
    check("지금 20~27주" in pg.inner_text("#charMonth"), "결과에 주수 표기 (%s)" % pg.inner_text("#charMonth"))
    check("+5문항" in pg.inner_text("#opMomBtn"), "엄마 챙기기 버튼 (+5문항)")
    pg.screenshot(path=os.path.join(OUT, "06-preg-char-430.png"))

    # ---------- 4. +5문항 (임신용 컨디션 체크) ----------
    pg.click("#opMomBtn"); pg.wait_for_timeout(250)
    check(pg.is_visible("#opMom"), "엄마 컨디션 체크 표시")
    check("몇 시간 자나요" in pg.inner_text("#mText"), "임신용 컨디션 M1 (수면)")
    pg.click("#mChoices .t-choice >> nth=1"); pg.wait_for_timeout(320)
    check("허리·손목·다리" in pg.inner_text("#mText"), "임신용 컨디션 M2 (%s)" % pg.inner_text("#mText"))
    for _ in range(4):
        pg.click("#mChoices .t-choice >> nth=2"); pg.wait_for_timeout(280)
    check(pg.is_visible("#opMomResult"), "엄마 컨디션 결과 표시")
    check("출산 준비" in pg.inner_text("#momTips"), "임신용 회복 팁 (출산 준비 분담)")
    pg.screenshot(path=os.path.join(OUT, "07-preg-momresult-430.png"))
    pg.click("#opMomGo"); pg.wait_for_timeout(400)
    check(pg.is_visible("#tab-quest"), "퀘스트 탭 진입")

    # ---------- 5. 주수별 퀘스트 5문항 완주 ----------
    def run_stage(idx, label, shot=None):
        pg.click("#monthRow .mchip >> nth=%d" % idx); pg.wait_for_timeout(300)
        if pg.is_visible("#careSheet"):
            pg.click("#careSheet [data-care-pick='daycare']"); pg.wait_for_timeout(250)
        header = pg.inner_text("#headSub")
        check(label in header, "%s 헤더 (%s)" % (label, header))
        check(pg.inner_text("#progAll") == "5", "%s 5문항 표시" % label)
        for q in range(5):
            pg.click("#choiceList .choice >> nth=0"); pg.wait_for_timeout(140)
            check(pg.is_visible("#fbBox"), "%s Q%d 피드백" % (label, q + 1))
            if q == 0 and shot:
                pg.screenshot(path=os.path.join(OUT, shot))
            pg.click("#nextBtn"); pg.wait_for_timeout(180)
            if pg.is_visible("#rescueView"):
                break
        if pg.is_visible("#rescueView"):
            check(False, "%s 1번 선택지 경로에서 SOS (게이지 0)" % label)
            return
        check(pg.is_visible("#resultView"), "%s 결과 화면" % label)
        res = pg.inner_text("#resultView")
        check("💛 이 시기 엄마 챙기기" in res, "%s 엔딩 엄마 챙기기 박스" % label)
        check("Lv." in res, "%s 결과 레벨" % label)
        return res

    for i, lab in enumerate(["~12주", "13~19주", "20~27주", "28~35주", "36주~출산"]):
        res = run_stage(i, lab, "08-quest-%d-430.png" % i if i == 2 else None)
        if res is None:
            continue
        if i == 2:
            pg.screenshot(path=os.path.join(OUT, "09-result-p2-430.png"))

    # ---------- 6. 도감 (임신 주수) ----------
    pg.click(".tab[data-tab='dex']"); pg.wait_for_timeout(300)
    for i, lab in enumerate(["~12주", "13~19주", "20~27주", "28~35주", "36주~출산"]):
        pg.click("#dexMonthRow .mchip >> nth=%d" % i); pg.wait_for_timeout(250)
        plays = pg.locator("#dexPlays .dex-card").count()
        checks = pg.locator("#dexChecks .check-item").count()
        shop = pg.locator("#dexShop .shop-item").count()
        check(plays == 5, "%s 도감 놀이 5개 (%d)" % (lab, plays))
        check(checks == 4, "%s 체크리스트 4개 (%d)" % (lab, checks))
        check(shop == 3, "%s 쿠파스 자리 3개 (%d)" % (lab, shop))
        title = pg.inner_text("#dexCheckTitle")
        check("산전검사" in title, "%s 체크리스트 제목 (%s)" % (lab, title))
    check("🌸" in pg.inner_text("#dexPlayTitle"), "주수 도감 제목 (%s)" % pg.inner_text("#dexPlayTitle"))
    check(pg.is_visible("#tab-dex .disclosure"), "쿠팡 파트너스 고지 유지")
    pg.click("#dexPlays .dex-card >> nth=0 >> .dex-toggle"); pg.wait_for_timeout(200)
    check(pg.inner_text("#dexCnt").strip().startswith("1 /"), "도감 발견 토글 (%s)" % pg.inner_text("#dexCnt"))
    pg.screenshot(path=os.path.join(OUT, "10-dex-preg-430.png"))
    # 보험/상품 영업 문구 금지 확인
    body = pg.inner_text("#tab-dex")
    check("보험" not in body, "도감에 보험 문구 없음")

    # ---------- 7. 기존 10개 월령 회귀 ----------
    months = ["~30일", "31~60일", "61~100일", "4~6", "7~9", "10~12", "13~18", "19~24", "25~30", "31~36개월+"]
    pg.click(".tab[data-tab='quest']"); pg.wait_for_timeout(200)
    for k, lab in enumerate(months):
        idx = 5 + k
        run_stage(idx, lab)
    # 기관 분기 (13개월+) 시트
    # 기관 분기 시트는 care 선택이 비어 있을 때 뜬다 → 새 컨텍스트로 확인
    pg3 = b.new_context(viewport={"width": 430, "height": 932}, locale="ko-KR").new_page()
    pg3.on("pageerror", lambda e: errs.append("PAGEERROR3 " + str(e)))
    pg3.goto(URL); pg3.wait_for_timeout(350)
    pg3.click("#opMonthList .m-pick-card:not([data-preg]) >> nth=0"); pg3.wait_for_timeout(300)
    pg3.click("#tSkip"); pg3.wait_for_timeout(300)
    check(pg3.is_visible("#tab-quest"), "테스트 건너뛰고 퀘스트 진입")
    pg3.click("#monthRow .mchip >> nth=%d" % (5 + 6)); pg3.wait_for_timeout(400)
    check(pg3.is_visible("#careSheet"), "13~18개월 기관 선택 시트")
    pg3.click("#careSheet [data-care-pick='daycare']"); pg3.wait_for_timeout(350)
    check(pg3.is_visible("#playView"), "기관 선택 후 퀘스트 진행")
    pg.click(".tab[data-tab='dex']"); pg.wait_for_timeout(300)
    check(pg.is_visible("#dexCareWrap .branch-sec"), "어린이집 분기 체크리스트 표시")
    check("영유아검진" in pg.inner_text("#dexCheckTitle"), "월령 체크리스트 제목 복귀 (%s)" % pg.inner_text("#dexCheckTitle"))
    pg.screenshot(path=os.path.join(OUT, "11-month-dex-430.png"))

    # ---------- 8. 홈 버튼 ----------
    pg.click("#homeBtn"); pg.wait_for_timeout(300)
    check(pg.is_visible("#opIntro"), "🏠 홈 → 첫 화면")
    check(pg.locator("#opMonthList [data-preg]").is_visible(), "홈에서 임신 허브 카드 재노출")

    # ---------- 9. 새로고침 후 상태 ----------
    pg.reload(); pg.wait_for_timeout(400)
    check(pg.is_visible("#opIntro"), "새로고침 후 인트로")
    last = pg.inner_text("#opMonthList [data-preg]")
    check("지난번" in last, "임신 구간이 지난번 선택으로 표시 (%s)" % last.replace("\n", " / "))

    # ---------- 10. 360px 전체 화면 넘침 ----------
    pg2 = b.new_context(viewport={"width": 360, "height": 740}, locale="ko-KR").new_page()
    pg2.on("pageerror", lambda e: errs.append("PAGEERROR360 " + str(e)))
    pg2.goto(URL); pg2.wait_for_timeout(400)
    no_overflow(pg2, "360 첫 화면")
    pg2.click("#opMonthList [data-preg]"); pg2.wait_for_timeout(250)
    no_overflow(pg2, "360 주수 선택")
    pg2.click("#opPregList .m-pick-card >> nth=4"); pg2.wait_for_timeout(300)
    no_overflow(pg2, "360 성향 테스트")
    pg2.screenshot(path=os.path.join(OUT, "12-preg-test-360.png"))

    check(not errs, "콘솔/페이지 에러 0 (%s)" % errs[:3])

    # 임신 5구간 문항 구조 (UI 레벨: 각 문항 선택지 3개)
    pg4 = b.new_context(viewport={"width": 430, "height": 932}, locale="ko-KR").new_page()
    pg4.on("pageerror", lambda e: errs.append("PAGEERROR4 " + str(e)))
    pg4.goto(URL); pg4.wait_for_timeout(300)
    pg4.click("#opMonthList .m-pick-card:not([data-preg]) >> nth=0"); pg4.wait_for_timeout(250)
    pg4.click("#tSkip"); pg4.wait_for_timeout(250)
    strict = True
    qtexts = {}
    for idx in range(5):
        pg4.click("#monthRow .mchip >> nth=%d" % idx); pg4.wait_for_timeout(250)
        texts = []
        for q in range(5):
            n = pg4.locator("#choiceList .choice").count()
            if n != 3:
                strict = False
                print("   ! stage %d Q%d 선택지 %d" % (idx, q + 1, n))
            texts.append(pg4.inner_text("#qTag"))
            pg4.click("#choiceList .choice >> nth=1"); pg4.wait_for_timeout(110)
            pg4.click("#nextBtn"); pg4.wait_for_timeout(150)
        qtexts[idx] = texts
    check(strict, "임신 5구간 × 5문항 모두 선택지 3개")
    for idx, t in qtexts.items():
        print("   preg", idx, "/".join(t))
        check(len(set(t)) == 5, "임신 구간 %d 태그 5개 모두 다름" % idx)
    check(not errs, "최종 콘솔/페이지 에러 0 (%s)" % errs[:3])
    b.close()

print("\n==== SUMMARY ====")
print("FAILURES:", len(FAIL))
for f in FAIL:
    print(" -", f)
sys.exit(1 if FAIL else 0)
