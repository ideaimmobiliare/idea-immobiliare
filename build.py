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

CONTACT_ADDRESS = "Via A. Acquacalda 6/6, Lugo (RA)"
CONTACT_EMAIL = "ideaimmobiliare2@gmail.com"
CONTACT_PHONE = "0545 27367"
CONTACT_CELL = "335 812 7996"
CONTACT_HOURS_1 = "Lun — Ven  8:00–12:30 / 15:00–18:30"
CONTACT_HOURS_2 = "Sab  8:00–12:00"
CONTACT_PIVA = "01040800391"

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
        'bagni': '',
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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
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
    <div class="nav-inner">
        <a href="{p}index.html" class="nav-brand">
            <img src="{p}assets/logo.jpg" alt="Idea Immobiliare" class="nav-brand-logo">
            <span class="nav-brand-text">Idea Immobiliare</span>
        </a>
        <div class="nav-links" id="nav-links">
            <a href="{p}index.html" data-route="home"{ac('home')}>Home</a>
            <a href="{p}vendite/index.html" data-route="vendite"{ac('vendite')}>Vendite</a>
            <a href="{p}affitti/index.html" data-route="affitti"{ac('affitti')}>Affitti</a>
            <a href="{p}contatti/index.html" data-route="info"{ac('contatti')}>Info</a>
        </div>
        <button class="nav-toggle" id="nav-toggle" aria-label="Menu">
            <span></span><span></span><span></span>
        </button>
    </div>
</nav>"""


def html_footer(depth=0):
    p = rel(depth)
    year = datetime.now().year

    return f"""
<footer class="footer">
    <div class="footer-inner">
        <div class="footer-col">
            <a href="{p}index.html" class="footer-brand">Idea Immobiliare</a>
            <p class="footer-desc">{CHI_SIAMO[:120]}…</p>
        </div>
        <div class="footer-col">
            <h4>Pagine</h4>
            <ul>
                <li><a href="{p}index.html">Home</a></li>
                <li><a href="{p}vendite/index.html">Vendite</a></li>
                <li><a href="{p}affitti/index.html">Affitti</a></li>
                <li><a href="{p}contatti/index.html">Info &amp; Contatti</a></li>
            </ul>
        </div>
        <div class="footer-col">
            <h4>Contatti</h4>
            <p>{CONTACT_ADDRESS}</p>
            <p>Tel. <a href="tel:{CONTACT_PHONE.replace(' ', '')}">{CONTACT_PHONE}</a></p>
            <p>Cell. <a href="tel:{CONTACT_CELL.replace(' ', '')}">{CONTACT_CELL}</a></p>
            <p><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>
            <p class="footer-hours">{CONTACT_HOURS_1}<br>{CONTACT_HOURS_2}</p>
            <p class="footer-piva">P.IVA {CONTACT_PIVA}</p>
        </div>
    </div>
    <div class="footer-bottom">
        <p>&copy; {year} Idea Immobiliare {SITE_OWNER}. Tutti i diritti riservati.</p>
    </div>
