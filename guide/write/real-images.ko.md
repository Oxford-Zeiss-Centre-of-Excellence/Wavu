# 실제 이미지

## 쉬운 말로 설명하면

*Blobs*는 평평한 그림 한 장이에요. 현미경 이미지는 흔히 **그림 더미**예요.
여러 색 채널, 여러 초점면(z-stack), 어쩌면 여러 시점까지 있어요. Wavu는 그
**더미 전체**를 NumPy 배열 하나로 스크립트에 넘겨주고, 뷰어가 알고 있다면 어떻게
쌓였는지도 알려 줘요. 슬라이드 상자를 받으면서 어느 방향으로 정리됐는지 적힌 라벨도
함께 받는 것과 같아요.

![이미지 평면 더미: 시간, z, 채널, 그다음 y와 x](../assets/img/axes.svg){ width="640" }

## 배열의 모양

=== "Fiji"

    축은 언제나 이 순서로 오고, 길이가 1인 축은 빠져요.

    **T**(시간) · **Z**(평면) · **C**(채널) · **Y** · **X**, 그리고 RGB
    컬러 이미지라면 마지막에 길이 3인 축 **S**가 붙어요.

    | Fiji의 이미지 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 2차원 회색 이미지 한 장, 512 × 512 | `(512, 512)` | `"YX"` |
    | 채널 3개 | `(3, 512, 512)` | `"CYX"` |
    | 평면 20개짜리 z-stack, 채널 2개 | `(20, 2, 512, 512)` | `"ZCYX"` |
    | RGB 사진 | `(512, 512, 3)` | `"YXS"` |

    그러니 `ZCYX` 이미지에서 "모든 평면의 채널 2"는 `img[:, 1]`이에요.
    Fiji는 8-bit, 16-bit, 32-bit, RGB 픽셀을 바꾸지 않고 그대로 보내요.

=== "napari"

    고른 레이어의 데이터를 레이어 자신의 축 순서 그대로 받아요. z-stack
    레이어는 `(20, 512, 512)`로 와요. napari는 보통 채널마다 레이어를 따로
    여니, 원하는 채널을 고르세요.

    | napari의 레이어 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
    |---|---|---|
    | 2차원 회색 이미지 한 장 | `(512, 512)` | `"YX"` |
    | 평면 20개짜리 z-stack | `(20, 512, 512)` | 레이어의 축 라벨이 z, y, x라면 `"ZYX"`, 아니면 설정되지 않아요 |
    | RGB 사진 | `(512, 512, 3)` | `"YXS"` |

    **multiscale** 레이어(이미지 피라미드)는 최고 해상도 단계를 보내요.
    2차원 레이어와 RGB 레이어에는 언제나 축 글자가 붙어요. 더 큰 레이어는
    OME-Zarr 리더가 설정하듯 napari의 축 라벨이 평범한 글자(t, z, c, y, x)일
    때만 붙어요. 그러니 축은 `.get("axes")`로 읽고, `img.ndim`과
    `img.shape`도 살펴보세요.

## 그 밖에 받는 것: `ctx.meta`

`ctx.meta["image"]`에는 `"image"` 입력란에서 고른 이미지에 대해 뷰어가 아는
정보가 들어 있어요.

- `"axes"`: 위와 같은 축 글자(Fiji에서는 언제나, napari에서는 2차원·RGB
  레이어와 축 라벨이 t/z/c/y/x인 더 큰 레이어에서);
- `"pixel_um"`: 알 수 있다면 마이크로미터 단위의 픽셀 크기. Fiji에서는
  이미지의 보정에서, napari에서는 레이어의 **scale**에서 가져와요(마지막
  두 값이 같고 1이 아닐 때);
- `"title"`: 창 제목(Fiji) 또는 레이어 이름(napari).

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"].get("axes")      # 뷰어가 알려 주지 않으면 None
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel")
    ...
