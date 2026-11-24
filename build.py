#!/usr/bin/env python3
"""
Idea Immobiliare — Generatore sito statico
Scansiona annunci/ e genera HTML statico in docs/
"""

import os
import json
import shutil
import re
import unicodedata
from pathlib import Path
from datetime import datetime

# ─── Configurazione ──────────────────────────────────────────────

SITE_TITLE = "Idea Immobiliare"
SITE_OWNER = "di Mordini Fabrizio"
SITE_TAGLINE = "La tua casa in Romagna"

CONTACT_ADDRESS = "Via Alberto Acquacalda 6/6, 48022 Lugo (RA)"
CONTACT_EMAIL = "info.ideaimmobiliarelugo@gmail.com"
CONTACT_PHONE = ""   # Da compilare
CONTACT_HOURS = ""   # Da compilare

CHI_SIAMO = (
    "Idea Immobiliare è un'agenzia immobiliare di Lugo che offre supporto "
    "nella compravendita e locazione di immobili. Mettiamo al primo posto "
    "la fiducia, l'ascolto e la trasparenza per accompagnarti nella scelta "
    "della tua casa ideale."
)

ANNUNCI_DIR = Path("annunci")
OUTPUT_DIR = Path("docs")
ASSETS_SRC = Path("assets")
NUM_EVIDENZA = 4

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}


# ─── Utilità ─────────────────────────────────────────────────────

def slugify(text):
    """Converte testo in slug URL-safe."""
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text or 'senza-titolo'


def display_name(folder_name):
    """Nome visualizzato da nome cartella."""
    return folder_name.replace('-', ' ').replace('_', ' ').title()


def parse_prezzo_num(prezzo_str):
    """Estrae valore numerico dal prezzo (formato italiano)."""
    if not prezzo_str:
        return None
    cleaned = prezzo_str.replace('€', '').replace('/mese', '')
    cleaned = cleaned.replace('.', '').replace(',', '.').strip()
    nums = re.findall(r'[\d.]+', cleaned)
    if nums:
        try:
            return int(float(nums[0]))
        except ValueError:
            return None
    return None


def parse_int_field(value):
    """Estrae intero da un campo."""
    if not value:
        return None
    nums = re.findall(r'\d+', value)
    if nums:
        try:
            return int(nums[0])
        except ValueError:
            return None
    return None


def parse_info_txt(filepath, errors):
    """
    Legge un info.txt con campi case-insensitive.
    Ritorna dict con campi, o None se illeggibile.
    """
    try:
        try:
            content = filepath.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = filepath.read_text(encoding='latin-1')
    except Exception as e:
        errors.append(f"Impossibile leggere {filepath}: {e}")
        return None

    fields = {
        'sottotitolo': '',
        'prezzo': '',
        'indirizzo': '',
        'classe_energetica': '',
        'mq': '',
        'camere': '',
        'descrizione': '',
    }

    parts = re.split(r'^---\s*$', content, maxsplit=1, flags=re.MULTILINE)
    header = parts[0]
    body = parts[1].strip() if len(parts) > 1 else ''
    fields['descrizione'] = body

    for line in header.strip().split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            if key in fields:
                fields[key] = value

    return fields


def folder_mtime(folder):
    """Timestamp più recente fra i file nella cartella."""
    latest = 0
    for f in folder.iterdir():
        if f.is_file():
            t = f.stat().st_mtime
            if t > latest:
                latest = t
    return latest


def find_copertina(directory):
    """Cerca copertina.* nella directory."""
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        for name in [f'copertina{ext}', f'Copertina{ext}', f'COPERTINA{ext}']:
            candidate = directory / name
            if candidate.exists():
                return candidate
    return None


# ─── Scansione ───────────────────────────────────────────────────

