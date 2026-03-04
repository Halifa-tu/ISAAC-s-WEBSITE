/* ═══════════════════════════════════════════════
   main.js — Shared utilities for public pages
═══════════════════════════════════════════════ */

// ── Active nav link ──────────────────────────────
function setActiveNav() {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link-item').forEach(a => {
    if (a.getAttribute('href') === page) a.classList.add('active');
  });
}

// ── Toast ────────────────────────────────────────
function toast(msg, duration = 3500) {
  let wrap = document.getElementById('toast-container');
  if (!wrap) { wrap = document.createElement('div'); wrap.id = 'toast-container'; document.body.appendChild(wrap); }
  const el = document.createElement('div');
  el.className = 'toast-msg';
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

// ── Mobile menu toggle ───────────────────────────
function initMobileMenu() {
  const btn = document.getElementById('mobile-toggle');
  const menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', () => {
    menu.style.display = menu.style.display === 'none' || !menu.style.display ? 'block' : 'none';
  });
}

// ── Footer inject ────────────────────────────────
function renderFooter() {
  const a = LM.getAgent();
  const el = document.getElementById('site-footer');
  if (!el) return;
  el.innerHTML = `
    <div class="container">
      <div class="row g-5 mb-2">
        <div class="col-lg-4">
          <div class="nav-brand d-block mb-3">
            <i class="bi bi-buildings me-2"></i>LandMark<span style="font-weight:400"> Realty</span>
          </div>
          <p style="color:var(--stone);font-size:0.88rem;line-height:1.8;margin-bottom:22px;">${a.bio || ''}</p>
          <div class="d-flex gap-3 flex-wrap">
            <a href="https://wa.me/${a.wa}" target="_blank" class="btn-wa py-2 px-4" style="font-size:0.85rem;">
              <i class="bi bi-whatsapp me-2"></i>WhatsApp
            </a>
            <a href="tel:${a.phone}" class="btn-outline-gold py-2 px-4" style="font-size:0.85rem;">
              <i class="bi bi-telephone me-2"></i>Call
            </a>
          </div>
        </div>
        <div class="col-6 col-lg-2">
          <h6 style="color:var(--cream);text-transform:uppercase;letter-spacing:0.12em;font-size:0.72rem;margin-bottom:16px;">Pages</h6>
          <a href="../index.html" class="footer-link">Home</a>
          <a href="../properties.html" class="footer-link">Properties</a>
          <a href="../about.html" class="footer-link">About</a>
          <a href="../services.html" class="footer-link">Services</a>
          <a href="../contact.html" class="footer-link">Contact</a>
        </div>
        <div class="col-6 col-lg-3">
          <h6 style="color:var(--cream);text-transform:uppercase;letter-spacing:0.12em;font-size:0.72rem;margin-bottom:16px;">Properties</h6>
          <a href="../properties.html?type=house" class="footer-link">🏠 Houses</a>
          <a href="../properties.html?type=room" class="footer-link">🛏 Rooms & Apartments</a>
          <a href="../properties.html?type=land" class="footer-link">🌿 Land for Sale</a>
          <a href="../request.html" class="footer-link">✏️ Request a Property</a>
        </div>
        <div class="col-lg-3">
          <h6 style="color:var(--cream);text-transform:uppercase;letter-spacing:0.12em;font-size:0.72rem;margin-bottom:16px;">Contact</h6>
          <div style="color:var(--stone);font-size:0.88rem;margin-bottom:8px;"><i class="bi bi-telephone me-2" style="color:var(--gold);"></i>${a.phone}</div>
          <div style="color:var(--stone);font-size:0.88rem;margin-bottom:8px;"><i class="bi bi-envelope me-2" style="color:var(--gold);"></i>${a.email}</div>
          <div style="color:var(--stone);font-size:0.88rem;"><i class="bi bi-geo-alt me-2" style="color:var(--gold);"></i>Accra, Ghana</div>
        </div>
      </div>
      <div class="footer-bottom">
        <span style="color:var(--stone);font-size:0.78rem;">© ${new Date().getFullYear()} LandMark Realty · ${a.name}. All rights reserved.</span>
        <span style="color:var(--stone);font-size:0.78rem;">Ghana Real Estate</span>
      </div>
    </div>`;
}

