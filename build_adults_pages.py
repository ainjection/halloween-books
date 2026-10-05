"""Build halloween-coloring-pages-for-adults.html: one PDF per page, thumbnails, static HTML + JSON-LD.

Sources (all already published as free PDFs on this site):
  pages/halloween-grayscale-vol1-sample-pages.pdf  p2-p6  (p1 is the title page)
  pages/halloween-grayscale-vol2-sample-pages.pdf  p2-p6
  free/halloween-bold-easy-coloring-book.pdf       p2-p51 (p1 title, p52 promo, p53 QR); order = D:/kdp-halloween-bold-easy/pages.json
The Complete Collection and Pocket Sudoku samples repeat these pages, so they are not included.

    python build_adults_pages.py
"""
import json
import re
from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject

HERE = Path(__file__).parent
OUT = HERE / "print" / "adults"
THUMBS = OUT / "thumbs"
SITE = "https://ainjection.github.io/halloween-books/"
PAGE_URL = SITE + "halloween-coloring-pages-for-adults.html"
A4 = (595.276, 841.89)

GRAYSCALE = [  # (source pdf, 0-based page, title) titles written from the rendered pages, 5 Oct 2026
    ("pages/halloween-grayscale-vol1-sample-pages.pdf", 1, "Barn owl on a wooden gate"),
    ("pages/halloween-grayscale-vol1-sample-pages.pdf", 2, "Witch stirring a cauldron under a gothic arch"),
    ("pages/halloween-grayscale-vol1-sample-pages.pdf", 3, "Haunted Victorian house behind iron gates"),
    ("pages/halloween-grayscale-vol1-sample-pages.pdf", 4, "Black cat in a lace-curtained window with a jack-o'-lantern"),
    ("pages/halloween-grayscale-vol1-sample-pages.pdf", 5, "Three carved pumpkins with autumn leaves"),
    ("pages/halloween-grayscale-vol2-sample-pages.pdf", 1, "Skeleton gentleman riding a penny-farthing"),
    ("pages/halloween-grayscale-vol2-sample-pages.pdf", 2, "Witch in a pumpkin patch with her spell book"),
    ("pages/halloween-grayscale-vol2-sample-pages.pdf", 3, "Grim Reaper in a wheat field with crows"),
    ("pages/halloween-grayscale-vol2-sample-pages.pdf", 4, "Skeleton couple waltzing in a ballroom"),
    ("pages/halloween-grayscale-vol2-sample-pages.pdf", 5, "Witch and her cat flying over moonlit rooftops"),
]
BE_PDF = "free/halloween-bold-easy-coloring-book.pdf"
BE_SUBJECTS = json.load(open("D:/kdp-halloween-bold-easy/pages.json", encoding="utf-8"))


def be_title(subject):
    t = re.sub(r"^(a |an |two |a group of three |a group of |a colony of |a stack of three |a big |a spooky )?(cute (little |friendly |fluffy friendly |cartoon |old |tiny |crooked |decorated |smiling |carved |bubbling |haunted |friendly little )?)?", "", subject.strip())
    return t[0].upper() + t[1:]


