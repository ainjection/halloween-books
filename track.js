/* Halloween Shelf visit counter. Same Supabase table as The Gentle Bookshop (book = 'halloween-shelf').
   No cookies, no personal data: page, event kind, referrer host, and the time. */
(function () {
  var ENDPOINT = 'https://kvjientfaaewancbmzrr.supabase.co/rest/v1/events';
  var KEY = 'sb_publishable_AISP1QyNwBJJFrKDZNjIAA_zYdxWnFQ';
  var book = 'halloween-shelf';
  /* Social in-app browsers strip document.referrer, so a ?src= tag on posted links is the reliable signal. */
  var ref = '';
  try {
    var q = new URLSearchParams(location.search);
    var src = q.get('src') || q.get('utm_source');
    if (src) { try { sessionStorage.setItem('hs_src', src); } catch (e) {} }
    else { try { src = sessionStorage.getItem('hs_src'); } catch (e) {} }
    ref = src || (document.referrer ? new URL(document.referrer).host : '');
  } catch (e) {}
  function send(kind, extra) {
    var body = JSON.stringify({ book: book, kind: kind, ref: ref, target: extra || null, ua_mobile: /Mobi|Android/i.test(navigator.userAgent) });
    try {
      fetch(ENDPOINT, { method: 'POST', keepalive: true, mode: 'cors',
        headers: { 'Content-Type': 'application/json', 'apikey': KEY, 'Authorization': 'Bearer ' + KEY, 'Prefer': 'return=minimal' },
        body: body });
    } catch (e) {}
  }
  send('view');
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a');
    if (!a || !a.href) return;
    if (a.href.indexOf('amazon.') !== -1) {
      send('amazon', (a.href.match(/\/dp\/([A-Z0-9]{10})/) || [])[1] || null);
    } else if (a.dataset.free) {
      /* full free downloads are logged as lookinside with a free: target */
      send('lookinside', 'free:' + a.dataset.free);
    } else if (/\/pages\/.+-sample-pages\.pdf/.test(a.href)) {
      /* sample-page downloads are logged as lookinside with a sample: target */
      send('lookinside', 'sample:' + a.href.split('/pages/')[1].replace('-sample-pages.pdf', ''));
    }
  }, true);
})();