def scan_annunci():
    """Scansiona la struttura annunci/. Ritorna (data, errors)."""
    errors = []
    data = {'vendite': {}, 'affitti': {}}

    if not ANNUNCI_DIR.exists():
        errors.append(f"Cartella '{ANNUNCI_DIR}' non trovata.")
        return data, errors

    for tipo in ['vendite', 'affitti']:
        tipo_dir = ANNUNCI_DIR / tipo
        if not tipo_dir.exists():
            continue

        for comune_dir in sorted(tipo_dir.iterdir()):
            if not comune_dir.is_dir():
                continue

            comune_name = comune_dir.name
            comune_slug = slugify(comune_name)
            copertina = find_copertina(comune_dir)
            annunci = []

            for ann_dir in sorted(comune_dir.iterdir()):
                if not ann_dir.is_dir():
                    continue

                titolo = ann_dir.name
                ann_slug = slugify(titolo)
                info_file = ann_dir / 'info.txt'

                if not info_file.exists():
                    errors.append(
                        f"'{titolo}' ({tipo}/{comune_name}) — info.txt mancante, ignorato."
                    )
                    continue

                fields = parse_info_txt(info_file, errors)
                if fields is None:
                    continue

                if not fields['prezzo']:
                    errors.append(
                        f"'{titolo}' ({tipo}/{comune_name}) — prezzo mancante."
                    )
                if not fields['sottotitolo']:
                    errors.append(
                        f"'{titolo}' ({tipo}/{comune_name}) — sottotitolo mancante."
                    )

                images = sorted(
                    [f for f in ann_dir.iterdir()
                     if f.is_file() and f.suffix.lower() in IMAGE_EXTS]
                )
                if not images:
                    errors.append(
                        f"'{titolo}' ({tipo}/{comune_name}) — nessuna immagine."
                    )

                annunci.append({
                    'titolo': titolo,
                    'slug': ann_slug,
                    'tipo': tipo,
                    'comune': comune_name,
                    'comune_slug': comune_slug,
                    'fields': fields,
                    'images': images,
                    'source_dir': ann_dir,
                    'mtime': folder_mtime(ann_dir),
                })

            data[tipo][comune_name] = {
                'slug': comune_slug,
                'display_name': display_name(comune_name),
                'copertina': copertina,
                'annunci': annunci,
            }

    return data, errors


# ─── Componenti HTML ─────────────────────────────────────────────

def rel(depth):
    """Prefisso relativo per la profondità data."""
    return '../' * depth


def html_head(title, depth=0):
    p = rel(depth)
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Idea Immobiliare di Mordini Fabrizio — Agenzia immobiliare a Lugo (RA). Vendita e affitto immobili in Romagna.">
    <title>{title} | Idea Immobiliare</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <link rel="stylesheet" href="{p}assets/style.css">
    <link rel="icon" href="{p}assets/logo.jpg" type="image/jpeg">
</head>"""


def html_nav(depth=0, active=''):
    p = rel(depth)

    def ac(page):
        return ' class="active"' if active == page else ''

    return f"""
<nav class="navbar" id="navbar">
    <div class="nav-container">
        <a href="{p}index.html" class="nav-logo">
            <img src="{p}assets/logo.jpg" alt="Idea Immobiliare">
            <div class="nav-logo-text">
                <span class="nav-title">Idea Immobiliare</span>
                <span class="nav-subtitle">{SITE_OWNER}</span>
            </div>
        </a>
        <div class="nav-search-wrapper">
            <input type="text" id="search-input" class="nav-search" placeholder="Cerca annunci..." autocomplete="off" data-base="{p}">
            <div id="search-results" class="search-dropdown"></div>
        </div>
        <button class="nav-toggle" id="nav-toggle" aria-label="Menu">
            <span></span><span></span><span></span>
        </button>
        <ul class="nav-links" id="nav-links">
            <li><a href="{p}index.html"{ac('home')}>Home</a></li>
            <li><a href="{p}vendite/index.html"{ac('vendite')}>Vendite</a></li>
            <li><a href="{p}affitti/index.html"{ac('affitti')}>Affitti</a></li>
            <li><a href="{p}contatti/index.html"{ac('contatti')}>Contatti</a></li>
        </ul>
    </div>
