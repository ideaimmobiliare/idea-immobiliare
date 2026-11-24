/* ─── Idea Immobiliare — Script ──────────────────────────────── */

(function () {
  'use strict';

  // ─── Mobile Menu ────────────────────────────────────────────
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');

  if (toggle && links) {
    toggle.addEventListener('click', function () {
      toggle.classList.toggle('active');
      links.classList.toggle('active');
    });

    // Chiudi menu quando si clicca un link
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        toggle.classList.remove('active');
        links.classList.remove('active');
      });
    });
  }

  // ─── Search ─────────────────────────────────────────────────
  var searchInput = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');
  var annunciData = null;

  if (searchInput) {
    var base = searchInput.getAttribute('data-base') || '';

    searchInput.addEventListener('focus', function () {
      loadAnnunci();
    });

    searchInput.addEventListener('input', function () {
      var q = this.value.trim().toLowerCase();
      if (q.length < 2) {
        searchResults.classList.remove('active');
        return;
      }
      loadAnnunci(function () {
        var results = annunciData.filter(function (a) {
          return (
            a.titolo.toLowerCase().includes(q) ||
            a.comune.toLowerCase().includes(q) ||
            (a.sottotitolo && a.sottotitolo.toLowerCase().includes(q)) ||
            (a.indirizzo && a.indirizzo.toLowerCase().includes(q))
          );
        }).slice(0, 8);

        if (results.length === 0) {
          searchResults.innerHTML = '<div class="search-empty">Nessun risultato</div>';
        } else {
          searchResults.innerHTML = results.map(function (a) {
            var imgHtml = a.cover
              ? '<img src="' + base + a.cover + '" alt="">'
              : '';
            var tipoLabel = a.tipo === 'vendite' ? 'Vendita' : 'Affitto';
            return (
              '<a href="' + base + a.url + '" class="search-item">' +
              imgHtml +
              '<div class="search-item-info">' +
              '<div class="search-item-title">' + a.titolo + '</div>' +
              '<div class="search-item-meta">' + tipoLabel + ' — ' + a.comune +
              (a.prezzo ? ' — ' + a.prezzo : '') +
              '</div></div></a>'
            );
          }).join('');
        }
        searchResults.classList.add('active');
      });
    });

    // Chiudi dropdown se si clicca fuori
    document.addEventListener('click', function (e) {
      if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
        searchResults.classList.remove('active');
      }
    });
  }

  function loadAnnunci(cb) {
    if (annunciData) {
      if (cb) cb();
      return;
    }
    var base = '';
    if (searchInput) {
      base = searchInput.getAttribute('data-base') || '';
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', base + 'annunci.json');
    xhr.onload = function () {
      if (xhr.status === 200) {
        try {
          annunciData = JSON.parse(xhr.responseText);
        } catch (e) {
          annunciData = [];
        }
      } else {
        annunciData = [];
      }
      if (cb) cb();
    };
    xhr.onerror = function () {
      annunciData = [];
      if (cb) cb();
    };
    xhr.send();
  }

  // ─── Filters ────────────────────────────────────────────────
  var filtersBar = document.getElementById('filters-bar');
  var annunciGrid = document.getElementById('annunci-grid');

  if (filtersBar && annunciGrid) {
    var prezzoMin = document.getElementById('filter-prezzo-min');
    var prezzoMax = document.getElementById('filter-prezzo-max');
    var mqMin = document.getElementById('filter-mq-min');
    var camere = document.getElementById('filter-camere');
    var resetBtn = document.getElementById('filter-reset');

    function applyFilters() {
      var cards = annunciGrid.querySelectorAll('.annuncio-card');
      var pMin = prezzoMin ? parseInt(prezzoMin.value) || 0 : 0;
      var pMax = prezzoMax ? parseInt(prezzoMax.value) || Infinity : Infinity;
      var mMin = mqMin ? parseInt(mqMin.value) || 0 : 0;
      var cMin = camere ? parseInt(camere.value) || 0 : 0;

      var visibleCount = 0;

      cards.forEach(function (card) {
        var cp = parseInt(card.getAttribute('data-prezzo')) || 0;
        var cm = parseInt(card.getAttribute('data-mq')) || 0;
        var cc = parseInt(card.getAttribute('data-camere')) || 0;

        var show = true;
        if (pMin > 0 && cp > 0 && cp < pMin) show = false;
        if (pMax < Infinity && cp > 0 && cp > pMax) show = false;
        if (mMin > 0 && cm > 0 && cm < mMin) show = false;
        if (cMin > 0 && cc > 0 && cc < cMin) show = false;

        // Se non ha il dato, mostra comunque (non filtrare su dati mancanti)
        card.style.display = show ? '' : 'none';
        if (show) visibleCount++;
      });

      // Messaggio nessun risultato
      var noRes = annunciGrid.parentNode.querySelector('.no-results-filter');
      if (visibleCount === 0 && cards.length > 0) {
        if (!noRes) {
          noRes = document.createElement('p');
          noRes.className = 'no-results no-results-filter';
          noRes.textContent = 'Nessun annuncio corrisponde ai filtri selezionati.';
          annunciGrid.parentNode.appendChild(noRes);
        }
        noRes.style.display = '';
      } else if (noRes) {
        noRes.style.display = 'none';
      }
    }

    [prezzoMin, prezzoMax, mqMin, camere].forEach(function (el) {
      if (el) el.addEventListener('input', applyFilters);
    });

    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        if (prezzoMin) prezzoMin.value = '';
        if (prezzoMax) prezzoMax.value = '';
        if (mqMin) mqMin.value = '';
        if (camere) camere.value = '';
        applyFilters();
      });
    }
  }

  // ─── Gallery ────────────────────────────────────────────────
  var gallery = document.getElementById('gallery');
  var currentSlide = 0;
  var slides = [];
  var thumbButtons = [];

  if (gallery) {
    slides = gallery.querySelectorAll('.gallery-slide');
    thumbButtons = gallery.querySelectorAll('.gallery-thumb');
    var counter = document.getElementById('gallery-counter');

    if (slides.length > 0 && counter) {
      counter.textContent = '1 / ' + slides.length;
    }

    // Click sulla gallery principale apre lightbox
    var mainArea = gallery.querySelector('.gallery-main');
    if (mainArea) {
      mainArea.addEventListener('click', function (e) {
        if (e.target.closest('.gallery-prev') || e.target.closest('.gallery-next')) return;
        openLightbox(currentSlide);
      });
    }

    // Thumbnails
    thumbButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        goToSlide(parseInt(this.getAttribute('data-index')));
      });
    });
  }

  function goToSlide(index) {
    if (slides.length === 0) return;
    currentSlide = index;
    slides.forEach(function (s) { s.classList.remove('active'); });
    thumbButtons.forEach(function (t) { t.classList.remove('active'); });
    slides[currentSlide].classList.add('active');
    if (thumbButtons[currentSlide]) {
      thumbButtons[currentSlide].classList.add('active');
      thumbButtons[currentSlide].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
    var counter = document.getElementById('gallery-counter');
    if (counter) counter.textContent = (currentSlide + 1) + ' / ' + slides.length;
  }

  window.galleryPrev = function () {
    goToSlide(currentSlide > 0 ? currentSlide - 1 : slides.length - 1);
  };

  window.galleryNext = function () {
    goToSlide(currentSlide < slides.length - 1 ? currentSlide + 1 : 0);
  };

  // ─── Lightbox ───────────────────────────────────────────────
  var lightbox = document.getElementById('lightbox');
  var lightboxImg = document.getElementById('lightbox-img');
  var lightboxCounter = document.getElementById('lightbox-counter');
  var lightboxIndex = 0;
  var lightboxSources = [];

  function openLightbox(index) {
    if (!lightbox || slides.length === 0) return;

    lightboxSources = [];
    slides.forEach(function (s) {
      var img = s.querySelector('img');
      if (img) lightboxSources.push(img.src);
    });

    lightboxIndex = index;
    showLightboxImage();
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function showLightboxImage() {
    if (!lightboxImg || lightboxSources.length === 0) return;
    lightboxImg.src = lightboxSources[lightboxIndex];
    if (lightboxCounter) {
      lightboxCounter.textContent = (lightboxIndex + 1) + ' / ' + lightboxSources.length;
    }
  }

  window.closeLightbox = function () {
    if (!lightbox) return;
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
  };

  window.lightboxPrev = function () {
    lightboxIndex = lightboxIndex > 0 ? lightboxIndex - 1 : lightboxSources.length - 1;
    showLightboxImage();
  };

  window.lightboxNext = function () {
    lightboxIndex = lightboxIndex < lightboxSources.length - 1 ? lightboxIndex + 1 : 0;
    showLightboxImage();
  };

  // Keyboard
  document.addEventListener('keydown', function (e) {
    if (!lightbox || !lightbox.classList.contains('active')) return;
    if (e.key === 'Escape') window.closeLightbox();
    if (e.key === 'ArrowLeft') window.lightboxPrev();
    if (e.key === 'ArrowRight') window.lightboxNext();
  });

  // Click sfondo chiude lightbox
  if (lightbox) {
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox || e.target.classList.contains('lightbox-body')) {
        window.closeLightbox();
      }
    });
  }

  // ─── Maps (Leaflet + Nominatim) ─────────────────────────────
  function initMap(containerId, address) {
    var container = document.getElementById(containerId);
    if (!container || !address || typeof L === 'undefined') return;

    // Geocode con Nominatim
    var url = 'https://nominatim.openstreetmap.org/search?format=json&q=' +
      encodeURIComponent(address) + '&limit=1';

    var xhr = new XMLHttpRequest();
    xhr.open('GET', url);
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.onload = function () {
      if (xhr.status !== 200) return;
      var results;
      try {
        results = JSON.parse(xhr.responseText);
      } catch (e) { return; }

      if (results.length === 0) {
        container.innerHTML = '<p style="padding:20px;color:#6b7280;text-align:center;">Posizione non trovata sulla mappa</p>';
        return;
      }

      var lat = parseFloat(results[0].lat);
      var lon = parseFloat(results[0].lon);

      var map = L.map(container).setView([lat, lon], 15);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 18,
      }).addTo(map);

      L.marker([lat, lon]).addTo(map);
    };
    xhr.send();
  }

  // Init mappe presenti nella pagina
  var detailMap = document.getElementById('detail-map');
  if (detailMap) {
    initMap('detail-map', detailMap.getAttribute('data-address'));
  }

  var contactsMap = document.getElementById('contacts-map');
  if (contactsMap) {
    initMap('contacts-map', contactsMap.getAttribute('data-address'));
  }

  // ─── Keyboard gallery (senza lightbox) ──────────────────────
  document.addEventListener('keydown', function (e) {
    if (lightbox && lightbox.classList.contains('active')) return;
    if (!gallery) return;
    if (e.key === 'ArrowLeft') window.galleryPrev();
    if (e.key === 'ArrowRight') window.galleryNext();
  });

})();