```

모양을 확인하고 분명한 `ValueError`를 내는 편이 나중에 코드가 엉뚱하게
죽는 것보다 친절해요. Fiji는 그 문장을 오류 창에, napari는 패널 로그와
알림에 보여 주거든요.

??? tip "축 순서: T C Z Y X 권장(저장, 전달, 계산)"

    Wavu는 아무것도 다시 정렬하지 않아요. Fiji는 **T Z C Y X**(ImageJ
    하이퍼스택 순서)로 보내고, napari는 레이어 자신의 순서로 보내며, Fiji는
    결과를 자기 순서로 돌려받기를 기대해요. 스크립트 안에서는 마음대로 고를 수
    있어요. 우리는 **T C Z Y X**를 권해요. 계층별 선택지는 다음과 같아요.

    | 계층 | 권장 | 대안 | 대안을 고를 때 |
    |---|---|---|---|
    | **저장**(디스크의 파일) | **T C Z Y X**(또는 C Z Y X, Z Y X)의 OME-Zarr | **T Z C Y X**의 ImageJ TIFF | 주로 Fiji에서 여는 작은 데이터(ImageJ TIFF는 자기 순서로만 저장할 수 있어요) |
    | **전달**(Wavu ↔ 스크립트) | `run()` 시작에서 C-연속 **T C Z Y X**로 바꾸고, 돌려주기 전에 되돌리기 | Wavu가 주는 그대로 두기(Fiji에서는 **T Z C Y X**) | 순서가 상관없는 평면별 처리(필터, 문턱값) |
    | **계산**(NumPy, PyTorch, GPU) | **T C Z Y X**: 시점 하나는 `(C, Z, Y, X)`, 배치 축을 더하면 PyTorch의 `(N, C, D, H, W)` | GPU 메모리 안에서만 **channels last**(B Z Y X C): `tensor.to(memory_format=torch.channels_last_3d)`. TensorFlow/Keras의 기본값 | 최신 NVIDIA GPU에서 혼합 정밀도 3-D 합성곱, Keras 모델 |

    왜 T C Z Y X일까요? 축 순서를 좌우하는 것은 네 가지인데, 이 순서는 그
    모두에 맞아요.

    1. **현미경.** 카메라는 한 번에 **Y × X** 프레임 하나를 읽고(가장 빠름),
       피에조 스테이지가 **Z**로 움직이고, 필터나 레이저가 **C**를 바꾸며,
       시간 간격 **T**가 가장 느려요. Y, X를 가장 안쪽에, 그 옆에 Z를 두면
       데이터를 얻는 방식을 따르고 3-D 부피가 한데 모여 있어요. (Z/C 반복
       순서는 장비마다 달라요.)
    2. **저장과 청크.** NumPy와 Zarr 배열은 *C-연속*이라서 마지막 축이 가장
       빨리 바뀌어요. T C Z Y X에서는 `(1, 1, 64, 512, 512)` 같은 청크가
       **채널 하나**의 촘촘한 3-D 블록이라서, 채널 0(예: DAPI)만 읽으면 그
       파일들만 읽어요. 채널이 섞여 있으면 읽을 때마다 모든 채널을 가져와요.
       그래서 [OME-NGFF 사양](https://ngff.openmicroscopy.org/0.4/#axes-md)은
       시간, 그다음 채널, 그다음 공간 순서를 요구해요(버전 0.4와 0.5. 이를
       완화하자는 제안인 [RFC-3](https://ngff.openmicroscopy.org/rfc/3/index.html)은
       아직 검토 중이에요). Fiji, napari, Bio-Formats 모두 이를 읽어요.
       디스크의 데이터는 수십 년 동안 남지만 GPU는 몇 년마다 바뀌어요.
    3. **딥러닝.** `(C, Z, Y, X)`에 배치 축을 더하면
       [PyTorch의 `Conv3d`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv3d.html)가
       기대하는 `(N, C, D, H, W)`와 똑같아요. C-연속 배열에 `torch.from_numpy()`를
       쓰면 메모리를 공유해서 아무것도 복사되지 않아요.
    4. **GPU.** NVIDIA Tensor 코어는 채널이 가장 안쪽에 있을 때("channels
       last") 혼합 정밀도(FP16/BF16) 3-D 합성곱을 더 빨리 돌릴 수 있어요.
       변환은 **GPU 메모리 안에서만**, 무거운 층 바로 앞에서 하세요. 모양은
       `(N, C, D, H, W)` 그대로이고 스트라이드만 바뀌어요. 결과가 GPU를 떠나기
       전에 다시 연속으로 만드세요(`.contiguous()`). 칩의 취향은 파일까지
       가지 않아요.

    스크립트 안에서 바꿨다가 되돌리는 예:

    ```python
    import numpy as np
    import wavu

    def to_tczyx(img, axes):
        """Reorder to T, C, Z, Y, X (only the axes present). Returns (array, new axes)."""
        new = "".join(a for a in "TCZYX" if a in axes)
        return np.ascontiguousarray(np.transpose(img, [axes.index(a) for a in new])), new

    def back(arr, axes_now, axes_wanted):
        """Reorder a result back, e.g. to the input's own order before returning it."""
        return np.ascontiguousarray(np.transpose(arr, [axes_now.index(a) for a in axes_wanted]))

    def run(ctx, inputs, params):
        axes = ctx.meta["image"].get("axes") or "YX"    # Fiji에서는 예: "TZCYX" 또는 "ZCYX"
        x, ours = to_tczyx(inputs["image"], axes)       # 예: (C, Z, Y, X), "CZYX"
        # PyTorch: 배치 축을 붙인 시점 하나, 복사 없음
        #   batch = torch.from_numpy(x)[None]           # "CZYX"면 (1, C, Z, Y, X)
        y = x * 2                                       # 여러분의 계산, 출력도 같은 배치
        return {"result": wavu.Image(back(y, ours, axes), axes=axes)}
    ```

    (축이 `S`로 끝나는 RGB 이미지는 여기서 다루지 않아요. 먼저 회색으로
    바꾸거나 색을 나누세요. napari 레이어가 `axes` 없이 오면 그 순서는
    여러분이 가장 잘 알아요. 글자를 직접 넘기세요.)

## 얼마나 크면 너무 큰가요?

Wavu는 **메모리에 넉넉히 들어가는 이미지 한 장으로 하는 대화형 작업**,
대략 **1–2 GB**까지를 위해 만들어졌어요. 작은 이미지는 메시지 하나로 가고,
큰 이미지는 디스크의 임시 TIFF 파일을 거쳐 가요. 여러분이 할 일은 없어요.
어느 쪽이든 `inputs["image"]`는 NumPy 배열이에요.
한계는 Fiji와 napari에서 같아요.

!!! warning "napari: 큰 지연 로딩 레이어는 통째로 불러와요"
    napari는 아주 큰 이미지를 지연 로딩(*dask* 배열)으로 보여 주면서 화면에
    보이는 부분만 읽을 수 있어요. Wavu는 그럴 수 없어요. 보내기 전에 레이어
    전체를 메모리에 불러오니, 메모리에 들어가는 레이어(잘라 낸 부분, 채널
    하나, 해상도를 낮춘 사본)를 고르세요.

그보다 크다면 OME-Zarr로 변환하고 스크립트가 조각조각 읽게 하세요.
[스트림 분석](../workflows/large-data.md)은 로컬 컴퓨터에서 약 50 GB까지
처리해요. 작동은 하지만, Fiji나 napari에서 조종하는 것은 권장하지 않아요.
파일이 수백 개라면 [배치 처리](../workflows/batch.md)를 보세요. 약 50 GB를
넘으면 배치나 HPC 워크플로를 쓰세요.

## 느린 첫 실행(과 사용자를 안심시키는 법) { #slow-first-runs-and-how-to-keep-users-calm }

*첫* 실행을 느리게 하는 것은 두 가지이고, 둘 다 한 번만 일어나요.

1. **환경을 만들어요.** pixi가 `pixi.toml`에 적힌 패키지를 내려받아요.
   PyTorch(Cellpose에 필요)가 있으면 **1–2 GB**에 몇 분이 걸릴 수 있어요.
   그동안 Fiji의 Log나 napari 패널의 로그가 알려 줘요.
2. **모델 가중치를 내려받아요.** Cellpose 같은 도구는 처음 쓸 때 학습된
   모델을 인터넷에서 가져와요. 이건 *스크립트 안에서* 일어나서 뷰어는 아무것도
   모르고, 멈춘 것처럼 보일 수 있어요.

사용자가 무슨 일인지 알 수 있게, **느린 단계 전에는 항상 로그를 남기세요.**

```python
ctx.log("Loading the Cellpose model (the first time, it is downloaded)...")
ctx.progress(0.1)
model = models.Cellpose(gpu=params["use_gpu"], model_type="nuclei")
ctx.log("Model ready")
```

!!! tip "잘 작동하는 Cellpose 설정"
    Wavu 저장소에 완전한 Cellpose 핵 스크립트가 있어요. PyTorch, Cellpose,
    선택 사항인 NVIDIA GPU 설정이 든 `pixi.toml`도 포함돼요:
    [`examples/cellpose_nuclei`](https://github.com/Oxford-Zeiss-Centre-of-Excellence/Wavu/tree/main/examples/cellpose_nuclei).
    그 `[dependencies]`와 `[pypi-dependencies]` 줄을 내 `pixi.toml`에
    복사하세요. Apple silicon Mac은 따로 설정하지 않아도 GPU를 써요.

## 한 문장으로

스크립트는 이미지 전체를 배열 하나로 받고(Fiji에서는 **T Z C Y X** 순서,
napari에서는 레이어 자신의 순서. 확실히 하려면 `ctx.meta`와 모양을
읽으세요. OME-NGFF와 PyTorch의 순서인 **T C Z Y X**로 다시 정렬하기를
권해요), 크기는 어느 뷰어에서든 대략 1–2 GB 아래여야 하며, 첫 모델 다운로드처럼
느린 일 전에는 `ctx.log`를 남기세요.

[다음: 컨테이너로 공유하기 :material-arrow-right:](container.md){ .md-button }