</nav>"""


def html_footer(depth=0):
    p = rel(depth)
    phone = (
        f'<p><a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>'
        if CONTACT_PHONE
        else '<p><em>In arrivo</em></p>'
    )
    hours = (
        f'<p>{CONTACT_HOURS}</p>'
        if CONTACT_HOURS
        else '<p><em>In arrivo</em></p>'
    )
    year = datetime.now().year

    return f"""
<footer class="footer">
    <div class="footer-container">
        <div class="footer-col footer-brand">
            <img src="{p}assets/logo.jpg" alt="Idea Immobiliare" class="footer-logo">
            <p class="footer-name">Idea Immobiliare</p>
            <p class="footer-owner">{SITE_OWNER}</p>
        </div>
        <div class="footer-col">
            <h4>Contatti</h4>
            <p>{CONTACT_ADDRESS}</p>
            <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
            {phone}
        </div>
        <div class="footer-col">
            <h4>Orari</h4>
            {hours}
        </div>
    </div>
    <div class="footer-bottom">
        <p>&copy; {year} Idea Immobiliare di Mordini Fabrizio. Tutti i diritti riservati.</p>
    </div>
</footer>"""


def html_end(depth=0):
    p = rel(depth)
    return f"""
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="{p}assets/script.js"></script>
</body>
</html>"""


# ─── Card annuncio ───────────────────────────────────────────────

def annuncio_card(a, depth=0):
    p = rel(depth)
    f = a['fields']

    if a['images']:
        img_src = f"{p}img/{a['tipo']}/{a['comune_slug']}/{a['slug']}/{a['images'][0].name}"
        img = f'<img src="{img_src}" alt="{a["titolo"]}" loading="lazy">'
    else:
        img = '<div class="card-noimg">Nessuna foto</div>'

    prezzo = f'<span class="card-price">{f["prezzo"]}</span>' if f['prezzo'] else ''
    sub = f'<p class="card-sub">{f["sottotitolo"]}</p>' if f['sottotitolo'] else ''
    badge_text = "Vendita" if a['tipo'] == 'vendite' else "Affitto"
    link = f"{p}{a['tipo']}/{a['comune_slug']}/{a['slug']}/index.html"
    comune_display = display_name(a['comune'])

    return f"""
    <a href="{link}" class="annuncio-card"
       data-prezzo="{parse_prezzo_num(f['prezzo']) or ''}"
       data-mq="{parse_int_field(f['mq']) or ''}"
       data-camere="{parse_int_field(f['camere']) or ''}">
        <div class="card-img">
            {img}
            <span class="card-badge badge-{a['tipo']}">{badge_text}</span>
        </div>
        <div class="card-body">
            <h3 class="card-title">{a['titolo']}</h3>
            {sub}
            {prezzo}
            <p class="card-loc">{comune_display}</p>
        </div>
    </a>"""


# ─── Pagine ──────────────────────────────────────────────────────

def page_home(data):
    all_ann = []
    for tipo in data.values():
        for cd in tipo.values():
            all_ann.extend(cd['annunci'])
    all_ann.sort(key=lambda x: x['mtime'], reverse=True)
    featured = all_ann[:NUM_EVIDENZA]

    cards = ''.join(annuncio_card(a, 0) for a in featured)

    evidenza = ''
    if cards:
        evidenza = f"""
    <section class="section">
        <div class="container">
            <h2 class="section-title">In Evidenza</h2>
            <div class="annunci-grid">{cards}
            </div>
        </div>
    </section>"""

    return f"""{html_head("Home", 0)}
