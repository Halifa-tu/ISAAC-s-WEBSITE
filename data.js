/* ═══════════════════════════════════════════════
   data.js — Shared data layer (localStorage)
   Used by all public pages AND admin
═══════════════════════════════════════════════ */

const LM = (() => {

  // ── Storage helpers ──────────────────────────
  function load(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
    catch { return fallback; }
  }
  function save(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch {}
  }

  // ── Default Data ─────────────────────────────
  const DEFAULT_LISTINGS = [
    {
      id: 1, type: 'house',
      title: 'Elegant 4-Bedroom Family Home',
      desc: 'Spacious modern home with open-plan living, fitted kitchen, master en-suite, and a large garden. Located in a quiet estate close to schools and shopping centres. 24/7 water and electricity with standby generator.',
      price: 'GHS 850,000', location: 'East Legon, Accra',
      bedrooms: 4, bathrooms: 3, size: '320 sqm',
      images: [], featured: true, status: 'available',
      created: Date.now() - 3600000
    },
    {
      id: 2, type: 'room',
      title: 'Self-Contained Studio Room',
      desc: 'Neat tiled self-contained room with private bath, kitchenette, and 24/7 water and electricity. Ideal for working professionals. Secure compound with parking.',
      price: 'GHS 1,200/mo', location: 'Tema, Community 25',
      bedrooms: 1, bathrooms: 1, size: '45 sqm',
      images: [], featured: false, status: 'available',
      created: Date.now() - 7200000
    },
    {
      id: 3, type: 'land',
      title: 'Prime Residential Plot',
      desc: 'Fenced, gated 1-acre residential land with all documents intact — Indenture, Site Plan, and Land Search Report available. Perfect for housing development in a fast-growing neighbourhood.',
      price: 'GHS 400,000', location: 'Kasoa, Central Region',
      bedrooms: null, bathrooms: null, size: '1 acre',
      images: [], featured: true, status: 'available',
      created: Date.now() - 10800000
    },
    {
      id: 4, type: 'house',
      title: 'Modern 3-Bedroom Townhouse',
      desc: 'Newly built 3-bedroom townhouse with solar panels, CCTV security system, covered parking for 2 cars, and a beautiful garden. Estate living in the heart of Tema.',
      price: 'GHS 620,000', location: 'Tema, Community 18',
      bedrooms: 3, bathrooms: 2, size: '220 sqm',
      images: [], featured: false, status: 'available',
      created: Date.now() - 14400000
    },
    {
      id: 5, type: 'room',
      title: 'Furnished 2-Bedroom Apartment',
      desc: 'Fully furnished 2-bedroom apartment ideal for expats or corporate rental. Includes air conditioning, washing machine, DSTV subscription, and high-speed WiFi.',
      price: 'GHS 4,500/mo', location: 'Airport Residential, Accra',
      bedrooms: 2, bathrooms: 2, size: '90 sqm',
      images: [], featured: true, status: 'available',
      created: Date.now() - 18000000
    },
    {
      id: 6, type: 'land',
      title: 'Commercial Land — Main Road',
      desc: 'Half-acre commercial land on a major road with high daily traffic. Ideal for shops, offices, hotel, or mixed-use development. All documents available for inspection.',
      price: 'GHS 750,000', location: 'Spintex Road, Accra',
      bedrooms: null, bathrooms: null, size: '0.5 acre',
      images: [], featured: false, status: 'available',
      created: Date.now() - 21600000
    }
  ];

  const DEFAULT_AGENT = {
    name:  'Kwame Asante',
    phone: '+233 244 000 000',
    email: 'kwame@landmarkrealty.gh',
    wa:    '233244000000',
    bio:   'With over 10 years of experience in Ghana\'s real estate market, I have helped hundreds of families, professionals, and investors find the right property at the right price. My approach is simple: honesty, speed, and genuine care for every client.'
  };

  // ── Public API ───────────────────────────────
  return {
    // Listings
    getListings()         { return load('lm_listings', DEFAULT_LISTINGS); },
    saveListings(arr)     { save('lm_listings', arr); },
    getListing(id)        { return this.getListings().find(l => l.id == id); },

    addListing(l) {
      const arr = this.getListings();
      arr.unshift({ ...l, id: Date.now(), created: Date.now() });
      this.saveListings(arr);
    },
    updateListing(l) {
      const arr = this.getListings().map(x => x.id == l.id ? l : x);
      this.saveListings(arr);
    },
    deleteListing(id) {
      this.saveListings(this.getListings().filter(l => l.id != id));
    },

    // Requests
    getRequests()     { return load('lm_requests', []); },
    addRequest(r)     { const a = this.getRequests(); a.unshift({ ...r, id: Date.now(), created: Date.now() }); save('lm_requests', a); },
    deleteRequest(id) { save('lm_requests', this.getRequests().filter(r => r.id != id)); },

    // Messages
    getMessages()     { return load('lm_messages', []); },
    addMessage(m)     { const a = this.getMessages(); a.unshift({ ...m, id: Date.now(), created: Date.now() }); save('lm_messages', a); },
    deleteMessage(id) { save('lm_messages', this.getMessages().filter(m => m.id != id)); },

    // Agent Info
    getAgent()        { return load('lm_agent', DEFAULT_AGENT); },
    saveAgent(info)   { save('lm_agent', info); },

    // Auth
    isLoggedIn()      { return sessionStorage.getItem('lm_admin') === '1'; },
    login(u, p)       {
      if (u === 'admin' && p === 'agent2024') { sessionStorage.setItem('lm_admin', '1'); return true; }
      return false;
    },
    logout()          { sessionStorage.removeItem('lm_admin'); },

    // Helpers
    typeIcon(t)  { return { house: '🏠', room: '🛏️', land: '🌿' }[t] || '🏠'; },
    typeBadgeClass(t) { return { house: 'type-house', room: 'type-room', land: 'type-land' }[t] || ''; },
    priceNum(str) { const n = parseInt(str.replace(/[^0-9]/g, '')); return isNaN(n) ? 0 : n; },
    fmt(ts) { return new Date(ts).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'numeric' }); },
    fmtFull(ts) { return new Date(ts).toLocaleString('en-GB', { day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }); },
  };
})();
