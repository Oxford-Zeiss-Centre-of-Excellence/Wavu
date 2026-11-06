---
title: 홈
hide:
  - navigation
  - toc
---

# Wavu: 이미지 뷰어 안에서 쓰는 나의 Python

*Wavu*는 피지어로 **다리**라는 뜻이에요. 이미지를 보는 뷰어, 곧 **Fiji**나
**napari**를, Cellpose나 scikit-image 같은 도구가 있는 Python과 이어 줘요.

레스토랑을 떠올려 보세요. **뷰어는 웨이터**예요. 주문(입력란 몇 개가 있는
대화상자)을 받고, 이미지를 **재료**로 주방에 날라 주고, 요리(새 이미지, 표,
윤곽선)를 테이블로 가져다줘요. **워커(worker)는 문 뒤의 주방**이고,
레시피마다 **자기만의 주방 도구**, 곧 자기만의 냄비, 칼, 오븐(Python
패키지)이 있어요. 그래서 Cellpose 레시피가 블러 레시피의 도구를 빌리거나
망가뜨리는 일은 없어요. 같은 레시피를 어느 웨이터든 내갈 수 있어요.

![웨이터 (프론트엔드): wavu-fiji, wavu-napari → 주방 (백엔드): wavu 워커, 나의 script.py PARAMS + run(), 자기만의 pixi 환경 (주방 도구) — 선택: 주방 전체를 컨테이너에 (Docker / Apptainer)](assets/img/home-model.svg){ width="1000" }

**스크립트 폴더 하나, 뷰어 둘.** `script.py`는 한 번만 쓰면 돼요. Fiji
사용자도 napari 사용자도 그것을 실행하고, 매번 그 폴더만의 환경에서 돌아요.

## Wavu가 필요한 이유 { #why-this-exists }

- **모든 것을 한 환경에 넣으면 망가져요.** napari 환경에 Cellpose 플러그인을
  `pip install`하면 다른 버전의 PyTorch, NumPy, Qt가 함께 들어올 수 있어요.
  다음 플러그인은 또 다른 버전을 고정하고, napari나 동료의 도구가 실행되지
  않게 돼요. 한 환경에서 `conda`와 `pip`를 섞으면 더 나빠져요.
- **Fiji 안의 Python은 더 어려워요.** Fiji 기본 스크립트 언어는 Jython
  (Python 2.7, NumPy 없음)이에요. PyImageJ 같은 연결 도구를 쓰면 컴퓨터마다
  Java, conda, 패키지 버전을 손으로 맞춰야 해요.
- **Wavu의 답:** 뷰어는 작고 깨끗하게 유지되고, 스크립트마다 자기
  `pixi.lock`으로 만든 **자기만의 pixi 환경**에서 실행돼요. 스크립트끼리
  패키지를 공유하지 않으니 서로도, napari나 Fiji도 망가뜨릴 수 없고, 같은
  폴더는 어느 컴퓨터에서나 똑같이 설치돼요.

## 다리만이 아니에요: 스크립트로 짜는 분석 전체

Wavu는 내 스크립트가 부를 수 있는 **함수 호출**이기도 해요. Groovy
스크립트, ImageJ 매크로, Python 노트북이 폴더를 돌면서 기본 단계(열기,
전처리, 측정, 저장)는 직접 하고, Cellpose 같은 무거운 단계만 Wavu에 맡겨요.
Wavu는 그것을 자기 환경에서 실행하고 결과를 스크립트로 돌려줘요. 스크립트
하나로 폴더 전체를, 매번 똑같이 처리해요.

[스크립트 워크플로 :material-arrow-right:](workflows/index.md){ .md-button .md-button--primary }

## 어디서 시작할까요?

<div class="grid cards" markdown>

-   :material-lightbulb-outline:{ .lg .middle } **작동 방식 이해하기**

    ---

    웨이터, 주방, 주방 도구: 무엇이 어디서 실행되는지, 왜 패키지가
    서로 충돌하지 않는지 알아봐요.

    [:octicons-arrow-right-24: 작동 방식](model/what-is-wavu.md)

-   :material-pencil-outline:{ .lg .middle } **스크립트 작성하기**

    ---

    노트북을 메뉴 항목으로 바꿔 보세요. 테스트부터 시작해요. 미리 만들어 둔
    기본 틀을 클릭 한 번으로 받을 수 있어요.

    [VS Code에서 템플릿 열기](vscode://vscode.git/clone?url=https%3A%2F%2Fgithub.com%2FOxford-Zeiss-Centre-of-Excellence%2FWavu-Script-Template.git){ .md-button .md-button--primary }

    [:octicons-arrow-right-24: 템플릿 받기](write/get-the-template.md)

-   :material-microscope:{ .lg .middle } **Fiji에서 쓰기**

    ---

    wavu-fiji를 설치하고, 샘플 이미지로 첫 스크립트를 실행하고, zip 파일
    하나로 연구실과 도구를 공유해요.

    [:octicons-arrow-right-24: wavu-fiji](fiji/install.md)

-   :material-layers-outline:{ .lg .middle } **napari에서 쓰기**

    ---

    Wavu 패널과 함께 napari를 시작해요. 결과는 Image, Labels, Shapes
    레이어로 돌아와요.

    [:octicons-arrow-right-24: wavu-napari](napari/install.md)

</div>

## 알아 두면 좋은 점

- **데이터는 어느 정도까지?** 대화형 사용은 메모리에 들어가는 이미지
  한 장, 대략 1–2 GB가 기준이에요. 청크 단위 스트림 처리(OME-Zarr)를 쓰면
  로컬 컴퓨터에서 약 50 GB까지 다룰 수 있지만, **중요한 주의점**이 있어요.
  Fiji와 napari는 메모리 속 데이터를 전제로 한 캔버스 기반 뷰어라서,
  스트림 동안에는 작은 미리보기나 최종 결과만 보이고, 느리며, 스트림을
  조종하기에 권장되는 곳이 아니에요. 약 50 GB를 넘으면 배치나 HPC
  파이프라인을 쓰세요.
- **스크립트마다 자기 환경이 있어요.** 그래서 PyTorch 스크립트와 NumPy만
  쓰는 스크립트가 서로 충돌하지 않아요.
- **어떻게 만들어졌는지 궁금한가요?** [아키텍처](model/architecture.md)
  페이지에서 워커, 워커의 HTTP 프로토콜, 뷰어가 워커를 시작하는 방법을
  설명해요.

아이디어부터 Fiji 플러그인 출시까지 모든 내용을 보고 싶다면
[GitHub의 전체 가이드](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/blob/main/docs/tutorial-cellpose-plugin.md)(영어)를
읽어 보세요.