<body>
{html_nav(0, 'home')}

    <section class="hero">
        <div class="hero-inner">
            <img src="assets/logo.jpg" alt="Idea Immobiliare" class="hero-logo">
            <h1>{SITE_TITLE}</h1>
            <p class="hero-owner">{SITE_OWNER}</p>
            <p class="hero-tagline">{SITE_TAGLINE}</p>
            <div class="hero-cta">
                <a href="vendite/index.html" class="btn btn-primary">Vendite</a>
                <a href="affitti/index.html" class="btn btn-outline">Affitti</a>
            </div>
        </div>
    </section>
{evidenza}
    <section class="section section-about">
        <div class="container">
            <h2 class="section-title">Chi Siamo</h2>
            <p class="about-text">{CHI_SIAMO}</p>
            <a href="contatti/index.html" class="btn btn-primary">Contattaci</a>
        </div>
    </section>

{html_footer(0)}
{html_end(0)}"""


def page_tipo(tipo, data):
    label = "Vendite" if tipo == "vendite" else "Affitti"

    comuni_cards = ''
    for cn, cd in sorted(data[tipo].items()):
        n = len(cd['annunci'])
        if cd['copertina']:
            cimg = f'<img src="{cd["slug"]}/copertina{cd["copertina"].suffix}" alt="{cd["display_name"]}" loading="lazy">'
        else:
            cimg = f'<div class="comune-ph">{cd["display_name"][0]}</div>'

        comuni_cards += f"""
        <a href="{cd['slug']}/index.html" class="comune-card">
            <div class="comune-img">{cimg}</div>
            <div class="comune-info">
                <h3>{cd['display_name']}</h3>
                <p>{n} annunc{'io' if n == 1 else 'i'}</p>
            </div>
        </a>"""

    all_ann = []
    for cd in data[tipo].values():
        all_ann.extend(cd['annunci'])
    all_ann.sort(key=lambda x: x['mtime'], reverse=True)
    ann_cards = ''.join(annuncio_card(a, 1) for a in all_ann)

    filters = ''
    if all_ann:
        filters = filters_bar()

    empty = '' if all_ann else '<p class="no-results">Nessun annuncio disponibile.</p>'

    return f"""{html_head(label, 1)}
<body>
{html_nav(1, tipo)}

    <section class="page-header">
        <div class="container">
            <h1 class="page-title">{label}</h1>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <h2 class="section-title">Zone</h2>
            <div class="comuni-grid">{comuni_cards}
            </div>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <h2 class="section-title">Tutti gli annunci</h2>
            {filters}
            <div class="annunci-grid" id="annunci-grid">{ann_cards}
            </div>
            {empty}
        </div>
    </section>

{html_footer(1)}
{html_end(1)}"""


def page_comune(tipo, comune_name, cd, data):
    label = "Vendite" if tipo == "vendite" else "Affitti"
    dn = cd['display_name']
    annunci = sorted(cd['annunci'], key=lambda x: x['mtime'], reverse=True)
    cards = ''.join(annuncio_card(a, 2) for a in annunci)
    n = len(annunci)

    header_bg = ''
    if cd['copertina']:
        img_p = f"copertina{cd['copertina'].suffix}"
        header_bg = f' style="background-image:url(\'{img_p}\')"'

    filters = filters_bar() if annunci else ''
    empty = '' if annunci else '<p class="no-results">Nessun annuncio per questa zona.</p>'

    return f"""{html_head(f"{dn} — {label}", 2)}
<body>
{html_nav(2, tipo)}

    <section class="comune-header"{header_bg}>
        <div class="comune-header-overlay">
            <div class="container">
                <nav class="breadcrumb">
                    <a href="../../index.html">Home</a> &rsaquo;
                    <a href="../index.html">{label}</a> &rsaquo;
                    <span>{dn}</span>
                </nav>
                <h1 class="page-title">{dn}</h1>
                <p class="page-sub">{n} annunc{'io' if n == 1 else 'i'} disponibil{'e' if n == 1 else 'i'}</p>
            </div>
        </div>
    </section>

    <section class="section">
        <div class="container">
            {filters}
            <div class="annunci-grid" id="annunci-grid">{cards}
            </div>
            {empty}
        </div>
    </section>

