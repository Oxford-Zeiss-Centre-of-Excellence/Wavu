# 실제 이미지

## 쉬운 말로 설명하면

*Blobs*는 평평한 그림 한 장이에요. 현미경 이미지는 흔히 **그림 더미**예요.
여러 색 채널, 여러 초점면(z-stack), 어쩌면 여러 시점까지 있어요. Wavu는 그
**더미 전체**를 NumPy 배열 하나로 스크립트에 넘겨주고, 어떻게 쌓였는지도
알려 줘요. 슬라이드 상자를 받으면서 어느 방향으로 정리됐는지 적힌 라벨도
함께 받는 것과 같아요.

![이미지 평면 더미: 시간, z, 채널, 그다음 y와 x](../assets/img/axes.svg){ width="640" }

## 배열의 모양

축은 언제나 이 순서로 오고, 길이가 1인 축은 빠져요.

**T**(시간) · **Z**(평면) · **C**(채널) · **Y** · **X**, 그리고 RGB 컬러
이미지라면 마지막에 길이 3인 축 **S**가 붙어요.

| Fiji의 이미지 | `inputs["image"].shape` | `ctx.meta["image"]["axes"]` |
|---|---|---|
| 2차원 회색 이미지 한 장, 512 × 512 | `(512, 512)` | `"YX"` |
| 채널 3개 | `(3, 512, 512)` | `"CYX"` |
| 평면 20개짜리 z-stack, 채널 2개 | `(20, 2, 512, 512)` | `"ZCYX"` |
| RGB 사진 | `(512, 512, 3)` | `"YXS"` |

그러니 `ZCYX` 이미지에서 "모든 평면의 채널 2"는 `img[:, 1]`이에요. Fiji는
8-bit, 16-bit, 32-bit, RGB 픽셀을 바꾸지 않고 그대로 보내요.

## 그 밖에 받는 것: `ctx.meta`

`ctx.meta["image"]`에는 `"image"` 입력란에서 고른 이미지에 대해 Fiji가 아는
정보가 들어 있어요.

- `"axes"`: 위와 같은 축 글자;
- `"pixel_um"`: 이미지가 보정되어 있다면 마이크로미터 단위의 픽셀 크기;
- `"title"`: 창 제목.

```python
def run(ctx, inputs, params):
    img = inputs["image"]
    axes = ctx.meta["image"]["axes"]
    ctx.log(f"Got {img.shape} with axes {axes}")
    if img.ndim != 2:
        raise ValueError("Please pick a single 2-D channel (Image › Duplicate…)")
    ...
```

모양을 확인하고 분명한 `ValueError`를 내는 편이 나중에 코드가 엉뚱하게
죽는 것보다 친절해요. Fiji가 그 문장을 오류 창에 보여 주거든요.

## 얼마나 크면 너무 큰가요?

Wavu는 **메모리에 넉넉히 들어가는 이미지 한 장으로 하는 대화형 작업**,
대략 **1–2 GB**까지를 위해 만들어졌어요. 작은 이미지는 메시지 하나로 가고,
큰 이미지는 디스크의 임시 TIFF 파일을 거쳐 가요. 여러분이 할 일은 없어요.
어느 쪽이든 `inputs["image"]`는 NumPy 배열이에요.

그보다 크거나 파일이 수백 개라면 Wavu는 맞는 도구가 아니에요. OME-Zarr로
변환하고 배치(batch)나 HPC 워크플로를 쓰세요.

## 느린 첫 실행(과 사용자를 안심시키는 법) { #slow-first-runs-and-how-to-keep-users-calm }

*첫* 실행을 느리게 하는 것은 두 가지이고, 둘 다 한 번만 일어나요.

1. **환경을 만들어요.** pixi가 `pixi.toml`에 적힌 패키지를 내려받아요.
   PyTorch(Cellpose에 필요)가 있으면 **1–2 GB**에 몇 분이 걸릴 수 있어요.
   그동안 Fiji의 Log가 알려 줘요.
2. **모델 가중치를 내려받아요.** Cellpose 같은 도구는 처음 쓸 때 학습된
   모델을 인터넷에서 가져와요. 이건 *스크립트 안에서* 일어나서 Fiji는 아무것도
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

스크립트는 이미지 전체를 **T Z C Y X** 순서의 배열 하나로 받고(확실히 하려면
`ctx.meta`를 읽으세요), 크기는 대략 1–2 GB 아래여야 하며, 첫 모델 다운로드처럼
느린 일 전에는 `ctx.log`를 남기세요.

[다음: 연구실과 공유하기 :material-arrow-right:](../share/with-your-lab.md){ .md-button }
