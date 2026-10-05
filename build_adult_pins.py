"""Pin images (1000x1500 JPG) + Pinterest bulk CSV for the 60 adult colouring pages.

Reads the page list from halloween-coloring-pages-for-adults.html (so names and PDF paths match the live page),
renders each page's PDF onto a dark branded card, writes pins/adults/NN-slug.jpg and
D:/gentle-shorts-media/PINTEREST-BULK-adults-60.csv.

    python build_adult_pins.py
"""
import csv
import datetime as dt
import re
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
PINS = HERE / "pins" / "adults"
SITE = "https://ainjection.github.io/halloween-books/"
PAGE = SITE + "halloween-coloring-pages-for-adults.html"
BOARD = "Halloween Coloring Pages for Adults and Kid"   # exact name on the digitalexpress77 account, 5 Oct 2026 (Blotato board 1084663960196176150)
W, H = 1000, 1500
F = HERE / "_rec" / "fonts"
GRIFFY = str(F / "Griffy-Regular.ttf"); NUNITO = str(F / "Nunito.ttf")


def nunito(size, wght=700):
    f = ImageFont.truetype(NUNITO, size); f.set_variation_by_axes([wght]); return f


def pages():
    html = (HERE / "halloween-coloring-pages-for-adults.html").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r'<article class="pg"><a href="(print/adults/[^"]+\.pdf)" download>.*?<h3>(.*?)</h3>', html, re.S):
        pdf, title = m.group(1), m.group(2).replace("&amp;", "&")
        out.append((pdf, title, "grayscale" if "grayscale-" in pdf else "bold-easy"))
    assert len(out) == 60, len(out)
    return out


def render(pdf):
    d = pdfium.PdfDocument(str(HERE / pdf)); p = d[0]
    return p.render(scale=900 / p.get_width()).to_pil().convert("RGB")


def wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]


def pin(pdf, title, kind, out):
    from PIL import ImageFilter
    im = Image.new("RGB", (W, H), "#22133a")
    glow = Image.new("RGB", (W, H), "#22133a"); ImageDraw.Draw(glow).ellipse((-200, -300, W + 200, 700), fill="#3b1f55")
    im = Image.blend(im, glow, 0.9); d = ImageDraw.Draw(im)
    kicker = "FREE PRINTABLE  ·  GRAYSCALE COLORING PAGE FOR ADULTS" if kind == "grayscale" else "FREE PRINTABLE  ·  BOLD AND EASY HALLOWEEN COLORING PAGE"
    fk = nunito(26, 800); fb = nunito(28, 700); fs = nunito(24, 400)
    page = render(pdf)
    maxw, maxh = (820, 940) if kind == "grayscale" else (880, 880)
    sc = min(maxw / page.width, maxh / page.height); page = page.resize((int(page.width * sc), int(page.height * sc)), Image.LANCZOS)
    ft = ImageFont.truetype(GRIFFY, 64); lines = wrap(d, title, ft, 900)
    if len(lines) > 2: ft = ImageFont.truetype(GRIFFY, 52); lines = wrap(d, title, ft, 900)
    lines = lines[:3]
    title_h = len(lines) * (ft.size + 10)
    total = 26 + 40 + page.height + 36 + title_h + 40 + 28 + 22 + 24      # kicker, gap, page, gap, title, gap, foot, gap, site
    y = max(50, (H - total) // 2)
    d.text(((W - d.textlength(kicker, font=fk)) / 2, y), kicker, font=fk, fill="#ffb347"); y += 26 + 40
    x = (W - page.width) // 2
    shadow = Image.new("RGBA", (page.width + 60, page.height + 60), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((30, 40, page.width + 30, page.height + 50), 18, fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18)); im.paste(shadow, (x - 30, y - 30), shadow)
    card = Image.new("RGB", (page.width + 24, page.height + 24), "white"); card.paste(page, (12, 12))
    mask = Image.new("L", card.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, card.width, card.height), 14, fill=255)
    im.paste(card, (x - 12, y - 12), mask); y += page.height + 36
    for ln in lines:
        d.text(((W - d.textlength(ln, font=ft)) / 2, y), ln, font=ft, fill="#f3ecff"); y += ft.size + 10
    y += 40
    foot = "Print it free: Letter or A4, no sign-up" if kind == "grayscale" else "Print it free, fits Letter or A4"
    d.text(((W - d.textlength(foot, font=fb)) / 2, y), foot, font=fb, fill="#ffb347"); y += 28 + 22
    site = "ainjection.github.io/halloween-books  ·  The Gentle Bookshop"
    d.text(((W - d.textlength(site, font=fs)) / 2, y), site, font=fs, fill="#b9a9d6")
    im.save(out, "JPEG", quality=88, optimize=True)