{html_footer(2)}
{html_end(2)}"""


def page_annuncio(a):
    f = a['fields']
    tipo_label = "Vendite" if a['tipo'] == 'vendite' else "Affitti"
    badge_label = "Vendita" if a['tipo'] == 'vendite' else "Affitto"
    comune_dn = display_name(a['comune'])
    p = rel(3)

    # Gallery
    slides = ''
    thumbs = ''
    for i, img in enumerate(a['images']):
        src = f"{p}img/{a['tipo']}/{a['comune_slug']}/{a['slug']}/{img.name}"
        act = ' active' if i == 0 else ''
        slides += f'        <div class="gallery-slide{act}" data-index="{i}"><img src="{src}" alt="{a["titolo"]} — Foto {i+1}"></div>\n'
        thumbs += f'        <button class="gallery-thumb{act}" data-index="{i}"><img src="{src}" alt="Miniatura {i+1}"></button>\n'

    nav_btns = ''
    if len(a['images']) > 1:
        nav_btns = """
            <button class="gallery-prev" onclick="galleryPrev()">&lsaquo;</button>
            <button class="gallery-next" onclick="galleryNext()">&rsaquo;</button>"""

    prezzo = f'<div class="detail-price">{f["prezzo"]}</div>' if f['prezzo'] else ''
    sub = f'<p class="detail-sub">{f["sottotitolo"]}</p>' if f['sottotitolo'] else ''
    classe = f'<span class="badge-classe">Classe {f["classe_energetica"]}</span>' if f['classe_energetica'] else ''

    # Dettagli rapidi
    details = []
    if f['mq']:
        details.append(f'<span class="detail-chip">{f["mq"]} mq</span>')
    if f['camere']:
        details.append(f'<span class="detail-chip">{f["camere"]} camere</span>')
    if f['classe_energetica']:
        details.append(f'<span class="detail-chip">Classe {f["classe_energetica"]}</span>')
    chips = f'<div class="detail-chips">{"".join(details)}</div>' if details else ''

    # Descrizione
    desc = ''
    if f['descrizione']:
        paras = [pp.strip() for pp in f['descrizione'].split('\n') if pp.strip()]
        desc = '\n'.join(f'                <p>{pp}</p>' for pp in paras)

    # Mappa
    map_section = ''
    if f['indirizzo']:
        map_section = f"""
            <section class="detail-block">
                <h2>Posizione</h2>
                <div class="detail-map" id="detail-map" data-address="{f['indirizzo']}"></div>
                <p class="map-address">{f['indirizzo']}</p>
            </section>"""

    # CTA
    email_subject = f"Informazioni: {a['titolo']}"
    phone_btn = ''
    if CONTACT_PHONE:
        phone_btn = f'<a href="tel:{CONTACT_PHONE}" class="btn btn-primary mobile-only">Chiama</a>'

    return f"""{html_head(a['titolo'], 3)}
<body>
{html_nav(3, a['tipo'])}

    <section class="section detail-page">
        <div class="container">
            <nav class="breadcrumb">
                <a href="{p}index.html">Home</a> &rsaquo;
                <a href="{p}{a['tipo']}/index.html">{tipo_label}</a> &rsaquo;
                <a href="{p}{a['tipo']}/{a['comune_slug']}/index.html">{comune_dn}</a> &rsaquo;
                <span>{a['titolo']}</span>
            </nav>

            <div class="detail-header">
                <div>
                    <span class="card-badge badge-{a['tipo']}">{badge_label}</span>
                    <h1 class="detail-title">{a['titolo']}</h1>
                    {sub}
                    {chips}
                </div>
                {prezzo}
            </div>

            <div class="gallery" id="gallery">
                <div class="gallery-main">
{slides}{nav_btns}
                    <span class="gallery-counter" id="gallery-counter"></span>
                </div>
                <div class="gallery-thumbs">
{thumbs}                </div>
            </div>

            <div class="detail-content">
                <section class="detail-block">
                    <h2>Descrizione</h2>
{desc}
                </section>
{map_section}
                <div class="detail-cta">
                    <a href="mailto:{CONTACT_EMAIL}?subject={email_subject}" class="btn btn-primary">Scrivi un'email</a>
                    {phone_btn}
                </div>
            </div>
        </div>
    </section>

    <div class="lightbox" id="lightbox">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <button class="lightbox-prev" onclick="lightboxPrev()">&lsaquo;</button>
        <button class="lightbox-next" onclick="lightboxNext()">&rsaquo;</button>
        <div class="lightbox-body">
            <img id="lightbox-img" src="" alt="">
        </div>
        <span class="lightbox-counter" id="lightbox-counter"></span>
    </div>