def slug(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return s if len(s) <= 56 else s[:56].rsplit("-", 1)[0]


def split_page(src, idx, dest, a4_dest=None):
    r = PdfReader(HERE / src)
    w = PdfWriter(); w.add_page(r.pages[idx]); w.write(dest)
    if a4_dest:
        pg = r.pages[idx]; pw, ph = float(pg.mediabox.width), float(pg.mediabox.height)
        f = min(A4[0] / pw, A4[1] / ph)
        w2 = PdfWriter(); blank = w2.add_blank_page(width=A4[0], height=A4[1])
        blank.merge_transformed_page(pg, Transformation().scale(f, f).translate((A4[0] - pw * f) / 2, (A4[1] - ph * f) / 2))
        blank.mediabox = RectangleObject((0, 0, A4[0], A4[1]))
        w2.write(a4_dest)


def thumb(src, idx, dest, width=420):
    d = pdfium.PdfDocument(str(HERE / src)); p = d[idx]
    p.render(scale=width / p.get_width()).to_pil().convert("RGB").save(dest, "WEBP", quality=78, method=6)


def card(item):
    a4 = f'<a class="btn ghost" href="{item["a4"]}" download>A4 PDF</a>' if item.get("a4") else ""
    letter_label = "Letter PDF" if item.get("a4") else "Print (PDF)"
    return (f'<article class="pg"><a href="{item["pdf"]}" download><img src="{item["thumb"]}" width="420" height="{item["th"]}" alt="{item["title"]}, Halloween coloring page for adults" loading="lazy"></a>'
            f'<h3>{item["title"]}</h3><div class="acts"><a class="btn" href="{item["pdf"]}" download>{letter_label}</a>{a4}</div></article>')


def main():
    OUT.mkdir(parents=True, exist_ok=True); THUMBS.mkdir(exist_ok=True)
    for old in list(OUT.glob("*.pdf")) + list(THUMBS.glob("*.webp")): old.unlink()   # rebuild from scratch
    gs, be = [], []
    for n, (src, idx, title) in enumerate(GRAYSCALE, 1):
        base = f"grayscale-{n:02d}-{slug(title)}"
        split_page(src, idx, OUT / f"{base}.pdf", OUT / f"{base}-a4.pdf")
        thumb(src, idx, THUMBS / f"{base}.webp")
        gs.append(dict(title=title, pdf=f"print/adults/{base}.pdf", a4=f"print/adults/{base}-a4.pdf", thumb=f"print/adults/thumbs/{base}.webp", th=544))
    for n, (subject, fact) in enumerate(BE_SUBJECTS, 1):
        title = be_title(subject); base = f"bold-easy-{n:02d}-{slug(title)}"
        split_page(BE_PDF, n, OUT / f"{base}.pdf")           # p(n+1) in 1-based terms: page 2 is design 1
        thumb(BE_PDF, n, THUMBS / f"{base}.webp")
        be.append(dict(title=title, pdf=f"print/adults/{base}.pdf", thumb=f"print/adults/thumbs/{base}.webp", th=420, fact=fact))
    total = len(gs) + len(be)

    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": ["CollectionPage", "WebPage"], "@id": PAGE_URL + "#webpage", "url": PAGE_URL,
         "name": f"{total} Free Printable Halloween Coloring Pages for Adults",
         "description": f"{len(gs)} detailed grayscale pages and {len(be)} bold-and-easy pages, one PDF each, Letter and A4, no sign-up.",
         "inLanguage": "en", "isPartOf": {"@id": "https://ainjection.github.io/#site"},
         "breadcrumb": {"@id": PAGE_URL + "#breadcrumb"}, "datePublished": "2026-10-05", "dateModified": "2026-10-05",
         "author": {"@type": "Person", "name": "Robert Milven", "url": "https://ainjection.github.io/gentle-bookshop/about.html",
                    "worksFor": {"@id": "https://ainjection.github.io/#org"}},
         "publisher": {"@id": "https://ainjection.github.io/#org"},
         "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + gs[3]["thumb"]},
         "hasPart": [{"@type": "CreativeWork", "name": i["title"], "url": SITE + i["pdf"], "thumbnailUrl": SITE + i["thumb"],
                      "encodingFormat": "application/pdf", "isAccessibleForFree": True} for i in gs + be]},
        {"@type": "BreadcrumbList", "@id": PAGE_URL + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "The Gentle Bookshop", "item": "https://ainjection.github.io/"},
            {"@type": "ListItem", "position": 2, "name": "The Halloween Shelf", "item": SITE},
            {"@type": "ListItem", "position": 3, "name": "Halloween coloring pages for adults", "item": PAGE_URL}]},
    ]}

    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{total} Free Printable Halloween Coloring Pages for Adults | The Gentle Bookshop</title>
