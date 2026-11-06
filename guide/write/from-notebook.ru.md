# От ноутбука к Wavu

## Идея простыми словами

Ячейка ноутбука и скрипт Wavu делают одну и ту же работу; меняются только
**двери входа и выхода**. В ноутбуке *вы* вводите настройки, загружаете файл
и смотрите на график. В Wavu просмотрщик (**Fiji** или **napari**) берёт
настройки из диалога или формы, передаёт уже открытое изображение и
показывает всё, что вы вернёте. Сам анализ посередине остаётся прежним, как
и скрипт, — неважно, какой просмотрщик его запускает.

```mermaid
flowchart LR
    subgraph NB["Ноутбук"]
        A1["sigma = 2.0"]:::script
        A2["img = io.imread(...)"]:::script
        A3["ваш анализ"]:::worker
        A4["plt.imshow(labels)"]:::script
    end
    subgraph WV["Скрипт Wavu"]
        B1["PARAMS → диалог / форма"]:::fiji
        B2["inputs['image']"]:::fiji
        B3["ваш анализ"]:::worker
        B4["return {'labels': labels}"]:::fiji
    end
    A1 -.-> B1
    A2 -.-> B2
    A3 -.-> B3
    A4 -.-> B4

    classDef fiji   fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef worker fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20
    classDef script fill:#fff3e0,stroke:#ef6c00,color:#e65100
```

## Таблица перевода

| В ноутбуке | В `script.py` | Что вы видите в Fiji или napari |
|---|---|---|
| `sigma = 2.0` | `"sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"}` в `PARAMS`, затем `params["sigma"]` | числовое поле **Sigma (pixels)** в диалоге Fiji или в форме панели napari |
| `img = io.imread("cells.tif")` | `"image": {"type": "image"}` в `PARAMS`, затем `inputs["image"]` | выпадающий список: открытые изображения (Fiji) или слои Image и Labels (napari); на вход идёт то, что вы выберете |
| `print("found", n)` | `ctx.log(f"found {n}")` (`print` тоже работает) | строка в окне **Log** Fiji или в журнале панели napari |
| `plt.imshow(labels)` | `return {"labels": labels}` | новое окно изображения *…-labels* (Fiji) или слой Labels (napari) |
| `df` (таблица) | `return {"cells": df}` | таблица Results (Fiji) или панель с таблицей (napari) |

## Разберём пример

Вот типичная ячейка ноутбука, которая пороговой обработкой выделяет ядра и
считает их:

```python
from skimage import io, filters, measure

sigma = 2.0
img = io.imread("nuclei.tif")
smooth = filters.gaussian(img, sigma)
mask = smooth > filters.threshold_otsu(smooth)
labels = measure.label(mask)
print("found", labels.max(), "nuclei")
plt.imshow(labels)
```

А вот то же самое как скрипт Wavu. Замените содержимое `script.py` на:

```python
"""Count nuclei -- Otsu threshold after a Gaussian blur."""

PARAMS = {
    "image": {"type": "image", "label": "Nuclei image"},
    "sigma": {"type": "float", "default": 2.0, "label": "Sigma (pixels)"},
}


def run(ctx, inputs, params):
    from skimage import filters, measure

    img = inputs["image"]                     # изображение, выбранное в диалоге/форме
    smooth = filters.gaussian(img, params["sigma"])
    mask = smooth > filters.threshold_otsu(smooth)
    labels = measure.label(mask)
    ctx.log(f"found {labels.max()} nuclei")   # появляется в журнале
    return {"labels": labels}                 # новое окно изображения / слой Labels
```

Здесь используется scikit-image, поэтому сначала добавьте
`scikit-image = "*"` в `pixi.toml` ([как](get-the-template.md#adding-a-package)).
Сохраните оба файла, остановите worker
([как](get-the-template.md#the-everyday-loop)) и запустите скрипт на 2-D
изображении: *Blobs* в Fiji или *Coins* в napari
(**File › Open Sample › napari builtins › Coins**).

## Три правила

1. **`PARAMS` в начале** — это диалог (Fiji) или форма (napari). Каждая
   запись становится одним полем.
2. **`def run(ctx, inputs, params):`** — здесь делается работа. Изображения
   приходят в `inputs`, остальные настройки — в `params`, а `ctx` — ваша
   связь с просмотрщиком (журнал, индикатор прогресса, отмена).
3. **Верните словарь.** Каждый ключ становится именем результата (Fiji
   добавляет спереди имя изображения, как в *blobs-labels*; napari называет
   слой по ключу), каждое значение показывается подходящим способом.

!!! tip "Две привычки, которые экономят время"
    - **Импортируйте тяжёлые пакеты внутри `run`**, как выше. Тогда диалог
      или форма появятся сразу, не дожидаясь больших импортов.
    - **Выбрасывайте понятную ошибку** при ошибках пользователя, например
      `raise ValueError("Please pick a single-channel image")`. Fiji покажет
      сообщение в окне ошибки; napari напишет `Error: …` в журнале панели и
      покажет уведомление.

Первая строка docstring (текст в тройных кавычках в самом начале файла)
показывается вверху диалога Fiji и панели napari, так что сделайте её
кратким описанием.

## Одним предложением

Оставьте анализ как есть; просто берите настройки из `params`, изображение
из `inputs`, пишите сообщения через `ctx.log` и возвращайте через `return`
то, что хотите увидеть.

[Далее: PARAMS = ваш диалог :material-arrow-right:](params.md){ .md-button }