// ── Navbar inject ────────────────────────────────
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
        <a href="index.html" class="nav-brand"><i class="bi bi-buildings me-2"></i>LandMark<span style="font-weight:400"> Realty</span></a>
        <div class="d-none d-lg-flex align-items-center gap-1">
          ${links.map(l => `<a href="${l.href}" class="nav-link-item${l.href===activePage?' active':''}">${l.label}</a>`).join('')}
          <a href="request.html" class="nav-link-item ms-1"><i class="bi bi-pencil-square me-1"></i>Request</a>
        </div>
        <button id="mobile-toggle" style="background:none;border:none;color:var(--gold);font-size:1.5rem;cursor:pointer;padding:4px;" class="d-lg-none">
          <i class="bi bi-list"></i>
        </button>
      </div>
      <div id="mobile-menu" style="display:none;" class="pb-2 mt-2 border-top border-secondary pt-2">
        ${links.map(l => `<a href="${l.href}" class="nav-link-item d-block mb-1">${l.label}</a>`).join('')}
        <a href="request.html" class="nav-link-item d-block mb-1"><i class="bi bi-pencil-square me-1"></i>Request a Property</a>
      </div>
    </div>`;
  initMobileMenu();
}

// ── Property card HTML ────────────────────────────
function buildPropertyCard(l, onclick) {
  const imgHtml = l.images?.length
    ? `<img src="${l.images[0]}" alt="${l.title}" loading="lazy"/>
       <span style="position:absolute;bottom:10px;right:10px;background:rgba(0,0,0,0.55);color:#fff;padding:3px 10px;border-radius:100px;font-size:0.73rem;">
         <i class="bi bi-images me-1"></i>${l.images.length}
       </span>`
    : `<div class="prop-img-placeholder">${LM.typeIcon(l.type)}</div>`;

  const specs = l.type !== 'land'
    ? `<div class="prop-specs">
        ${l.bedrooms ? `<span><i class="bi bi-door-open me-1"></i>${l.bedrooms} Bed${l.bedrooms>1?'s':''}</span>` : ''}
        ${l.bathrooms ? `<span><i class="bi bi-droplet me-1"></i>${l.bathrooms} Bath${l.bathrooms>1?'s':''}</span>` : ''}
        ${l.size ? `<span><i class="bi bi-arrows-angle-expand me-1"></i>${l.size}</span>` : ''}
       </div>`
    : l.size ? `<div class="prop-specs"><span><i class="bi bi-arrows-angle-expand me-1"></i>${l.size}</span></div>` : '';

  return `
    <div class="col-md-6 col-lg-4">
      <div class="prop-card" onclick="${onclick}(${l.id})">
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

// ── Property Modal ────────────────────────────────
let _modalListing = null;
let _modalImgIdx  = 0;