<meta name="description" content="{total} free Halloween coloring pages for adults: {len(gs)} detailed grayscale scenes and {len(be)} bold and easy designs. One PDF per page, Letter and A4, no email sign-up, from The Gentle Bookshop.">
<link rel="canonical" href="{PAGE_URL}">
<meta property="og:title" content="{total} Free Printable Halloween Coloring Pages for Adults">
<meta property="og:description" content="{len(gs)} grayscale scenes and {len(be)} bold and easy designs, one PDF each, Letter and A4, no sign-up.">
<meta property="og:image" content="{SITE}{gs[3]["thumb"]}">
<meta property="og:url" content="{PAGE_URL}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 84'%3E%3Cellipse cx='48' cy='48' rx='44' ry='34' fill='%23ff7a1a'/%3E%3Cpath d='M46 10 Q50 0 58 2 L54 12Z' fill='%233d6b24'/%3E%3Cpath d='M24 38 L36 32 L34 46Z M72 38 L60 32 L62 46Z M24 58 Q48 74 72 58 L48 62Z' fill='%231b0c00'/%3E%3C/svg%3E">
<link rel="preload" href="fonts/griffy-400.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">{json.dumps(ld, separators=(",", ":"))}</script>
<style>
@font-face{{font-family:'Griffy';font-style:normal;font-weight:400;font-display:swap;src:url(fonts/griffy-400.woff2) format('woff2')}}
@font-face{{font-family:'Nunito';font-style:normal;font-weight:400 900;font-display:swap;src:url(fonts/nunito-400.woff2) format('woff2')}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Nunito,system-ui,sans-serif;background:radial-gradient(120% 80% at 80% 0%,#3b1f55 0%,#22133a 45%,#0b0816 100%);background-color:#22133a;min-height:100vh;color:#f3ecff;line-height:1.6}}
.wrap{{max-width:1100px;margin:0 auto;padding:0 16px}}
nav{{padding:18px 0;font-weight:800}} nav a{{color:#b9a9d6;text-decoration:none}} nav a:hover{{color:#f3ecff}}
header{{padding:28px 0 12px;text-align:center}}
h1{{font-family:"Griffy",serif;font-size:clamp(2rem,5.5vw,3.3rem);line-height:1.1;color:#f3ecff}}
h1 em{{display:block;font-style:normal;color:#ffb347;font-size:.6em;margin-top:6px}}
.byline{{color:#b9a9d6;font-size:.9rem;margin-top:14px}} .byline a{{color:#b9a9d6}}
.intro{{max-width:46rem;margin:14px auto 0;color:#dcd2ee;font-size:1.06rem}}
.intro a{{color:#ffb347}}
h2{{font-family:"Griffy",serif;font-size:2rem;color:#ffb347;margin:44px 0 6px}}
.lead{{color:#b9a9d6;max-width:46rem;margin-bottom:18px}} .lead a{{color:#ffb347}}
.grid{{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}}
.pg{{background:#22133a;border:1px solid rgba(255,255,255,.1);border-radius:14px;overflow:hidden;display:flex;flex-direction:column}}
.pg img{{width:100%;height:auto;display:block;background:#fff}}
.pg h3{{font-size:.95rem;line-height:1.3;padding:10px 12px 4px;font-weight:700}}
.acts{{display:flex;flex-wrap:wrap;gap:6px;padding:4px 12px 12px;margin-top:auto}}
.btn{{display:inline-block;font-weight:800;padding:7px 12px;border-radius:999px;background:#ff7a1a;color:#1b1030;text-decoration:none;font-size:.85rem}}
.btn.ghost{{background:transparent;color:#f3ecff;border:2px solid rgba(255,255,255,.35)}}
.btn:hover{{filter:brightness(1.1)}}
.books{{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));margin-top:14px}}
.book{{display:flex;gap:12px;align-items:center;background:rgba(255,255,255,.05);border-radius:14px;padding:12px;text-decoration:none;color:#f3ecff}}
.book img{{width:64px;height:auto;border-radius:4px}} .book strong{{display:block;font-size:.95rem}} .book span{{color:#b9a9d6;font-size:.82rem}}
.tipgrid{{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}}
.tip{{background:rgba(255,255,255,.05);border-radius:14px;padding:16px 18px}} .tip h3{{font-size:1.05rem;margin-bottom:4px}} .tip p{{color:#b9a9d6}} .tip a{{color:#ffb347}}
.note{{color:#b9a9d6;font-size:.9rem;margin-top:16px}}
footer{{text-align:center;color:#b9a9d6;font-size:.9rem;padding:34px 0 40px}} footer a{{color:#b9a9d6}}
</style>
</head>
<body>
<div class="wrap">
  <nav><a href="https://ainjection.github.io/halloween-books/">&larr; The Halloween Shelf</a> &nbsp;&middot;&nbsp; <a href="halloween-coloring-pages-printable.html">Pages for kids</a></nav>
  <header>
    <h1>{total} Halloween Coloring Pages for Adults <em>free printable PDFs, one page each</em></h1>
    <p class="byline">By <a href="https://ainjection.github.io/gentle-bookshop/about.html">Robert Milven</a>, The Gentle Bookshop, Wakefield. Updated <time datetime="2026-10-05">5 October 2026</time>.</p>
    <p class="intro">Every page below is a single PDF you can print at home on ordinary paper, Letter or A4. No email address, no sign-up, no watermark. The {len(gs)} grayscale pages are the detailed, shaded kind made for coloured pencils; the {len(be)} bold and easy pages have thick lines and big spaces, good for markers, a tired evening, or colouring with the kids. All of them come from our own Halloween books, so if you like a page the whole book is on Amazon.</p>
  </header>
  <main>
    <h2 id="grayscale">Grayscale Halloween coloring pages ({len(gs)})</h2>
    <p class="lead">Grayscale means the shading is already printed in soft grey. You lay colour over it and the shadows show through, so the picture looks three-dimensional with very little effort. Soft, wax-based pencils work best; <a href="best-pencils-for-grayscale-coloring.html">here is why, and which ones</a>. Five pages are from <a href="https://ainjection.github.io/gentle-bookshop/books/halloween-grayscale-vol1.html">Volume One</a> (classic scenes) and five from <a href="https://ainjection.github.io/gentle-bookshop/books/halloween-grayscale-vol2.html">Volume Two</a> (Victorian Gothic).</p>
    <section class="grid" aria-label="Grayscale pages">{''.join(card(i) for i in gs)}</section>

    <h2 id="bold-easy">Bold and easy Halloween coloring pages ({len(be)})</h2>
    <p class="lead">Thick friendly lines, big spaces, and a "Did you know?" Halloween fact on every page. These are square pages, so they print the same on Letter or A4 with "Fit to page". They are the complete <a href="free-halloween-coloring-book.html">Halloween Bold and Easy Coloring Book</a>, which you can also download as one PDF.</p>
    <section class="grid" aria-label="Bold and easy pages">{''.join(card(i) for i in be)}</section>

    <h2>Printing tips</h2>
    <div class="tipgrid">
      <div class="tip"><h3>Letter or A4?</h3><p>Grayscale pages come in both sizes. Bold and easy pages are square and fit either paper; choose "Fit to page" in the print box.</p></div>
      <div class="tip"><h3>Which paper?</h3><p>Ordinary 80 gsm printer paper is fine for pencils. For markers use thicker paper, or put a spare sheet underneath. Each page is single-sided, so nothing bleeds onto another picture.</p></div>
      <div class="tip"><h3>Pencils for grayscale</h3><p>Soft pencils lay see-through colour over the grey; hard school pencils look chalky. A colourless blender pencil smooths everything. <a href="best-pencils-for-grayscale-coloring.html">The short pencil guide</a> explains it.</p></div>
      <div class="tip"><h3>Print quality</h3><p>Pick "High" or "Best" quality for the grayscale pages so the fine shading prints cleanly. Draft mode drops the light greys.</p></div>
    </div>

    <h2>The books these pages come from</h2>
    <div class="books">
      <a class="book" href="https://ainjection.github.io/gentle-bookshop/books/halloween-grayscale-vol1.html"><img src="covers/halloween-grayscale-vol1.webp" width="64" height="83" alt="Halloween Grayscale, Volume One cover" loading="lazy"><div><strong>Halloween Grayscale, Volume One</strong><span>50 classic scenes, 106 pages</span></div></a>
      <a class="book" href="https://ainjection.github.io/gentle-bookshop/books/halloween-grayscale-vol2.html"><img src="covers/halloween-grayscale-vol2.webp" width="64" height="83" alt="Halloween Grayscale, Volume Two cover" loading="lazy"><div><strong>Halloween Grayscale, Volume Two</strong><span>50 Victorian Gothic scenes, 106 pages</span></div></a>
      <a class="book" href="https://ainjection.github.io/gentle-bookshop/books/halloween-grayscale-complete.html"><img src="covers/halloween-grayscale-complete.webp" width="64" height="83" alt="Halloween Grayscale: The Complete Collection cover" loading="lazy"><div><strong>The Complete Collection</strong><span>All 100 designs, 206 pages</span></div></a>
      <a class="book" href="free-halloween-coloring-book.html"><img src="covers/halloween-bold-easy.webp" width="64" height="64" alt="Halloween Bold and Easy Coloring Book cover" loading="lazy"><div><strong>Halloween Bold and Easy</strong><span>The whole book as one PDF</span></div></a>
    </div>
    <p class="note">These pages are for personal, home and classroom use. Please don't sell them or upload them elsewhere; link to this page instead. Book links go to our own book pages, which link on to Amazon.com; as an Amazon Associate we earn from qualifying purchases. Children's pages: <a href="halloween-coloring-pages-printable.html" style="color:#ffb347">Halloween coloring pages for kids</a>.</p>
  </main>
  <footer>Made by <a href="https://ainjection.github.io/gentle-bookshop/">The Gentle Bookshop</a>, Wakefield, UK. All books are printed and shipped by Amazon.</footer>
</div>
<script src="track.js" defer></script>
</body>
</html>
'''
    (HERE / "halloween-coloring-pages-for-adults.html").write_text(html, encoding="utf-8")
    print(f"{total} pages: {len(gs)} grayscale (+A4), {len(be)} bold-easy; html {len(html)//1024} KB")
    return total


if __name__ == "__main__":
    total = main()
    assert total == 60
    assert len(list(OUT.glob("*.pdf"))) == 10 * 2 + 50 and len(list(THUMBS.glob("*.webp"))) == 60
    print("self-check ok")
