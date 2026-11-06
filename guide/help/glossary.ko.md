# 용어집

## 쉬운 말로 설명하면

어느 분야에나 전문 용어가 있어요. Wavu의 단어를 하나씩, 쉬운 한 줄로
설명했어요. 도움이 되는 곳에는 레스토랑 그림도 함께 붙였어요.

![레스토랑 비유: Fiji는 웨이터, 워커는 주방, 레시피마다 자기만의 주방 도구가 있어요](../assets/img/restaurant.svg){ width="560" }

## 단어

**Fiji**
:   이미 쓰고 있는 이미지 분석 프로그램이에요(플러그인이 든 ImageJ). Wavu에서는
    *웨이터*예요. 대화상자가 들어가고 결과가 나와요.

**Wavu**
:   피지어로 "다리". Fiji의 메뉴 항목과, Fiji를 Python 스크립트에 이어 주는
    작은 Python 도우미를 합친 거예요.

**스크립트(Script)**
:   `PARAMS`와 `run` 함수가 있는 `.py` 파일. *레시피*예요.

**스크립트 폴더(Script folder)**
:   `pixi.toml`과 스크립트 하나 이상이 든 폴더. **Run Python Script**에서
    고르는 것이에요.

**PARAMS**
:   스크립트 맨 위에서 대화상자 입력란을 설명하는 목록. *메뉴판*이에요.

**`run(ctx, inputs, params)`**
:   Wavu가 부르는 함수. `inputs`에는 이미지가, `params`에는 나머지 설정이
    들어 있고, `ctx`는 Fiji로 이어진 연락선이에요.

**ctx**
:   "context"(맥락)의 줄임말. `ctx.log`, `ctx.progress`, `ctx.cancelled` 등이
    있어요.

**워커(Worker)**
:   Fiji가 요청하면 스크립트를 실행하는, *여러분의* 컴퓨터 위의 작은 Python
    프로그램. *주방*이에요. Fiji와는 내 컴퓨터 안에서만 이야기해요.

**환경(Environment)**
:   정확히 한 가지 Python과 스크립트 하나에 필요한 패키지를 담은 전용 폴더로,
    스크립트 폴더 안의 `.pixi`에 있어요. 레시피의
    *주방 도구*, 곧 자기만의 냄비, 칼, 오븐이에요.

**pixi**
:   환경을 만들고 패키지를 내려받는 무료 도구로, conda를 대신하는 요즘
    도구예요. Wavu가 대신 가져와 줘요.

**`pixi.toml`**
:   *주방 도구 목록*: 스크립트에 필요한 패키지들.

**잠금 파일(Lock file, `pixi.lock`)**
:   주방 도구의 *영수증*: 모든 패키지의 정확한 버전. 이걸 공유하면 모두가 같은 환경을
    받아요.

**conda-forge / PyPI**
:   Python 패키지를 파는 두 큰 온라인 "가게". pixi는 기본으로 conda-forge를
    쓰고, PyPI는 `pip`이 장을 보는 곳이에요.

**NumPy 배열(NumPy array)**
:   Python의 숫자 격자. 스크립트가 이미지를 받고 돌려주는 형태예요.

**라벨(라벨 이미지)**
:   물체마다 자기 정수(1, 2, 3 …)를 갖고 배경은 0인 이미지. Fiji는 무작위의
    밝은 색으로 보여 줘요.

**ROI**
:   "관심 영역"(region of interest): 이미지 위에 그린 윤곽선. Fiji는 이걸
    **ROI Manager**에 보관하고, *RoiSet*은 ROI가 가득 든 zip 파일이에요.

**협력적 취소(Cooperative cancel)**
:   Esc가 깃발을 올리면 스크립트가 그걸 확인하고 스스로 멈춰요.

**중단점(Breakpoint)**
:   VS Code에서 실행 중인 스크립트가 멈추는 빨간 점. 안을 들여다볼 수 있어요.

**태그 / 릴리스(Tag / release)**
:   코드에 붙인 `v1.0.0` 같은 버전 라벨과, GitHub가 그에 맞춰 만드는 다운로드
    페이지.

**CI**
:   "지속적 통합"(continuous integration): 태그를 push하면 코드를 테스트하고
    패키징하는 GitHub의 로봇. 선택 사항이에요.

**업데이트 사이트(Update site)**
:   **Help › Update…**에서 체크해서 플러그인을 설치하고 업데이트하는 Fiji의
    다운로드 출처.

## 한 문장으로

Fiji는 웨이터, 워커는 주방, 스크립트는 레시피, 이미지는 재료, 그 pixi
환경은 주방 도구, `pixi.lock`은 영수증이에요.