</footer>"""


def html_end(depth=0):
    p = rel(depth)
    return f"""
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="{p}assets/script.js"></script>
</body>
</html>"""


# ─── Card annuncio (stile artefatto) ────────────────────────────

def annuncio_card(a, depth=0):
    p = rel(depth)
    f = a['fields']
    link = f"{p}{a['tipo']}/{a['comune_slug']}/{a['slug']}/index.html"
    badge_text = "Vendita" if a['tipo'] == 'vendite' else "Affitto"
    comune_display = display_name(a['comune'])

    # Primary image
    if a['images']:
        img_base = f"{p}img/{a['tipo']}/{a['comune_slug']}/{a['slug']}/"
        primary_src = img_base + a['images'][0].name
        primary_img = f'<img class="primary" src="{primary_src}" alt="{a["titolo"]}" loading="lazy">'
        # Alt image for hover swap
        if len(a['images']) > 1:
            alt_src = img_base + a['images'][1].name
            alt_img = f'<img class="alt" src="{alt_src}" alt="{a["titolo"]}" loading="lazy">'
        else:
            alt_img = ''
    else:
        primary_img = '<div class="card-noimg">Nessuna foto</div>'
        alt_img = ''

    # Price
    prezzo = f['prezzo'] if f['prezzo'] else ''

    # Meta info
    meta_parts = []
    if f['mq']:
        meta_parts.append(f'{f["mq"]} mq')
    if f['camere']:
        meta_parts.append(f'{f["camere"]} cam.')
    if f.get('bagni'):
        meta_parts.append(f'{f["bagni"]} bagn{"o" if f["bagni"] == "1" else "i"}')
    if f['classe_energetica']:
        meta_parts.append(f'Classe {f["classe_energetica"]}')
    meta_html = ' · '.join(meta_parts)

    return f"""
    <a href="{link}" class="card-immobile"
       data-prezzo="{parse_prezzo_num(f['prezzo']) or ''}"
       data-mq="{parse_int_field(f['mq']) or ''}"
       data-camere="{parse_int_field(f['camere']) or ''}">
        <div class="card-media">
            <span class="card-badge">{badge_text}</span>
            {primary_img}
            {alt_img}
        </div>
        <div class="card-body">
            <span class="card-zone">{comune_display}</span>
            <h3 class="card-title">{a['titolo']}</h3>
            <span class="card-price">{prezzo}</span>
            <span class="card-meta">{meta_html}</span>
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

    # In evidenza section
    evidenza = ''
    if cards:
        evidenza = f"""
    <section class="section reveal">
        <div class="section-inner">
            <h2 class="section-label">In evidenza</h2>
            <div class="immobili-grid">{cards}
            </div>
        </div>
    </section>"""

    # Zone cards (comuni) for vendite
    zone_cards = ''
    comuni_items = []
    for tipo in ['vendite', 'affitti']:
        for cn, cd in sorted(data[tipo].items()):
            # avoid duplicates
            if cd['display_name'] not in [c['name'] for c in comuni_items]:
                n_v = len(data['vendite'].get(cn, {}).get('annunci', []) if cn in data['vendite'] else [])
                n_a = len(data['affitti'].get(cn, {}).get('annunci', []) if cn in data['affitti'] else [])
                # Count from both
                total = 0
                for t in ['vendite', 'affitti']:
                    if cn in data[t]:
                        total += len(data[t][cn]['annunci'])
                comuni_items.append({
                    'name': cd['display_name'],
                    'slug': cd['slug'],
                    'count': total,
                })

    if comuni_items:
        zone_html = ''
        for c in comuni_items:
            zone_html += f"""
            <a href="vendite/{c['slug']}/index.html" class="comune-card reveal">
                <span class="comune-name">{c['name']}</span>
                <span class="comune-sub">Bassa Romagna</span>
                <span class="comune-count">{c['count']} annunc{'io' if c['count'] == 1 else 'i'}</span>
                <span class="comune-arrow">&rarr;</span>
            </a>"""

        zone_cards = f"""
    <section class="section reveal">
        <div class="section-inner">
            <h2 class="section-label">Zone</h2>
            <div class="comuni-grid">{zone_html}
            </div>
        </div>
    </section>"""

    # CTA section
    cta = f"""
    <section class="cta-section reveal">
        <div class="section-inner">
            <h2>Cerchi casa in Romagna?</h2>
            <p>Contattaci per una consulenza gratuita e senza impegno.</p>
            <a href="contatti/index.html" class="btn btn-accent">Contattaci</a>
        </div>
    </section>"""

    return f"""{html_head("Home", 0)}
<body>
{html_nav(0, 'home')}

    <section class="hero">
        <div class="hero-inner">
            <img src="assets/logo.jpg" alt="Idea Immobiliare" class="hero-logo">
            <h1>{SITE_TITLE}</h1>
            <p class="hero-sub">{SITE_OWNER}</p>
            <p class="hero-tagline">{SITE_TAGLINE}</p>
            <div class="hero-actions">
                <a href="vendite/index.html" class="btn btn-accent">Vendite</a>
                <a href="affitti/index.html" class="btn btn-outline">Affitti</a>
            </div>
        </div>
    </section>
{evidenza}
{zone_cards}
{cta}

{html_footer(0)}
{html_end(0)}"""