{html_footer(3)}
{html_end(3)}"""


def page_contatti():
    phone_item = (
        f'<p><a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>'
        if CONTACT_PHONE
        else '<p><em>In arrivo</em></p>'
    )
    hours_item = (
        f'<p>{CONTACT_HOURS}</p>'
        if CONTACT_HOURS
        else '<p><em>In arrivo</em></p>'
    )
    email_btn = f'<a href="mailto:{CONTACT_EMAIL}" class="btn btn-primary">Scrivi un\'email</a>'
    phone_btn = ''
    if CONTACT_PHONE:
        phone_btn = f'<a href="tel:{CONTACT_PHONE}" class="btn btn-primary mobile-only">Chiama</a>'

    return f"""{html_head("Contatti", 1)}
<body>
{html_nav(1, 'contatti')}

    <section class="page-header">
        <div class="container">
            <h1 class="page-title">Contatti</h1>
        </div>
    </section>

    <section class="section">
        <div class="container">
            <div class="contacts-grid">
                <div class="contacts-info">
                    <div class="contact-row">
                        <h3>Indirizzo</h3>
                        <p>{CONTACT_ADDRESS}</p>
                    </div>
                    <div class="contact-row">
                        <h3>Email</h3>
                        <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
                    </div>
                    <div class="contact-row">
                        <h3>Telefono</h3>
                        {phone_item}
                    </div>
                    <div class="contact-row">
                        <h3>Orari</h3>
                        {hours_item}
                    </div>
                    <div class="contact-cta">
                        {email_btn}
                        {phone_btn}
                    </div>
                </div>
                <div class="contacts-map" id="contacts-map" data-address="{CONTACT_ADDRESS}"></div>
            </div>
        </div>
    </section>

