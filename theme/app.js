(function () {
  var root = document.documentElement;
  var base = root.dataset.base || '';
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  // ---- theme and list/grid toggles ----
  function labels() {
    document.querySelectorAll('[data-label="theme"]').forEach(function (el) {
      el.textContent = root.dataset.theme === 'dark' ? 'Light mode' : 'Dark mode';
    });
    document.querySelectorAll('[data-label="view"]').forEach(function (el) {
      el.textContent = root.dataset.view === 'list' ? 'Grid view' : 'List view';
    });
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-action]');
    if (!btn) return;
    e.preventDefault();
    if (btn.dataset.action === 'theme') {
      var dark = root.dataset.theme !== 'dark';
      if (dark) root.dataset.theme = 'dark'; else delete root.dataset.theme;
      store.set('wiki-theme', dark ? 'dark' : 'light');
    } else if (btn.dataset.action === 'view') {
      var list = root.dataset.view !== 'list';
      if (list) root.dataset.view = 'list'; else delete root.dataset.view;
      store.set('wiki-view', list ? 'list' : 'grid');
    }
    labels();
  });
  labels();

  // ---- relative dates ----
  var rtf = window.Intl && Intl.RelativeTimeFormat ? new Intl.RelativeTimeFormat('en', { numeric: 'auto' }) : null;
  var units = [['year', 31536000], ['month', 2592000], ['week', 604800], ['day', 86400], ['hour', 3600], ['minute', 60]];
  document.querySelectorAll('time[data-rel]').forEach(function (el) {
    var then = new Date(el.getAttribute('datetime'));
    if (!rtf || isNaN(then)) return;
    var secs = (then - Date.now()) / 1000;
    el.title = then.toLocaleString();
    for (var i = 0; i < units.length; i++) {
      if (Math.abs(secs) >= units[i][1]) {
        el.textContent = rtf.format(Math.round(secs / units[i][1]), units[i][0]);
        return;
      }
    }
    el.textContent = 'just now';
  });

  // ---- search page ----
  var results = document.getElementById('search-results');
  if (!results) return;
  var input = document.getElementById('search-input');
  var count = document.getElementById('search-count');
  var index = null;

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function highlight(text, tokens) {
    var out = escapeHtml(text);
    tokens.forEach(function (t) {
      var safe = escapeHtml(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      out = out.replace(new RegExp('(' + safe + ')(?![^<]*>)', 'gi'), '<mark>$1</mark>');
    });
    return out;
  }
  function run() {
    var q = input.value.trim().toLowerCase();
    var tokens = q.split(/\s+/).filter(Boolean);
    results.innerHTML = '';
    if (!tokens.length || !index) { count.textContent = tokens.length ? 'Loading...' : 'Type something to search.'; return; }
    var hits = [];
    index.forEach(function (item) {
      var title = item.title.toLowerCase(), text = (item.text || '').toLowerCase(), score = 0;
      for (var i = 0; i < tokens.length; i++) {
        var inTitle = title.indexOf(tokens[i]) !== -1, inText = text.indexOf(tokens[i]) !== -1;
        if (!inTitle && !inText) return;
        score += (inTitle ? 10 : 0) + (inText ? 1 : 0);
      }
      hits.push({ item: item, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    count.textContent = hits.length + (hits.length === 1 ? ' result' : ' results');
    results.innerHTML = hits.slice(0, 50).map(function (h) {
      var item = h.item, text = item.text || '';
      var at = text.toLowerCase().indexOf(tokens[0]);
      var start = Math.max(0, at - 70);
      var snippet = (start > 0 ? '... ' : '') + text.slice(start, start + 200) + (text.length > start + 200 ? ' ...' : '');
      return '<a class="row kind-' + item.kind + '" href="' + escapeHtml(item.url) + '"><div>' +
        '<h4>' + highlight(item.title, tokens) + '</h4>' +
        (item.where ? '<small>' + escapeHtml(item.where) + '</small>' : '') +
        '<p>' + highlight(snippet, tokens) + '</p></div></a>';
    }).join('');
  }

  input.value = new URLSearchParams(location.search).get('q') || '';
  input.addEventListener('input', run);
  input.form.addEventListener('submit', function (e) {
    e.preventDefault();
    history.replaceState(null, '', '?q=' + encodeURIComponent(input.value));
    run();
  });
  run();
  fetch(base + '/search.json').then(function (r) { return r.json(); }).then(function (data) {
    index = data;
    run();
  }).catch(function () { count.textContent = 'Could not load the search index.'; });
  input.focus();
})();