def page_tipo(tipo, data):
    label = "Vendite" if tipo == "vendite" else "Affitti"
    scopo_label = "in vendita" if tipo == "vendite" else "in affitto"

    # Comuni cards
    comuni_cards = ''
    for cn, cd in sorted(data[tipo].items()):
        n = len(cd['annunci'])
        comuni_cards += f"""
            <a href="{cd['slug']}/index.html" class="comune-card reveal">
                <span class="comune-name">{cd['display_name']}</span>
                <span class="comune-sub">Bassa Romagna</span>
                <span class="comune-count">{n} annunc{'io' if n == 1 else 'i'}</span>
                <span class="comune-arrow">&rarr;</span>
            </a>"""

    total = sum(len(cd['annunci']) for cd in data[tipo].values())

    return f"""{html_head(label, 1)}
<body>
{html_nav(1, tipo)}

    <section class="page-intro reveal">
        <div class="section-inner">
            <h1>{label}</h1>
            <p>{total} immobil{'e' if total == 1 else 'i'} {scopo_label} nella Bassa Romagna.</p>
        </div>
    </section>

    <section class="section reveal">
        <div class="section-inner">
            <div class="comuni-grid">{comuni_cards}
            </div>
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

    filters = filters_bar() if annunci else ''
    empty = '' if annunci else '<p class="no-results">Nessun annuncio per questa zona.</p>'

    return f"""{html_head(f"{dn} — {label}", 2)}
<body>
{html_nav(2, tipo)}

    <section class="page-intro reveal">
        <div class="section-inner">
            <nav class="breadcrumb">
                <a href="../../index.html">Home</a>
                <span class="sep">/</span>
                <a href="../index.html">{label}</a>
                <span class="sep">/</span>
                <span>{dn}</span>
            </nav>
            <h1>{dn}</h1>
            <p>{n} annunc{'io' if n == 1 else 'i'} disponibil{'e' if n == 1 else 'i'}.</p>
        </div>
    </section>

    <section class="section">
        <div class="section-inner">
            {filters}
            <div class="immobili-grid" id="annunci-grid">{cards}
            </div>
            {empty}
        </div>
    </section>