{html_footer(1)}
{html_end(1)}"""


def filters_bar():
    return """
            <div class="filters-bar" id="filters-bar">
                <div class="filter-group">
                    <label for="filter-prezzo-min">Prezzo min</label>
                    <input type="number" id="filter-prezzo-min" placeholder="€ min">
                </div>
                <div class="filter-group">
                    <label for="filter-prezzo-max">Prezzo max</label>
                    <input type="number" id="filter-prezzo-max" placeholder="€ max">
                </div>
                <div class="filter-group">
                    <label for="filter-mq-min">Mq min</label>
                    <input type="number" id="filter-mq-min" placeholder="mq">
                </div>
                <div class="filter-group">
                    <label for="filter-camere">Camere</label>
                    <select id="filter-camere">
                        <option value="">Tutte</option>
                        <option value="1">1+</option>
                        <option value="2">2+</option>
                        <option value="3">3+</option>
                        <option value="4">4+</option>
                    </select>
                </div>
                <button class="btn btn-small" id="filter-reset">Reset</button>
            </div>"""


# ─── JSON ────────────────────────────────────────────────────────

def build_json(data):
    items = []
    for tipo in ['vendite', 'affitti']:
        for cn, cd in data[tipo].items():
            for a in cd['annunci']:
                f = a['fields']
                cover = ''
                if a['images']:
                    cover = f"img/{a['tipo']}/{a['comune_slug']}/{a['slug']}/{a['images'][0].name}"
                items.append({
                    'titolo': a['titolo'],
                    'slug': a['slug'],
                    'tipo': a['tipo'],
                    'comune': cd['display_name'],
                    'comune_slug': a['comune_slug'],
                    'sottotitolo': f['sottotitolo'],
                    'prezzo': f['prezzo'],
                    'prezzo_num': parse_prezzo_num(f['prezzo']),
                    'mq': parse_int_field(f['mq']),
                    'camere': parse_int_field(f['camere']),
                    'indirizzo': f['indirizzo'],
                    'classe_energetica': f['classe_energetica'],
                    'url': f"{a['tipo']}/{a['comune_slug']}/{a['slug']}/index.html",
                    'cover': cover,
                })
    return json.dumps(items, ensure_ascii=False, indent=2)


# ─── Build principale ───────────────────────────────────────────

def build():
    print("🏗  Idea Immobiliare — Generazione sito...\n")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    data, errors = scan_annunci()

    total = sum(len(cd['annunci']) for t in data.values() for cd in t.values())
    zones = sum(len(t) for t in data.values())
    print(f"📊 {total} annunci in {zones} zone\n")

    # Assets
    assets_out = OUTPUT_DIR / "assets"
    if ASSETS_SRC.exists():
        shutil.copytree(ASSETS_SRC, assets_out)
    else:
        assets_out.mkdir(parents=True)
    print("  ✅ Assets copiati")

    # Immagini
    img_out = OUTPUT_DIR / "img"
    for tipo in ['vendite', 'affitti']:
        for cn, cd in data[tipo].items():
            if cd['copertina']:
                dest = img_out / tipo / cd['slug']
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cd['copertina'], dest / f"copertina{cd['copertina'].suffix}")
            for a in cd['annunci']:
                if a['images']:
                    dest = img_out / tipo / cd['slug'] / a['slug']
                    dest.mkdir(parents=True, exist_ok=True)
                    for im in a['images']:
                        shutil.copy2(im, dest / im.name)
    print("  ✅ Immagini copiate")

    # Homepage
    write_page(OUTPUT_DIR / "index.html", page_home(data))
    print("  ✅ Homepage")

    # Vendite & Affitti
    for tipo in ['vendite', 'affitti']:
        td = OUTPUT_DIR / tipo
        td.mkdir(parents=True, exist_ok=True)
        write_page(td / "index.html", page_tipo(tipo, data))

        for cn, cd in data[tipo].items():
            cd_dir = td / cd['slug']
            cd_dir.mkdir(parents=True, exist_ok=True)
            # Copia copertina anche qui per header background
            if cd['copertina']:
                shutil.copy2(cd['copertina'], cd_dir / f"copertina{cd['copertina'].suffix}")
            write_page(cd_dir / "index.html", page_comune(tipo, cn, cd, data))

            for a in cd['annunci']:
                ad = cd_dir / a['slug']
                ad.mkdir(parents=True, exist_ok=True)
                write_page(ad / "index.html", page_annuncio(a))

    print("  ✅ Pagine annunci")

    # Contatti
    cont_dir = OUTPUT_DIR / "contatti"
    cont_dir.mkdir(parents=True, exist_ok=True)
    write_page(cont_dir / "index.html", page_contatti())
    print("  ✅ Contatti")

    # JSON
    write_page(OUTPUT_DIR / "annunci.json", build_json(data))
    print("  ✅ annunci.json")

    # Errori
    if errors:
        err = f"Errori rilevati — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        err += "=" * 50 + "\n\n"
        for e in errors:
            err += f"⚠️  {e}\n"
        Path("_errori.txt").write_text(err, encoding='utf-8')
        print(f"\n⚠️  {len(errors)} problemi (vedi _errori.txt):")
        for e in errors:
            print(f"   • {e}")
    else:
        ef = Path("_errori.txt")
        if ef.exists():
            ef.unlink()

    print(f"\n🎉 Sito generato in '{OUTPUT_DIR}/' — {total} annunci!")


def write_page(path, content):
    path.write_text(content, encoding='utf-8')


if __name__ == "__main__":
    build()
