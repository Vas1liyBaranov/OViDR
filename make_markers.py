"""Генерирует маркеры-картинки для MindAR и лист для печати.

MindAR распознаёт не узор в рамке, а саму картинку по её характерным
точкам (углы, края, перепады яркости). Поэтому маркер должен быть
контрастным, детализированным и не повторяться: здесь каждый маркер
состоит из таблички с названием оборудования и поля из случайных фигур
со своим зерном генератора.

Запуск: python3 make_markers.py
Результат: markers/lathe.png, markers/mill.png, markers/printer.png
и markers_print.pdf. После этого нужно заново собрать targets.mind
на странице compile.html.
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
MARKERS = BASE / "markers"
SIZE = 1000  # сторона маркера в пикселях

# порядок важен: номер в списке = targetIndex в targets.mind
TARGETS = [
    ("lathe", "Токарно-винторезный", "станок 16К20", "ИС-0451", 11),
    ("mill", "Фрезерный станок", "с ЧПУ 6Р13Ф3", "ИС-0452", 22),
    ("printer", "3D-принтер", "ПТ-300", "ИС-0517", 33),
]


def find_font(size, bold=False):
    # шрифт с кириллицей: Windows, macOS или Linux
    names = (["C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
             if bold else
             ["C:/Windows/Fonts/arial.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for path in names:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def random_shapes(draw, rnd, box, count):
    # поле из фигур разного размера, яркости и наклона: много углов и краёв
    x0, y0, x1, y1 = box
    for _ in range(count):
        kind = rnd.random()
        cx, cy = rnd.randint(x0, x1), rnd.randint(y0, y1)
        r = rnd.randint(12, 70)
        tone = rnd.choice([0, 0, 0, 60, 120, 180])
        if kind < 0.4:
            pts = [(cx + rnd.randint(-r, r), cy + rnd.randint(-r, r))
                   for _ in range(rnd.randint(3, 6))]
            draw.polygon(pts, fill=tone)
        elif kind < 0.7:
            draw.ellipse([cx - r, cy - r // 2, cx + r, cy + r // 2],
                         outline=tone, width=rnd.randint(4, 10))
        else:
            draw.line([cx - r, cy + rnd.randint(-r, r),
                       cx + r, cy + rnd.randint(-r, r)],
                      fill=tone, width=rnd.randint(4, 12))


def marker_image(title1, title2, inv, seed):
    rnd = random.Random(seed)
    img = Image.new("L", (SIZE, SIZE), 255)
    draw = ImageDraw.Draw(img)

    # толстая рамка и табличка с названием
    draw.rectangle([0, 0, SIZE - 1, SIZE - 1], outline=0, width=40)
    draw.rectangle([40, 40, SIZE - 41, 300], fill=0)
    draw.text((SIZE // 2, 125), title1, fill=255,
              font=find_font(70, bold=True), anchor="mm")
    draw.text((SIZE // 2, 220), title2, fill=255,
              font=find_font(70, bold=True), anchor="mm")

    # поле случайных фигур — у каждого маркера своё
    random_shapes(draw, rnd, (70, 340, SIZE - 70, SIZE - 180), 140)

    # нижняя полоса с инвентарным номером и «штрихкодом»
    draw.rectangle([40, SIZE - 160, SIZE - 41, SIZE - 41], fill=255,
                   outline=0, width=6)
    draw.text((80, SIZE - 100), "инв. № " + inv, fill=0,
              font=find_font(54, bold=True), anchor="lm")
    x = 560
    while x < SIZE - 80:
        w = rnd.choice([4, 8, 12, 16])
        draw.rectangle([x, SIZE - 140, x + w, SIZE - 60], fill=0)
        x += w + rnd.choice([6, 10, 14])
    return img


def print_sheet(images, path, side_mm=120, dpi=200):
    # по одному маркеру на страницу A4, сторона side_mm
    mm = dpi / 25.4
    pages = []
    for (name, t1, t2, inv, _), img in zip(TARGETS, images):
        page = Image.new("L", (round(210 * mm), round(297 * mm)), 255)
        side = round(side_mm * mm)
        x = (page.width - side) // 2
        y = round(40 * mm)
        page.paste(img.resize((side, side), Image.LANCZOS), (x, y))
        draw = ImageDraw.Draw(page)
        draw.text((page.width // 2, y + side + round(15 * mm)),
                  "Маркер «" + t1 + " " + t2 + "» (" + str(side_mm // 10)
                  + " см). Печатать в масштабе 100%",
                  fill=0, font=find_font(round(4 * mm)), anchor="mm")
        pages.append(page.convert("RGB"))
    pages[0].save(path, save_all=True, append_images=pages[1:],
                  resolution=dpi)


MARKERS.mkdir(exist_ok=True)
images = []
for name, t1, t2, inv, seed in TARGETS:
    img = marker_image(t1, t2, inv, seed)
    img.save(MARKERS / (name + ".png"))
    images.append(img)
print_sheet(images, BASE / "markers_print.pdf")
print("Готово:", ", ".join("markers/" + t[0] + ".png" for t in TARGETS),
      "и markers_print.pdf")
print("Теперь соберите targets.mind на странице compile.html")