def main():
    PINS.mkdir(parents=True, exist_ok=True)
    for old in PINS.glob("*.jpg"): old.unlink()
    rows = []
    start = dt.datetime(2026, 10, 6, 8, 0)                   # UTC; 6 a day at 08/10/12/14/16/18 so the lot lands before Halloween
    slots = [8, 10, 12, 14, 16, 18]
    for i, (pdf, title, kind) in enumerate(pages()):
        base = Path(pdf).stem.replace("-a4", "")
        img = PINS / f"{i + 1:02d}-{base}.jpg"
        pin(pdf, title, kind, img)
        day, slot = divmod(i, len(slots))
        when = (start + dt.timedelta(days=day)).replace(hour=slots[slot])
        if kind == "grayscale":
            pt = f"Free Grayscale Halloween Coloring Page for Adults: {title}"
            desc = (f"{title}: free printable grayscale Halloween coloring page for adults. The shading is printed in soft grey; "
                    f"lay colour over it with soft pencils and it looks three-dimensional. One PDF, Letter or A4, no sign-up. "
                    f"From the Halloween Grayscale Coloring Book by The Gentle Bookshop. "
                    f"Grayscale coloring pages for adults, Halloween coloring pages for adults, adult coloring pages printable. "
                    f"#grayscalecoloring #halloweencoloringpages #adultcoloring #freeprintable")
            kw = "grayscale coloring pages for adults, halloween coloring pages for adults, adult coloring pages printable, free printable coloring pages, grayscale coloring book, halloween printables, coloring pages for adults, spooky coloring pages"
            anchor = "#grayscale"
        else:
            pt = f"Free Bold and Easy Halloween Coloring Page: {title}"
            desc = (f"{title}: free printable Halloween coloring page with thick easy lines and a 'Did you know?' fact. "
                    f"Good for markers, seniors, tired evenings or colouring with the kids. One PDF, fits Letter or A4, no sign-up. "
                    f"From the Halloween Bold and Easy Coloring Book by The Gentle Bookshop. "
                    f"Bold and easy coloring pages, Halloween coloring pages for adults, easy coloring pages for seniors. "
                    f"#boldandeasy #halloweencoloringpages #freeprintable #easycoloringpages")
            kw = "bold and easy coloring pages, halloween coloring pages for adults, easy coloring pages for seniors, free printable halloween coloring pages, halloween coloring pages printable, coloring pages for adults, large print coloring pages, cute halloween coloring pages"
            anchor = "#bold-easy"
        pt = pt[:100]
        while len(desc) > 500: desc = desc.rsplit(" #", 1)[0]   # drop trailing hashtags until it fits
        assert len(desc) <= 500, (len(desc), title)
        rows.append({"Title": pt, "Media URL": SITE + f"pins/adults/{img.name}", "Pinterest board": BOARD, "Thumbnail": "",
                     "Description": desc, "Link": PAGE + "?src=pinterest" + anchor, "Publish date": when.strftime("%Y-%m-%dT%H:%M:%S"), "Keywords": kw})
    out = Path("D:/gentle-shorts-media/PINTEREST-BULK-adults-60.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), quoting=csv.QUOTE_MINIMAL); w.writeheader(); w.writerows(rows)
    with open(out.with_name("PINTEREST-BULK-adults-TEST-3.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), quoting=csv.QUOTE_MINIMAL); w.writeheader(); w.writerows(rows[:3])
    print(len(rows), "pins ->", PINS, "| csv", out, "| last publish", rows[-1]["Publish date"])


if __name__ == "__main__":
    main()
    assert len(list(PINS.glob("*.jpg"))) == 60
    print("self-check ok")
