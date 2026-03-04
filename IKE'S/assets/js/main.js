/* ═══════════════════════════════════════════════
   main.js — Shared utilities for public pages
   Fixed: paths, full image gallery carousel
═══════════════════════════════════════════════ */

// ── Toast ────────────────────────────────────────
function toast(msg, duration = 3500) {
  let wrap = document.getElementById('toast-container');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = 'toast-container';
    document.body.appendChild(wrap);
  }
  const el = document.createElement('div');
  el.className = 'toast-msg';
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── Mobile menu ───────────────────────────────────
function initMobileMenu() {
  const btn  = document.getElementById('mobile-toggle');
  const menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', () => {
    const open = menu.style.display === 'block';
    menu.style.display = open ? 'none' : 'block';
    btn.querySelector('i').className = open ? 'bi bi-list' : 'bi bi-x';
  });
}

// ── Navbar ────────────────────────────────────────
function renderNavbar(activePage) {
  const el = document.getElementById('site-nav');
  if (!el) return;
  const links = [
    { href: 'index.html',      label: 'Home' },
    { href: 'properties.html', label: 'Properties' },
    { href: 'about.html',      label: 'About' },
    { href: 'services.html',   label: 'Services' },
    { href: 'contact.html',    label: 'Contact' },
  ];
  el.innerHTML = `
    <div class="container">
      <div class="d-flex align-items-center justify-content-between">
        <a href="index.html" class="nav-brand">
          <i class="bi bi-buildings me-2"></i>LandMark<span style="font-weight:400"> Realty</span>
        </a>
        <div class="d-none d-lg-flex align-items-center gap-1">
          ${links.map(l => `<a href="${l.href}" class="nav-link-item${l.href===activePage?' active':''}">${l.label}</a>`).join('')}
          <a href="request.html" class="nav-link-item ms-1" style="color:var(--gold) !important;">
            <i class="bi bi-pencil-square me-1"></i>Request Property
          </a>
        </div>
        <button id="mobile-toggle" style="background:none;border:none;color:var(--gold);font-size:1.5rem;cursor:pointer;padding:4px;line-height:1;" class="d-lg-none">
          <i class="bi bi-list"></i>
        </button>
      </div>
      <div id="mobile-menu" style="display:none;" class="pb-3 mt-2 pt-2" style="border-top:1px solid rgba(255,255,255,0.08);">
        ${links.map(l => `<a href="${l.href}" class="nav-link-item d-block mb-1${l.href===activePage?' active':''}">${l.label}</a>`).join('')}
        <a href="request.html" class="nav-link-item d-block mb-1" style="color:var(--gold) !important;">
          <i class="bi bi-pencil-square me-1"></i>Request a Property
        </a>
      </div>
    </div>`;
  initMobileMenu();
}

