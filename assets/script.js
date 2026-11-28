/* ===== Idea Immobiliare — Script (from artifact, adapted for static pages) ===== */

(function () {
  'use strict';

  /* ── Navbar scroll behaviour ── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    let lastY = 0;
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y > 40) {
        navbar.classList.add('is-opaque');
        if (y > lastY && y > 120) navbar.classList.add('is-hidden');
        else navbar.classList.remove('is-hidden');
      } else {
        navbar.classList.remove('is-opaque', 'is-hidden');
      }
      lastY = y;
    }, { passive: true });
  }

  /* ── Mobile menu toggle ── */
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const spans = toggle.querySelectorAll('span');
      if (navLinks.classList.contains('open')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px,5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(5px,-5px)';
      } else {
        spans[0].style.transform = '';
        spans[1].style.opacity = '';
        spans[2].style.transform = '';
      }
    });
    navLinks.querySelectorAll('a').forEach(a =>
      a.addEventListener('click', () => {
        navLinks.classList.remove('open');
        toggle.querySelectorAll('span').forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
      })
    );
  }

  /* ── Active nav link ── */
  const currentPath = window.location.pathname.replace(/\/+$/, '') || '/';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (!href) return;
    const linkPath = href.replace(/\/+$/, '') || '/';
    if (currentPath === linkPath || (linkPath !== '/' && currentPath.startsWith(linkPath))) {
      a.classList.add('active');
    }
  });

  /* ── Scroll reveal (IntersectionObserver) ── */
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.1 });
    reveals.forEach(el => obs.observe(el));
  }

  /* ── Gallery (property detail page) ── */
  const mainImg = document.querySelector('.property-hero .main-image');
  const thumbs = document.querySelectorAll('.gallery-thumbs img');
  if (mainImg && thumbs.length) {
    thumbs.forEach(t => {
      t.addEventListener('click', () => {
        mainImg.style.opacity = '0';
        setTimeout(() => {
          mainImg.src = t.dataset.full || t.src;
          mainImg.style.opacity = '1';
          thumbs.forEach(tt => tt.classList.remove('active'));
          t.classList.add('active');
        }, 300);
      });
    });
  }

  /* ── Lightbox ── */
  let lightbox = document.querySelector('.lightbox');
  const galleryImgs = document.querySelectorAll('.gallery-grid img');
  let lbImages = [];
  let lbIndex = 0;

  if (galleryImgs.length) {
    if (!lightbox) {
      lightbox = document.createElement('div');
      lightbox.className = 'lightbox';
      lightbox.innerHTML = `
        <button class="lightbox-close" aria-label="Chiudi">&times;</button>
        <button class="lightbox-prev" aria-label="Precedente">&#8249;</button>
        <img src="" alt="Foto ingrandita">
        <button class="lightbox-next" aria-label="Successiva">&#8250;</button>
      `;
      document.body.appendChild(lightbox);
    }

    const lbImg = lightbox.querySelector('img');
    const lbClose = lightbox.querySelector('.lightbox-close');
    const lbPrev = lightbox.querySelector('.lightbox-prev');
    const lbNext = lightbox.querySelector('.lightbox-next');

    lbImages = Array.from(galleryImgs).map(i => i.dataset.full || i.src);

    galleryImgs.forEach((img, i) => {
      img.addEventListener('click', () => {
        lbIndex = i;
        lbImg.src = lbImages[lbIndex];
        lightbox.classList.add('active');
        document.body.style.overflow = 'hidden';
      });
    });

    const closeLb = () => {
      lightbox.classList.remove('active');
      document.body.style.overflow = '';
    };

    lbClose.addEventListener('click', closeLb);
    lightbox.addEventListener('click', (e) => { if (e.target === lightbox) closeLb(); });

    lbPrev.addEventListener('click', (e) => {
      e.stopPropagation();
      lbIndex = (lbIndex - 1 + lbImages.length) % lbImages.length;
      lbImg.src = lbImages[lbIndex];
    });
    lbNext.addEventListener('click', (e) => {
      e.stopPropagation();
      lbIndex = (lbIndex + 1) % lbImages.length;
      lbImg.src = lbImages[lbIndex];
    });

    document.addEventListener('keydown', (e) => {
      if (!lightbox.classList.contains('active')) return;
      if (e.key === 'Escape') closeLb();
      if (e.key === 'ArrowLeft') { lbIndex = (lbIndex - 1 + lbImages.length) % lbImages.length; lbImg.src = lbImages[lbIndex]; }
      if (e.key === 'ArrowRight') { lbIndex = (lbIndex + 1) % lbImages.length; lbImg.src = lbImages[lbIndex]; }
    });
  }

  /* ── Filters (listing pages) ── */
  const filtersBar = document.querySelector('.filters-bar');
  if (filtersBar) {
    const cards = Array.from(document.querySelectorAll('.card-immobile'));
    const selTipo = filtersBar.querySelector('[data-filter="tipo"]');
    const selPrezzo = filtersBar.querySelector('[data-filter="prezzo"]');
    const selLocali = filtersBar.querySelector('[data-filter="locali"]');
    const selSort = filtersBar.querySelector('[data-filter="sort"]');
    const countEl = filtersBar.querySelector('.filter-count');

    function applyFilters() {
      let visible = 0;
      cards.forEach(card => {
        let show = true;
        if (selTipo && selTipo.value) {
          show = show && card.dataset.tipo === selTipo.value;
        }
        if (selPrezzo && selPrezzo.value) {
          const price = parseFloat(card.dataset.prezzo || '0');
          const [min, max] = selPrezzo.value.split('-').map(Number);
          if (max) show = show && price >= min && price <= max;
          else show = show && price >= min;
        }
        if (selLocali && selLocali.value) {
          const locali = parseInt(card.dataset.locali || '0');
          const val = parseInt(selLocali.value);
          if (val === 5) show = show && locali >= 5;
          else show = show && locali === val;
        }
        card.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      if (countEl) countEl.textContent = visible + ' risultat' + (visible === 1 ? 'o' : 'i');

      /* Sort */
      if (selSort && selSort.value) {
        const grid = document.querySelector('.immobili-grid');
        if (grid) {
          const sorted = cards.filter(c => c.style.display !== 'none');
          sorted.sort((a, b) => {
            const pa = parseFloat(a.dataset.prezzo || '0');
            const pb = parseFloat(b.dataset.prezzo || '0');
            if (selSort.value === 'prezzo-asc') return pa - pb;
            if (selSort.value === 'prezzo-desc') return pb - pa;
            return 0;
          });
          sorted.forEach(c => grid.appendChild(c));
        }
      }
    }

    [selTipo, selPrezzo, selLocali, selSort].forEach(sel => {
      if (sel) sel.addEventListener('change', applyFilters);
    });
  }

  /* ── Leaflet Maps ── */
  function makeMap(containerId, lat, lng, zoom, options) {
    if (!window.L || !document.getElementById(containerId)) return null;
    const map = L.map(containerId, { scrollWheelZoom: false }).setView([lat, lng], zoom || 15);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OSM &amp; CartoDB',
      maxZoom: 19
    }).addTo(map);
    return map;
  }

  /* Office map (contatti page) */
  const officeMapEl = document.getElementById('map-ufficio');
  if (officeMapEl) {
    const lat = parseFloat(officeMapEl.dataset.lat || '44.4211');
    const lng = parseFloat(officeMapEl.dataset.lng || '11.9108');
    const map = makeMap('map-ufficio', lat, lng, 16);
    if (map) {
      const icon = L.divIcon({
        className: '',
        html: '<div class="marker-pin"></div>',
        iconSize: [32, 42],
        iconAnchor: [16, 42]
      });
      L.marker([lat, lng], { icon: icon }).addTo(map);
    }
  }

  /* Property zone map */
  const zoneMapEl = document.getElementById('map-zona');
  if (zoneMapEl) {
    const lat = parseFloat(zoneMapEl.dataset.lat || '44.42');
    const lng = parseFloat(zoneMapEl.dataset.lng || '11.91');
    const zone = zoneMapEl.dataset.zona || '';
    const map = makeMap('map-zona', lat, lng, 14);
    if (map) {
      L.circle([lat, lng], {
        radius: 800,
        color: 'var(--accent, #1E4E8C)',
        fillColor: 'var(--accent, #1E4E8C)',
        fillOpacity: 0.08,
        weight: 1.5
      }).addTo(map);
      if (zone) {
        const pill = L.divIcon({
          className: '',
          html: '<div class="zone-pill">' + zone + '</div>',
          iconSize: [100, 28],
          iconAnchor: [50, 14]
        });
        L.marker([lat, lng], { icon: pill }).addTo(map);
      }
    }
  }

  /* ── Contact form → mailto ── */
  document.querySelectorAll('form[data-mailto]').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const to = form.dataset.mailto;
      const nome = form.querySelector('[name="nome"]');
      const email = form.querySelector('[name="email"]');
      const tel = form.querySelector('[name="telefono"]');
      const msg = form.querySelector('[name="messaggio"]');
      const oggetto = form.querySelector('[name="oggetto"]');
      const subject = oggetto ? oggetto.value : 'Richiesta informazioni';
      let body = '';
      if (nome) body += 'Nome: ' + nome.value + '\n';
      if (email) body += 'Email: ' + email.value + '\n';
      if (tel) body += 'Telefono: ' + tel.value + '\n';
      if (msg) body += '\n' + msg.value;
      window.location.href = 'mailto:' + to +
        '?subject=' + encodeURIComponent(subject) +
        '&body=' + encodeURIComponent(body);
    });
  });

  /* ── Card image hover swap ── */
  // Handled via CSS (.card-media .primary/.alt opacity swap on hover)
  // No JS needed for the basic effect

})();
