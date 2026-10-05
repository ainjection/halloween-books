"""Pre-render the book cards and the JSON-LD into index.html (SEO audit 5 Oct 2026, Phase 1).

The JS `BOOKS` object in index.html stays the single source for slug / ASIN / short name / audience.
This script reads it, adds the verified facts below (taken from the Book schema on the
/gentle-bookshop/books/halloween-*.html pages), and writes static cards into every
<div class="shelf" data-books="..."> plus a JSON-LD block in <head>. Re-runnable: it replaces
what it wrote last time. The JS still enhances the cards (tilt, ghost) but no longer builds them.

    python build_static.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
SITE = "https://ainjection.github.io"
SHELF = f"{SITE}/halloween-books/"
BOOK_PAGE = SITE + "/gentle-bookshop/books/{slug}.html"
AMZ = "https://www.amazon.com/dp/{asin}?tag=gentlebooksho-20"

# Verified from each book page's Book JSON-LD (numberOfPages, name) and visible age text.
FACTS = {
    "halloween-seek-and-find":      dict(pages=105, age="4-8",   full="Halloween Seek and Find: A Hidden Pictures Activity & Colouring Book for Kids Ages 4-8"),
    "halloween-mosaics-vol1":       dict(pages=112, age="6-12",  full="Halloween Mystery Mosaics, Volume One: Color by Number for Kids Ages 6-12"),
    "halloween-mosaics-vol2":       dict(pages=112, age="6-12",  full="Halloween Mystery Mosaics, Volume Two: Color by Number for Kids Ages 6-12"),
    "halloween-mosaics-complete":   dict(pages=218, age="6-12",  full="Halloween Mystery Mosaics: The Complete Collection: Color by Number for Kids Ages 6-12"),
    "halloween-word-search-easy":   dict(pages=103, age="18-",   full="Happy Halloween Word Search: 80 Easy Large Print Puzzles for Adults and Seniors"),
    "halloween-word-search-hard":   dict(pages=103, age="18-",   full="Happy Halloween Word Search: 80 Hard Large Print Puzzles for Adults and Seniors"),
    "halloween-grayscale-vol1":     dict(pages=106, age="18-",   full="Halloween Grayscale Coloring Book for Adults, Volume One: 50 Detailed Designs"),
    "halloween-grayscale-vol2":     dict(pages=106, age="18-",   full="Halloween Grayscale Coloring Book for Adults, Volume Two: 50 Victorian Gothic Scenes"),
    "halloween-grayscale-complete": dict(pages=206, age="18-",   full="Halloween Grayscale Coloring Book for Adults: The Complete Collection"),
    "halloween-bold-easy":          dict(pages=None, age="6-",   full="Halloween Bold and Easy Coloring Book"),
    "halloween-pocket-sudoku":      dict(pages=230, age="18-",   full="Pocket Sudoku & Grayscale Coloring: Halloween Edition: 100 Sudoku Puzzles + 100 Grayscale Pages"),
}
COVER_H = {  # 320px-wide webp heights, from the conversion run
    "halloween-bold-easy": 320, "halloween-mosaics-complete": 426, "halloween-mosaics-vol1": 412,
    "halloween-mosaics-vol2": 426,
}

GHOST = ('<svg viewBox="0 0 100 120" width="100%"><path d="M50 4 C22 4 8 26 8 52 V112 L20 102 L32 114 L44 102 L56 114 '
         'L68 102 L80 114 L92 104 V52 C92 26 78 4 50 4Z" fill="#eef1ff"/><ellipse cx="36" cy="48" rx="7" ry="10" fill="#1b1030"/>'
         '<ellipse cx="64" cy="48" rx="7" ry="10" fill="#1b1030"/><ellipse cx="50" cy="72" rx="8" ry="10" fill="#1b1030"/></svg>')


def read_books(html):
    m = re.search(r"const BOOKS = \{(.*?)\n  \};", html, re.S)
    books = {}
    for slug, asin, name, who in re.findall(r"'([a-z0-9-]+)': \['([A-Z0-9]*)', '([^']*)', '([^']*)'\]", m.group(1)):
        books[slug] = (asin, name, who)
    assert len(books) == 11, books.keys()
    return books


def card(slug, asin, name, who):
    page = BOOK_PAGE.format(slug=slug) if asin else "free-halloween-coloring-book.html"
    h = COVER_H.get(slug, 414)
    alt = f"{name} book cover"
    buy = (f'<a class="buy" href="{AMZ.format(asin=asin)}" target="_blank" rel="noopener sponsored">See it on Amazon</a>'
           f'<a class="dl" href="pages/{slug}-sample-pages.pdf" download>Print 5 sample pages</a>') if asin else \
          '<a class="buy" href="free-halloween-coloring-book.html">Download it free</a>'
    return (f'<div class="card"><div class="cw"><div class="pk">{GHOST}</div>'
            f'<a href="{page}" tabindex="-1" aria-hidden="true"><div class="tilt"><img src="covers/{slug}.webp" width="320" height="{h}" alt="{alt}" loading="lazy"></div></a></div>'
            f'<h3><a href="{page}">{name}</a></h3><span class="who">{who}</span><div class="acts">{buy}</div></div>')


def jsonld(books):
    items = []
    for i, (slug, (asin, name, who)) in enumerate(books.items(), 1):
        f = FACTS[slug]
        book = {"@type": "Book", "@id": BOOK_PAGE.format(slug=slug) + "#book" if asin else SHELF + "free-halloween-coloring-book.html#book",
                "name": f["full"], "url": BOOK_PAGE.format(slug=slug) if asin else SHELF + "free-halloween-coloring-book.html",
                "image": f"{SHELF}covers/{slug}.jpg", "bookFormat": "https://schema.org/Paperback" if asin else "https://schema.org/EBook",
                "inLanguage": "en", "typicalAgeRange": f["age"],
                "author": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"}}
        if f["pages"]:
            book["numberOfPages"] = f["pages"]
        if asin:
            book["sku"] = asin
        items.append({"@type": "ListItem", "position": i, "item": book})
    graph = [
        {"@type": ["CollectionPage", "WebPage"], "@id": SHELF + "#webpage", "url": SHELF,
         "name": "Halloween Colouring, Seek and Find and Puzzle Books | The Gentle Bookshop",
         "description": "Spooky, never scary. Halloween grayscale colouring books for adults, colour-by-number mosaics and seek-and-find for kids, and large-print word search for seniors.",
         "inLanguage": "en-GB", "isPartOf": {"@id": SITE + "/#site"}, "breadcrumb": {"@id": SHELF + "#breadcrumb"},
         "mainEntity": {"@id": SHELF + "#shelf"}, "primaryImageOfPage": {"@type": "ImageObject", "url": SHELF + "og.jpg"},
         "dateModified": "2026-10-05"},
        {"@type": "BreadcrumbList", "@id": SHELF + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "The Gentle Bookshop", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "The Halloween Shelf", "item": SHELF}]},
        {"@type": "Organization", "@id": SITE + "/#org", "name": "The Gentle Bookshop", "url": SITE + "/",
         "logo": {"@type": "ImageObject", "url": SITE + "/gentle-bookshop/logo-512.png", "width": 512, "height": 512},
         "sameAs": ["https://www.youtube.com/@TheGentleBookshop", "https://www.tiktok.com/@tgbookshop"]},
        {"@type": "ItemList", "@id": SHELF + "#shelf", "name": "The Halloween Shelf", "numberOfItems": len(items), "itemListElement": items},
    ]
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}, separators=(",", ":")) + "</script>"


def main():
    p = HERE / "index.html"
    html = p.read_text(encoding="utf-8")
    books = read_books(html)

    def fill(m):
        attr = m.group(1)
        slugs = list(books) if attr == "all" else attr.split(",")
        return f'<div class="shelf" data-books="{attr}"><!--static-->' + "".join(card(s, *books[s]) for s in slugs) + "<!--/static--></div>"
    html, n = re.subn(r'<div class="shelf" data-books="([a-z0-9,-]+)">(?:<!--static-->.*?<!--/static-->)?</div>', fill, html, flags=re.S)
    assert n == 6, n

    ld = "<!--ld-->" + jsonld(books) + "<!--/ld-->"
    if "<!--ld-->" in html:
        html = re.sub(r"<!--ld-->.*?<!--/ld-->", lambda _: ld, html, flags=re.S)
    else:
        html = html.replace("</head>", ld + "\n</head>", 1)
    p.write_text(html, encoding="utf-8")
    print(f"filled {n} shelves, {len(books)} books, JSON-LD {len(ld)} bytes")


if __name__ == "__main__":
    main()
    # self-check: the raw HTML now carries every book page link and no empty alt on covers
    html = (HERE / "index.html").read_text(encoding="utf-8")
    assert html.count("/gentle-bookshop/books/halloween-") >= 10 * 2 * 2  # 10 books, 2 links each, in the 'all' shelf + section shelves
    assert 'alt="" loading' not in html.split("<script")[0]
    print("self-check ok")