{html_footer(2)}
{html_end(2)}"""


def page_annuncio(a):
    f = a['fields']
    tipo_label = "Vendite" if a['tipo'] == 'vendite' else "Affitti"
    comune_dn = display_name(a['comune'])
    p = rel(3)

    # Gallery images
    gallery_imgs = ''
    thumb_imgs = ''
    all_gallery = ''
    for i, img in enumerate(a['images']):
        src = f"{p}img/{a['tipo']}/{a['comune_slug']}/{a['slug']}/{img.name}"
        act = ' active' if i == 0 else ''
        gallery_imgs += f'            <div class="gallery-slide{act}" data-index="{i}"><img src="{src}" alt="{a["titolo"]} — Foto {i+1}"></div>\n'
        thumb_imgs += f'            <button class="gallery-thumb{act}" data-index="{i}"><img src="{src}" alt="Miniatura {i+1}"></button>\n'
        all_gallery += f'        <div class="gallery-grid-item"><img src="{src}" alt="{a["titolo"]} — Foto {i+1}" loading="lazy"></div>\n'

    nav_btns = ''
    if len(a['images']) > 1:
        nav_btns = """
            <button class="gallery-prev">&lsaquo;</button>
            <button class="gallery-next">&rsaquo;</button>"""

    # Data grid items
    data_items = ''
    if f['mq']:
        data_items += f'                <div class="data-item"><span class="data-label">Superficie</span><span class="data-value">{f["mq"]} mq</span></div>\n'
    if f['camere']:
        data_items += f'                <div class="data-item"><span class="data-label">Camere</span><span class="data-value">{f["camere"]}</span></div>\n'
    if f.get('bagni'):
        data_items += f'                <div class="data-item"><span class="data-label">Bagni</span><span class="data-value">{f["bagni"]}</span></div>\n'
    if f['classe_energetica']:
        data_items += f'                <div class="data-item"><span class="data-label">Classe energetica</span><span class="data-value">{f["classe_energetica"]}</span></div>\n'
    tipo_label_badge = "Vendita" if a['tipo'] == 'vendite' else "Affitto"
    data_items += f'                <div class="data-item"><span class="data-label">Tipo</span><span class="data-value">{tipo_label_badge}</span></div>\n'

    # Description
    desc = ''
    if f['descrizione']:
        paras = [pp.strip() for pp in f['descrizione'].split('\n') if pp.strip()]
        desc_body = '\n'.join(f'                <p>{pp}</p>' for pp in paras)
        desc = f"""
            <div class="description">
                <h3>Descrizione</h3>
{desc_body}
            </div>"""

    # Gallery grid (all photos)
    gallery_grid = ''
    if len(a['images']) > 1:
        gallery_grid = f"""
            <div class="gallery-grid">
                <h3>Tutte le foto</h3>
{all_gallery}            </div>"""

    # Map section
    map_section = ''
    if f['indirizzo'] or comune_dn:
        zone_name = comune_dn
        map_section = f"""
            <div class="map-section" id="property-map" data-zone="{zone_name}" data-address="{f['indirizzo']}">
                <h3>Posizione</h3>
                <div class="map-container" id="detail-map"></div>
            </div>"""

    # Contact form
    email_subject = f"Informazioni: {a['titolo']}"
    contact_form = f"""
            <div class="contact-form-section">
                <h3>Richiedi informazioni</h3>
                <form class="form-card" id="contact-form"
                      data-email="{CONTACT_EMAIL}"
                      data-subject="{email_subject}">
                    <input type="text" name="nome" placeholder="Il tuo nome" required>
                    <input type="email" name="email" placeholder="La tua email" required>
                    <input type="tel" name="telefono" placeholder="Telefono (opzionale)">
                    <textarea name="messaggio" rows="4" placeholder="Messaggio" required></textarea>
                    <button type="submit" class="btn btn-accent">Invia richiesta</button>
                </form>
            </div>"""

    # Ref code
    ref_code = a['slug'].upper()[:8]

    return f"""{html_head(a['titolo'], 3)}
<body>
{html_nav(3, a['tipo'])}

    <section class="property-page">
        <div class="section-inner">
            <nav class="breadcrumb">
                <a href="{p}index.html">Home</a>
                <span class="sep">/</span>
                <a href="{p}{a['tipo']}/index.html">{tipo_label}</a>
                <span class="sep">/</span>
                <a href="{p}{a['tipo']}/{a['comune_slug']}/index.html">{comune_dn}</a>
                <span class="sep">/</span>
                <span>{a['titolo']}</span>
            </nav>

            <div class="property-hero">
                <div class="gallery" id="gallery">
                    <div class="gallery-main">
{gallery_imgs}{nav_btns}
                        <span class="gallery-counter" id="gallery-counter"></span>
                    </div>
                    <div class="gallery-thumbs">
{thumb_imgs}                    </div>
                </div>

                <div class="property-info">
                    <span class="property-zone">{comune_dn}</span>
                    <h1 class="property-title">{a['titolo']}</h1>
                    <span class="property-price">{f['prezzo']}</span>
                    <span class="property-ref">Rif. {ref_code}</span>
                    <div class="property-actions">
                        <a href="tel:{CONTACT_PHONE.replace(' ', '')}" class="btn btn-accent">Chiama {CONTACT_PHONE}</a>
                        <a href="mailto:{CONTACT_EMAIL}?subject={email_subject}" class="btn btn-outline">Scrivi email</a>
                    </div>
                </div>
            </div>

            <div class="property-body">
                <div class="data-grid">
{data_items}                </div>
{desc}
{gallery_grid}
{map_section}
{contact_form}
            </div>
        </div>
    </section>

    <div class="lightbox" id="lightbox">
        <button class="lightbox-close">&times;</button>
        <button class="lightbox-prev">&lsaquo;</button>
        <button class="lightbox-next">&rsaquo;</button>
        <div class="lightbox-body">
            <img id="lightbox-img" src="" alt="">
        </div>
        <span class="lightbox-counter" id="lightbox-counter"></span>
    </div>