function openModal(id) {
  const l = LM.getListing(id);
  if (!l) return;
  _modalListing = l;
  _modalImgIdx  = 0;

  const a = LM.getAgent();
  const msg = encodeURIComponent(`Hi, I'm interested in: ${l.title} (${l.price})`);

  // Carousel
  const carouselWrap = document.getElementById('modal-carousel');
  if (l.images?.length) {
    document.getElementById('modal-img').src = l.images[0];
    document.getElementById('modal-img').style.display = '';
    document.getElementById('modal-placeholder').style.display = 'none';
    document.getElementById('modal-dots').innerHTML = l.images.length > 1
      ? l.images.map((_,i) => `<div class="dot${i===0?' active':''}" onclick="modalSetImg(${i})"></div>`).join('')
      : '';
  } else {
    document.getElementById('modal-img').style.display = 'none';
    document.getElementById('modal-placeholder').style.display = 'flex';
    document.getElementById('modal-placeholder').textContent = LM.typeIcon(l.type);
    document.getElementById('modal-dots').innerHTML = '';
  }

  document.getElementById('modal-type-badge').innerHTML = `<span class="type-badge ${LM.typeBadgeClass(l.type)}" style="position:static;display:inline-block;">${l.type}</span>`;
  document.getElementById('modal-featured').innerHTML = l.featured ? '<span class="featured-badge" style="position:static;display:inline-block;">★ Featured</span>' : '';
  document.getElementById('modal-price').textContent = l.price;
  document.getElementById('modal-title').textContent = l.title;
  document.getElementById('modal-location').innerHTML = `<i class="bi bi-geo-alt me-1"></i>${l.location}`;
  document.getElementById('modal-desc').textContent = l.desc;

  // Specs
  let specs = '';
  if (l.bedrooms)  specs += `<div class="text-center"><div style="font-size:1.4rem;">🛏</div><div style="color:var(--cream);font-weight:700;">${l.bedrooms}</div><div style="color:var(--stone);font-size:0.72rem;margin-top:2px;">Bedrooms</div></div>`;
  if (l.bathrooms) specs += `<div class="text-center"><div style="font-size:1.4rem;">🚿</div><div style="color:var(--cream);font-weight:700;">${l.bathrooms}</div><div style="color:var(--stone);font-size:0.72rem;margin-top:2px;">Bathrooms</div></div>`;
  if (l.size)      specs += `<div class="text-center"><div style="font-size:1.4rem;">📐</div><div style="color:var(--cream);font-weight:700;">${l.size}</div><div style="color:var(--stone);font-size:0.72rem;margin-top:2px;">Size</div></div>`;
  const specsEl = document.getElementById('modal-specs');
  specsEl.innerHTML = specs;
  specsEl.style.display = specs ? 'flex' : 'none';

  document.getElementById('modal-actions').innerHTML = `
    <a href="tel:${a.phone}" class="btn-gold flex-fill text-center"><i class="bi bi-telephone me-2"></i>Call</a>
    <a href="sms:${a.phone}&body=${msg}" class="btn-outline-gold flex-fill text-center"><i class="bi bi-chat-text me-2"></i>SMS</a>
    <a href="https://wa.me/${a.wa}?text=${msg}" target="_blank" class="btn-wa flex-fill text-center"><i class="bi bi-whatsapp me-2"></i>WhatsApp</a>`;

  document.getElementById('prop-modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function modalSetImg(idx) {
  if (!_modalListing?.images?.length) return;
  _modalImgIdx = idx;
  document.getElementById('modal-img').src = _modalListing.images[idx];
  document.querySelectorAll('#modal-dots .dot').forEach((d,i) => d.classList.toggle('active', i===idx));
}

function closeModal() {
  document.getElementById('prop-modal').classList.remove('open');
  document.body.style.overflow = '';
}

// ── Modal HTML (inject once per page) ─────────────
function injectModal() {
  if (document.getElementById('prop-modal')) return;
  document.body.insertAdjacentHTML('beforeend', `
    <div class="modal-overlay" id="prop-modal" onclick="closeModal()">
      <div class="modal-box" onclick="event.stopPropagation()">
        <div class="modal-carousel-wrap" id="modal-carousel">
          <img id="modal-img" src="" alt="" style="display:none;"/>
          <div id="modal-placeholder" class="modal-carousel-placeholder" style="display:none;font-size:6rem;"></div>
          <div class="carousel-dots" id="modal-dots"></div>
          <div style="position:absolute;top:14px;left:14px;display:flex;gap:8px;align-items:center;" id="modal-type-badge"></div>
          <div style="position:absolute;top:14px;right:60px;" id="modal-featured"></div>
          <button class="modal-close" onclick="closeModal()">✕</button>
        </div>
        <div class="modal-body-pad">
          <div style="font-family:'Cormorant Garamond',serif;color:var(--gold);font-size:1.6rem;font-weight:700;margin-bottom:4px;" id="modal-price"></div>
          <h2 style="font-family:'Cormorant Garamond',serif;color:var(--cream);font-size:1.65rem;margin-bottom:8px;" id="modal-title"></h2>
          <p style="color:#5A8FA0;font-size:0.88rem;margin-bottom:14px;" id="modal-location"></p>
          <p style="color:var(--stone-light);line-height:1.8;font-size:0.93rem;margin-bottom:22px;" id="modal-desc"></p>
          <div id="modal-specs" style="background:var(--ink-700);border-radius:12px;padding:16px 20px;gap:28px;margin-bottom:24px;flex-wrap:wrap;"></div>
          <div class="d-flex gap-3 flex-wrap" id="modal-actions"></div>
        </div>
      </div>
    </div>`);
}

// ── Init on load ─────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  injectModal();
});