// ── Footer ────────────────────────────────────────
// All hrefs use root-relative paths (no ../) so they work on Vercel/GitHub Pages
function renderFooter() {
  const a  = LM.getAgent();
  const el = document.getElementById('site-footer');
  if (!el) return;
  el.innerHTML = `
    <div class="container">
      <div class="row g-5 mb-2">
        <div class="col-lg-4">
          <a href="index.html" class="nav-brand d-block mb-3" style="text-decoration:none;">
            <i class="bi bi-buildings me-2"></i>LandMark<span style="font-weight:400"> Realty</span>
          </a>
          <p style="color:var(--stone);font-size:0.88rem;line-height:1.8;margin-bottom:22px;">${a.bio || ''}</p>
          <div class="d-flex gap-3 flex-wrap">
            <a href="https://wa.me/${a.wa}" target="_blank" class="btn-wa" style="padding:9px 20px;font-size:0.85rem;">
              <i class="bi bi-whatsapp me-2"></i>WhatsApp
            </a>
            <a href="tel:${a.phone}" class="btn-outline-gold" style="padding:9px 20px;font-size:0.85rem;">
              <i class="bi bi-telephone me-2"></i>Call
            </a>
          </div>
        </div>
        <div class="col-6 col-lg-2">
          <h6 style="color:var(--cream);text-transform:uppercase;letter-spacing:0.12em;font-size:0.72rem;margin-bottom:16px;">Pages</h6>
          <a href="index.html"      class="footer-link">Home</a>
          <a href="properties.html" class="footer-link">Properties</a>
          <a href="about.html"      class="footer-link">About</a>
          <a href="services.html"   class="footer-link">Services</a>
          <a href="contact.html"    class="footer-link">Contact</a>
        </div>
        <div class="col-6 col-lg-3">
          <h6 style="color:var(--cream);text-transform:uppercase;letter-spacing:0.12em;font-size:0.72rem;margin-bottom:16px;">Properties</h6>
          <a href="properties.html?type=house" class="footer-link">🏠 Houses for Sale</a>
          <a href="properties.html?type=room"  class="footer-link">🛏 Rooms &amp; Apartments</a>
          <a href="properties.html?type=land"  class="footer-link">🌿 Land for Sale</a>
          <a href="request.html"               class="footer-link">✏️ Request a Property</a>
        </div>
        <div class="col-lg-3">
          <h6 style="color:var(--cream);text-transform:uppercase;letter-spacing:0.12em;font-size:0.72rem;margin-bottom:16px;">Contact</h6>
          <div style="color:var(--stone);font-size:0.88rem;margin-bottom:10px;">
            <i class="bi bi-telephone me-2" style="color:var(--gold);"></i>${a.phone}
          </div>
          <div style="color:var(--stone);font-size:0.88rem;margin-bottom:10px;">
            <i class="bi bi-envelope me-2" style="color:var(--gold);"></i>${a.email}
          </div>
          <div style="color:var(--stone);font-size:0.88rem;">
            <i class="bi bi-geo-alt me-2" style="color:var(--gold);"></i>Accra, Ghana
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span style="color:var(--stone);font-size:0.78rem;">
          © ${new Date().getFullYear()} LandMark Realty · ${a.name}. All rights reserved.
        </span>
        <span style="color:var(--stone);font-size:0.78rem;">Ghana Real Estate</span>
      </div>
    </div>`;
}

// ── Property Card ─────────────────────────────────
function buildPropertyCard(l, onclickFn) {
  const imgHtml = l.images?.length
    ? `<img src="${l.images[0]}" alt="${l.title}" loading="lazy"/>
       <span style="position:absolute;bottom:10px;right:10px;background:rgba(0,0,0,0.62);color:#fff;padding:3px 10px;border-radius:100px;font-size:0.72rem;display:flex;align-items:center;gap:4px;">
         <i class="bi bi-images"></i>&nbsp;${l.images.length} photo${l.images.length>1?'s':''}
       </span>`
    : `<div class="prop-img-placeholder">${LM.typeIcon(l.type)}</div>`;

  const specs = l.type !== 'land'
    ? `<div class="prop-specs">
        ${l.bedrooms  ? `<span><i class="bi bi-door-open me-1"></i>${l.bedrooms} Bed${l.bedrooms>1?'s':''}</span>` : ''}
        ${l.bathrooms ? `<span><i class="bi bi-droplet me-1"></i>${l.bathrooms} Bath${l.bathrooms>1?'s':''}</span>` : ''}
        ${l.size      ? `<span><i class="bi bi-arrows-angle-expand me-1"></i>${l.size}</span>` : ''}
      </div>`
    : l.size ? `<div class="prop-specs"><span><i class="bi bi-arrows-angle-expand me-1"></i>${l.size}</span></div>` : '';

  return `
    <div class="col-md-6 col-lg-4">
      <div class="prop-card" onclick="${onclickFn}(${l.id})">
        <div class="prop-img-wrap">
          ${imgHtml}
          <span class="type-badge ${LM.typeBadgeClass(l.type)}">${l.type.charAt(0).toUpperCase()+l.type.slice(1)}</span>
          ${l.featured ? '<span class="featured-badge">★ Featured</span>' : ''}
        </div>
        <div class="prop-body">
          <div class="prop-price">${l.price}</div>
          <div class="prop-title">${l.title}</div>
          <div class="prop-location"><i class="bi bi-geo-alt me-1" style="color:var(--gold);"></i>${l.location}</div>
          <div class="prop-desc">${l.desc}</div>
          ${specs}
        </div>
      </div>
    </div>`;
}