{html_footer(3)}
{html_end(3)}"""


def page_contatti():
    return f"""{html_head("Info e Contatti", 1)}
<body>
{html_nav(1, 'contatti')}

    <section class="hero hero-small">
        <div class="hero-inner">
            <h1>Info &amp; Contatti</h1>
            <p class="hero-tagline">Siamo a tua disposizione per qualsiasi informazione.</p>
        </div>
    </section>

    <section class="section reveal">
        <div class="section-inner">
            <div class="contact-grid">
                <div class="contact-info-col">
                    <h2>I nostri recapiti</h2>
                    <div class="contact-row">
                        <span class="contact-label">Indirizzo</span>
                        <span class="contact-value">{CONTACT_ADDRESS}</span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Telefono</span>
                        <span class="contact-value"><a href="tel:{CONTACT_PHONE.replace(' ', '')}">{CONTACT_PHONE}</a></span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Cellulare</span>
                        <span class="contact-value"><a href="tel:{CONTACT_CELL.replace(' ', '')}">{CONTACT_CELL}</a></span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Email</span>
                        <span class="contact-value"><a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">Orari</span>
                        <span class="contact-value">{CONTACT_HOURS_1}<br>{CONTACT_HOURS_2}</span>
                    </div>
                    <div class="contact-row">
                        <span class="contact-label">P.IVA</span>
                        <span class="contact-value">{CONTACT_PIVA}</span>
                    </div>
                </div>

                <div class="contact-form-col">
                    <h2>Scrivici</h2>
                    <form class="form-card" id="contact-form"
                          data-email="{CONTACT_EMAIL}"
                          data-subject="Contatto dal sito">
                        <input type="text" name="nome" placeholder="Il tuo nome" required>
                        <input type="email" name="email" placeholder="La tua email" required>
                        <input type="tel" name="telefono" placeholder="Telefono (opzionale)">
                        <textarea name="messaggio" rows="5" placeholder="Come possiamo aiutarti?" required></textarea>
                        <button type="submit" class="btn btn-accent">Invia messaggio</button>
                    </form>
                </div>
            </div>
        </div>
    </section>

    <section class="section reveal">
        <div class="section-inner">
            <h2 class="section-label">Dove siamo</h2>
            <div class="map-container" id="office-map"
                 data-address="{CONTACT_ADDRESS}"
                 data-lat="44.4213"
                 data-lng="11.9110"></div>
        </div>
    </section>

    <section class="section chi-siamo reveal">
        <div class="section-inner">
            <h2>Chi siamo</h2>
            <p>{CHI_SIAMO}</p>
        </div>
    </section>

{html_footer(1)}
{html_end(1)}"""


def filters_bar():
    return """
            <div class="filters-bar" id="filters-bar">
                <select id="filter-prezzo" class="filter-select">
                    <option value="">Prezzo</option>
                    <option value="0-100000">Fino a €100.000</option>
                    <option value="100000-200000">€100.000 — €200.000</option>
                    <option value="200000-300000">€200.000 — €300.000</option>
                    <option value="300000-99999999">Oltre €300.000</option>
                </select>
                <select id="filter-locali" class="filter-select">
                    <option value="">Locali</option>
                    <option value="1">1+</option>
                    <option value="2">2+</option>
                    <option value="3">3+</option>
                    <option value="4">4+</option>
                </select>
                <select id="filter-sort" class="filter-select">
                    <option value="">Ordina</option>
                    <option value="prezzo-asc">Prezzo crescente</option>
                    <option value="prezzo-desc">Prezzo decrescente</option>
                    <option value="recenti">Più recenti</option>
                </select>
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
