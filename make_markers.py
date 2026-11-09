from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# файлы сохраняются рядом со скриптом, из какой бы папки его ни запустили
BASE = Path(__file__).resolve().parent
MARKERS = BASE / "markers"

# подписи на листе для печати
LABELS = {
    "lathe": ("Токарно-винторезный станок 16К20", "инв. № ИС-0451"),
    "mill": ("Фрезерный станок с ЧПУ 6Р13Ф3", "инв. № ИС-0452"),
    "printer": ("3D-принтер ПТ-300", "инв. № ИС-0517"),
}

# узоры маркеров 4 на 4 клетки (1 = чёрная клетка)
GRIDS = {
    "lathe":   [[0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1], [0, 0, 1, 1]],
    "mill":    [[1, 0, 0, 0], [1, 0, 1, 1], [0, 0, 0, 1], [1, 0, 1, 1]],
    "printer": [[1, 0, 1, 0], [0, 1, 0, 1], [0, 1, 1, 1], [1, 0, 0, 0]],
}


def inner_image(grid, u):
    # внутренняя область 16u: белый отступ 2u и клетки по 3u
    img = Image.new("L", (16 * u, 16 * u), 255)
    draw = ImageDraw.Draw(img)
    for r in range(4):
        for c in range(4):
            if grid[r][c] == 1:
                x = (2 + 3 * c) * u
                y = (2 + 3 * r) * u
                draw.rectangle([x, y, x + 3 * u - 1, y + 3 * u - 1], fill=0)
    return img


def marker_image(grid, u):
    # чёрная рамка 8u, внутренняя область занимает половину маркера
    img = Image.new("L", (32 * u, 32 * u), 0)
    img.paste(inner_image(grid, u), (8 * u, 8 * u))
    return img


def template(grid):
    # внутренняя область, уменьшенная до 16 на 16 точек
    return np.array(inner_image(grid, 10).resize((16, 16), Image.BOX))


def patt_text(grid):
    # 4 поворота против часовой стрелки, для каждого каналы B, G, R
    small = template(grid)
    text = ""
    for k in range(4):
        if k > 0:
            text += "\n"
        turned = np.rot90(small, k)
        for channel in range(3):
            for row in turned:
                text += " ".join(str(v).rjust(3) for v in row) + "\n"
    return text


def correlation(a, b):
    # нормированная корреляция двух шаблонов, как в ARToolKit
    a = a - a.mean()
    b = b - b.mean()
    return (a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum())


def find_font(size):
    # шрифт с кириллицей: Windows, macOS или Linux
    for path in ["C:/Windows/Fonts/arial.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return None


def print_sheet(path, side_mm=60, dpi=300):
    # лист A4: маркеры со стороной side_mm и белым полем вокруг рамки
    mm = dpi / 25.4
    page = Image.new("L", (round(210 * mm), round(297 * mm)), 255)
    draw = ImageDraw.Draw(page)
    side = round(side_mm * mm)
    font, small = find_font(round(3.5 * mm)), find_font(round(3 * mm))
    if font:
        draw.text((page.width // 2, round(12 * mm)),
                  "Маркеры AR-паспорта оборудования (сторона маркера "
                  + str(side_mm) + " мм)", fill=0, font=small, anchor="mm")
    places = [(55, 25), (155, 25), (105, 150)]  # центры ячеек, мм
    for (name, grid), (cx, top) in zip(GRIDS.items(), places):
        x, y = round(cx * mm) - side // 2, round(top * mm)
        # пунктир для вырезания, белое поле 15 мм
        pad = round(15 * mm)
        box = [x - pad, y - pad // 2, x + side + pad, y + side + round(32 * mm)]
        for i in range(box[0], box[2], 20):
            draw.line([i, box[1], i + 10, box[1]], fill=160)
            draw.line([i, box[3], i + 10, box[3]], fill=160)
        for j in range(box[1], box[3], 20):
            draw.line([box[0], j, box[0], j + 10], fill=160)
            draw.line([box[2], j, box[2], j + 10], fill=160)
        page.paste(marker_image(grid, 40).resize((side, side), Image.NEAREST), (x, y))
        if font:
            title, inv = LABELS[name]
            draw.text((x + side // 2, y + side + round(10 * mm)), title,
                      fill=0, font=font, anchor="mm")
            draw.text((x + side // 2, y + side + round(18 * mm)), inv,
                      fill=80, font=small, anchor="mm")
    page.save(path, resolution=dpi)


MARKERS.mkdir(exist_ok=True)
for name, grid in GRIDS.items():
    with open(MARKERS / (name + ".patt"), "w") as f:
        f.write(patt_text(grid))
    marker_image(grid, 40).save(MARKERS / (name + ".png"))
print_sheet(BASE / "markers_print.pdf")
print("Маркеры сохранены в", MARKERS)

# проверка: похожесть маркеров друг на друга и на свои повороты
names = list(GRIDS)
for i in range(len(names)):
    for j in range(i, len(names)):
        a = template(GRIDS[names[i]]).astype(float)
        b = template(GRIDS[names[j]]).astype(float)
        turns = [1, 2, 3] if i == j else [0, 1, 2, 3]
        best = max(correlation(a, np.rot90(b, k)) for k in turns)
        print(names[i], names[j], round(best, 2))