// ════════════════════════════════════════════════
//  PROPERTY MODAL — full scrollable image gallery
// ════════════════════════════════════════════════
let _ml  = null;  // current listing
let _mi  = 0;     // current image index
let _tsx = 0;     // touch start X

function openModal(id) {
  const l = LM.getListing(id);
  if (!l) return;
  _ml = l;
  _mi = 0;

  const a   = LM.getAgent();
  const msg = encodeURIComponent(`Hi, I'm interested in: ${l.title} (${l.price})`);

  _buildGallery();

  document.getElementById('m-price').textContent     = l.price;
  document.getElementById('m-title').textContent     = l.title;
  document.getElementById('m-location').innerHTML    = `<i class="bi bi-geo-alt me-1"></i>${l.location}`;
  document.getElementById('m-desc').textContent      = l.desc;

  let specs = '';
  if (l.bedrooms)  specs += `<div class="modal-spec"><div class="msi">🛏</div><div class="msv">${l.bedrooms}</div><div class="msl">Bedrooms</div></div>`;
  if (l.bathrooms) specs += `<div class="modal-spec"><div class="msi">🚿</div><div class="msv">${l.bathrooms}</div><div class="msl">Bathrooms</div></div>`;
  if (l.size)      specs += `<div class="modal-spec"><div class="msi">📐</div><div class="msv">${l.size}</div><div class="msl">Size</div></div>`;
  const specsEl = document.getElementById('m-specs');
  specsEl.innerHTML = specs;
  specsEl.style.display = specs ? 'flex' : 'none';

  document.getElementById('m-actions').innerHTML = `
    <a href="tel:${a.phone}" class="btn-gold flex-fill text-center" style="padding:12px 16px;">
      <i class="bi bi-telephone me-2"></i>Call
    </a>
    <a href="sms:${a.phone}&body=${msg}" class="btn-outline-gold flex-fill text-center" style="padding:10px 16px;">
      <i class="bi bi-chat-text me-2"></i>SMS
    </a>
    <a href="https://wa.me/${a.wa}?text=${msg}" target="_blank" class="btn-wa flex-fill text-center" style="padding:12px 16px;">
      <i class="bi bi-whatsapp me-2"></i>WhatsApp
    </a>`;

  document.getElementById('prop-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function _buildGallery() {
  const imgs = _ml.images || [];
  const wrap = document.getElementById('m-gallery');

  if (!imgs.length) {
    wrap.innerHTML = `
      <div class="gallery-empty">
        <div style="font-size:7rem;opacity:0.15;">${LM.typeIcon(_ml.type)}</div>
        <div style="color:var(--stone);font-size:0.85rem;margin-top:12px;">No photos uploaded</div>
      </div>
      <button class="modal-close" onclick="closeModal()">✕</button>`;
    return;
  }

  // Build thumbnails HTML
  const thumbsHtml = imgs.length > 1
    ? `<div class="gallery-thumbs" id="g-thumbs">
        ${imgs.map((src,i) => `
          <button class="g-thumb${i===0?' active':''}" onclick="modalGoTo(${i})" title="Photo ${i+1}">
            <img src="${src}" alt="Photo ${i+1}"/>
          </button>`).join('')}
       </div>`
    : '';

  wrap.innerHTML = `
    <div class="gallery-stage" id="g-stage">
      <!-- Main image -->
      <div class="gallery-img-wrap" id="g-imgwrap">
        <img id="g-img" src="${imgs[0]}" alt="Photo 1"/>
      </div>

      <!-- Prev / Next arrows -->
      ${imgs.length > 1 ? `
        <button class="g-arrow g-prev" onclick="modalPrev()" aria-label="Previous photo">
          <i class="bi bi-chevron-left"></i>
        </button>
        <button class="g-arrow g-next" onclick="modalNext()" aria-label="Next photo">
          <i class="bi bi-chevron-right"></i>
        </button>` : ''}

      <!-- Counter badge -->
      ${imgs.length > 1 ? `<div class="g-counter" id="g-counter">1 / ${imgs.length}</div>` : ''}

      <!-- Badges -->
      <div style="position:absolute;top:14px;left:14px;display:flex;gap:8px;flex-wrap:wrap;" id="m-type-badge">
        <span class="type-badge ${LM.typeBadgeClass(_ml.type)}" style="position:static;display:inline-block;">
          ${_ml.type.charAt(0).toUpperCase()+_ml.type.slice(1)}
        </span>
        ${_ml.featured ? '<span class="featured-badge" style="position:static;display:inline-block;">★ Featured</span>' : ''}
      </div>

      <!-- Close -->
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>

    <!-- Thumbnail strip -->
    ${thumbsHtml}`;

  // Touch / swipe support
  const stage = document.getElementById('g-stage');
  stage.addEventListener('touchstart', e => { _tsx = e.touches[0].clientX; }, { passive: true });
  stage.addEventListener('touchend',   e => {
    const dx = e.changedTouches[0].clientX - _tsx;
    if (Math.abs(dx) > 40) { dx < 0 ? modalNext() : modalPrev(); }
  }, { passive: true });

  _updateGallery();
}

function _updateGallery() {
  const imgs = _ml?.images || [];
  if (!imgs.length) return;

  // Main image
  const imgEl = document.getElementById('g-img');
  if (imgEl) {
    imgEl.src = imgs[_mi];
    imgEl.alt = `Photo ${_mi + 1}`;
  }

  // Counter
  const ctr = document.getElementById('g-counter');
  if (ctr) ctr.textContent = `${_mi + 1} / ${imgs.length}`;

  // Arrows opacity
  const prev = document.querySelector('.g-prev');
  const next = document.querySelector('.g-next');
  if (prev) prev.style.opacity = _mi === 0             ? '0.35' : '1';
  if (next) next.style.opacity = _mi === imgs.length-1 ? '0.35' : '1';

  // Thumbnails
  document.querySelectorAll('.g-thumb').forEach((t, i) => {
    t.classList.toggle('active', i === _mi);
    if (i === _mi) {
      t.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  });
}

function modalGoTo(idx) {
  const imgs = _ml?.images || [];
  _mi = Math.max(0, Math.min(idx, imgs.length - 1));
  _updateGallery();
}

function modalPrev() { modalGoTo(_mi - 1); }
function modalNext() { modalGoTo(_mi + 1); }

function closeModal() {
  document.getElementById('prop-modal')?.classList.remove('open');
  document.body.style.overflow = '';
}

// Keyboard nav
document.addEventListener('keydown', e => {
  if (!document.getElementById('prop-modal')?.classList.contains('open')) return;
  if (e.key === 'ArrowLeft')  { e.preventDefault(); modalPrev(); }
  if (e.key === 'ArrowRight') { e.preventDefault(); modalNext(); }
  if (e.key === 'Escape')     closeModal();
});

// ── Inject modal HTML once ────────────────────────
function injectModal() {
  if (document.getElementById('prop-modal')) return;
  document.body.insertAdjacentHTML('beforeend', `
    <div class="modal-overlay" id="prop-modal" onclick="closeModal()">
      <div class="modal-box" onclick="event.stopPropagation()">

        <!-- Gallery section (built dynamically) -->
        <div id="m-gallery"></div>

        <!-- Text body -->
        <div class="modal-body-pad">
          <div style="font-family:'Cormorant Garamond',serif;color:var(--gold);font-size:1.6rem;font-weight:700;margin-bottom:4px;" id="m-price"></div>
          <h2 style="font-family:'Cormorant Garamond',serif;color:var(--cream);font-size:1.6rem;font-weight:700;line-height:1.2;margin-bottom:8px;" id="m-title"></h2>
          <p style="color:#5A8FA0;font-size:0.88rem;margin-bottom:14px;display:flex;align-items:center;gap:4px;" id="m-location"></p>
          <p style="color:var(--stone-light);line-height:1.85;font-size:0.92rem;margin-bottom:22px;" id="m-desc"></p>
          <div id="m-specs" style="background:var(--ink-700);border-radius:12px;padding:16px 20px;gap:28px;margin-bottom:24px;flex-wrap:wrap;"></div>
          <div class="d-flex gap-3 flex-wrap" id="m-actions"></div>
        </div>

      </div>
    </div>`);
}

document.addEventListener('DOMContentLoaded', () => { injectModal(); });
