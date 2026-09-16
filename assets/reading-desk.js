/* Reading-desk selection, resizable columns and system-aware color preference. No dependencies. */
let readingDeskTheme = 'system';
const readingDeskSystemTheme = window.matchMedia('(prefers-color-scheme: dark)');
const readingDeskWide = window.matchMedia('(min-width: 1120px)');
let readingDeskSelectedId = '';
let readingDeskSplit = 47.5;
let readingDeskDetailCollapsed = false;
const READING_DESK_COLLAPSE_WIDTH = 220;

/** Resolve a saved preference, including invalid or missing storage values. */
function resolveReadingDeskTheme(preference, systemDark) {
  return preference === 'dark' || (preference !== 'light' && systemDark) ? 'dark' : 'light';
}

/** Apply before first paint; storage failure must not prevent manual switching. */
function applyReadingDeskTheme(preference) {
  readingDeskTheme = ['system', 'light', 'dark'].includes(preference) ? preference : 'system';
  document.documentElement.dataset.theme = resolveReadingDeskTheme(readingDeskTheme, readingDeskSystemTheme.matches);
  document.querySelectorAll('[data-theme-choice]').forEach(function(button) {
    button.setAttribute('aria-pressed', String(button.dataset.themeChoice === readingDeskTheme));
  });
}

try { readingDeskTheme = localStorage.getItem('loop-models-theme') || 'system'; } catch (_) { /* Private browsing may deny storage. */ }
applyReadingDeskTheme(readingDeskTheme);
readingDeskSystemTheme.addEventListener('change', function() { applyReadingDeskTheme(readingDeskTheme); });

/** Retain a visible selection, otherwise use the first displayed record. */
function chooseReadingDeskPaper(papers, selectedId) {
  return papers.find(function(paper) { return paper.id === selectedId; }) || papers[0] || null;
}

/** Build a best-effort alphaXiv image URL only from a validated arXiv identifier. */
function getReadingDeskThumbnailUrl(paper) {
  if (paper.entry_type === 'blog') return '';
  const links = paper.links || {};
  const match = String(links.arxiv || links.alphaxiv || '').match(/^https?:\/\/(?:www\.)?(?:arxiv\.org\/(?:abs|pdf)|alphaxiv\.org\/abs)\/(\d{4}\.\d{4,5})(v[1-9]\d*)?(?:\.pdf)?\/?(?:[?#].*)?$/)
    || String(paper.arxiv_id || paper.id || '').match(/^(\d{4}\.\d{4,5})(v[1-9]\d*)?$/);
  // ponytail: Unversioned records try v1; resolve alphaXiv version IDs if coverage needs it.
  return match ? 'https://thumbnails.assets.alphaxiv.org/' + match[1] + (match[2] || 'v1') + '.png' : '';
}

/** Reuse catalog renderers so tags, scope notes and every source stay available. */
function renderReadingDeskDetail(paper) {
  const content = document.getElementById('paper-detail-content');
  if (!paper) {
    content.innerHTML = '<header class="desk-detail-header"><div class="desk-detail-kicker">Reading desk</div><h2 id="paper-detail-title">No matching resources</h2></header><div class="desk-detail-body" tabindex="0" role="region" aria-label="Resource details"><p>Try a broader search or clear the active filters.</p></div>';
    return;
  }
  const primaryUrl = getPrimaryPaperUrl(paper);
  const thumbnailUrl = getReadingDeskThumbnailUrl(paper);
  const metricsHtml = renderMetricsHtml(paper);
  const tags = paper._tagEntries || [];
  const groups = ['mechanism', 'focus', 'domain'].map(function(group) {
    const entries = tags.filter(function(entry) { return entry.group === group; });
    return entries.length ? '<div class="desk-tag-group"><h4>' + escapeHtml(TAG_GROUP_LABELS[group]) + '</h4><div class="paper-tags">'
      + entries.map(function(entry) { return renderPaperTagHtml(entry, 'paper-tag-' + group); }).join('') + '</div></div>' : '';
  }).join('');
  content.innerHTML = '<header class="desk-detail-header"><div class="desk-detail-kicker">' + (paper.entry_type === 'blog' ? 'From the blogs' : 'From the collection') + '</div>'
    + (thumbnailUrl || metricsHtml ? '<div class="desk-detail-visual">' : '')
    + (thumbnailUrl ? '<a class="desk-card-preview desk-detail-preview" href="' + escapeHtml(primaryUrl || thumbnailUrl)
      + '" target="_blank" rel="noopener noreferrer" aria-label="Open paper: ' + escapeHtml(paper.title) + '">'
      + '<img src="' + thumbnailUrl + '" alt="" width="144" height="186" loading="eager" decoding="async" referrerpolicy="no-referrer" onerror="this.parentElement.remove()"></a>' : '')
    + metricsHtml + (thumbnailUrl || metricsHtml ? '</div>' : '')
    + '<h2 id="paper-detail-title">' + escapeHtml(paper.title) + '</h2>'
    + '<p class="desk-detail-authors">' + escapeHtml(paper._authorsText) + '</p>'
    + '<div class="desk-detail-meta"><span>' + escapeHtml(paper.venue) + '</span><time>' + escapeHtml(getPaperDisplayDate(paper)) + '</time>'
    + (paper.must_read ? '<span class="desk-must-read">Must read</span>' : '')
    + (paper.foundation ? '<span class="foundation-badge">Foundation</span>' : '') + renderCatalogFitBadgeHtml(paper) + '</div>'
    + '<div class="desk-primary-actions">'
    + (primaryUrl ? '<a class="desk-open-paper" href="' + escapeHtml(primaryUrl) + '" target="_blank" rel="noopener">Open ' + (paper.entry_type === 'blog' ? 'blog' : 'paper') + ' ↗</a>' : '')
    + '</div></header>'
    + '<div class="desk-detail-body" tabindex="0" role="region" aria-label="Resource details">'
    + '<section class="desk-detail-section"><h3>Summary</h3><p>' + escapeHtml(paper.desc || 'No summary is available yet. Follow the source for the full text.') + '</p>' + renderCatalogFitNoteHtml(paper) + '</section>'
    + '<section class="desk-detail-section"><h3>Classification</h3><p class="desk-category-label">' + escapeHtml(paper._categoryTrailLabel) + '</p>' + groups + '</section>'
    + '<section class="desk-detail-section" aria-labelledby="desk-sources-title"><h3 id="desk-sources-title">Sources</h3><div class="paper-links">' + renderPaperLinksHtml(paper, false) + '</div>'
    + (paper._addedDate ? '<p class="desk-added-date">Added to the collection ' + escapeHtml(paper._addedDate) + '</p>' : '') + '</section>'
    + '<section class="desk-detail-section desk-discussion" aria-labelledby="desk-discussion-title"><h3 id="desk-discussion-title">Discussion</h3>' + renderCommunityCommentsHtml(paper, true) + '</section></div>';
}

/** Update selection from real visible records, never from presentation text. */
function syncReadingDeskSelection(papers) {
  // Category order is the displayed order, which can differ from a global date sort.
  const firstCard = document.querySelector('.paper-card[data-id]');
  const firstId = firstCard ? firstCard.dataset.id : '';
  const retained = papers.some(function(paper) { return paper.id === readingDeskSelectedId; });
  const paper = chooseReadingDeskPaper(papers, retained ? readingDeskSelectedId : firstId);
  readingDeskSelectedId = paper ? paper.id : '';
  syncReadingDeskButtons();
  renderReadingDeskDetail(paper);
}

/** Keep selection and disclosure state consistent after every open or close path. */
function syncReadingDeskButtons() {
  const open = document.getElementById('paper-detail').open;
  document.querySelectorAll('.desk-paper-select').forEach(function(button) {
    const selected = button.dataset.paperId === readingDeskSelectedId;
    button.setAttribute('aria-pressed', String(selected));
    button.setAttribute('aria-expanded', String(selected && open));
    button.closest('.paper-card').classList.toggle('is-selected', selected);
  });
}

/** Keep a nonmodal desktop column; narrow screens use the native modal focus trap. */
function syncReadingDeskPanel() {
  const dialog = document.getElementById('paper-detail');
  if (!dialog) return;
  const layout = document.querySelector('.layout');
  const wideList = readingDeskWide.matches && !document.body.classList.contains('stats-mode')
    && !layout.classList.contains('table-view-active');
  const collapsed = wideList && readingDeskDetailCollapsed;
  const showColumn = wideList && !collapsed;
  layout.classList.toggle('desk-detail-collapsed', collapsed);
  document.getElementById('desk-show-details').hidden = !collapsed;
  if (showColumn && !dialog.open) dialog.show();
  if (!showColumn && dialog.open) dialog.close();
  document.getElementById('desk-divider').hidden = !showColumn;
  if (showColumn) setReadingDeskSplit(readingDeskSplit);
  syncReadingDeskButtons();
}

/** Desktop closing widens the unchanged cards; mobile retains native dialog focus return. */
function closeReadingDeskDetail() {
  if (readingDeskWide.matches) setReadingDeskDetailCollapsed(true);
  else document.getElementById('paper-detail').close();
}

/** Clicking the visible selection toggles it closed; other papers replace the detail. */
function selectReadingDeskPaper(paper) {
  const dialog = document.getElementById('paper-detail');
  if (dialog.open && paper.id === readingDeskSelectedId) {
    closeReadingDeskDetail();
    return;
  }
  readingDeskSelectedId = paper.id;
  renderReadingDeskDetail(paper);
  if (!readingDeskWide.matches) dialog.showModal();
  else if (readingDeskDetailCollapsed) setReadingDeskDetailCollapsed(false);
  syncReadingDeskButtons();
}

/** Keep the list readable and allow the detail pane to reach its collapse threshold. */
function clampReadingDeskSplit(percent, width) {
  const minimum = Math.min(50, 360 / Math.max(1, width) * 100);
  const maximum = 100 - Math.min(50, READING_DESK_COLLAPSE_WIDTH / Math.max(1, width) * 100);
  return Math.max(minimum, Math.min(maximum, Number.isFinite(percent) ? percent : 47.5));
}

/** Only explicit dragging or keyboard resizing can collapse the detail column. */
function shouldCollapseReadingDeskSplit(percent, width) {
  return Number.isFinite(percent) && width > 0 && percent >= 100 * (1 - READING_DESK_COLLAPSE_WIDTH / width);
}

/** Preserve the user's layout choice independently of Table, Stats and mobile dialogs. */
function setReadingDeskDetailCollapsed(collapsed) {
  readingDeskDetailCollapsed = collapsed;
  if (!collapsed) readingDeskSplit = 47.5;
  document.querySelector('.layout').classList.remove('is-resizing');
  syncReadingDeskPanel();
  if (collapsed) document.getElementById('desk-show-details').focus();
}

/** Set flexible grid tracks without overriding the tablet, Table or Stats layouts. */
function setReadingDeskSplit(percent, allowCollapse) {
  const layout = document.querySelector('.layout');
  const divider = document.getElementById('desk-divider');
  const width = layout.clientWidth - layout.querySelector('.sidebar').getBoundingClientRect().width - divider.offsetWidth;
  if (allowCollapse && shouldCollapseReadingDeskSplit(percent, width)) {
    setReadingDeskDetailCollapsed(true);
    return;
  }
  readingDeskSplit = clampReadingDeskSplit(percent, width);
  layout.style.setProperty('--desk-list-fr', readingDeskSplit + 'fr');
  layout.style.setProperty('--desk-detail-fr', (100 - readingDeskSplit) + 'fr');
  divider.setAttribute('aria-valuemin', clampReadingDeskSplit(0, width).toFixed(1));
  divider.setAttribute('aria-valuemax', '100');
  divider.setAttribute('aria-valuenow', readingDeskSplit.toFixed(1));
  divider.setAttribute('aria-valuetext', Math.round(readingDeskSplit) + '% paper list');
}

/** Keep navigation visible and reserve at least 360px for the neighboring content. */
function clampReadingDeskSidebarWidth(width, layoutWidth) {
  const maximum = Math.max(200, Math.min(420, layoutWidth - 360));
  return Math.max(200, Math.min(maximum, Number.isFinite(width) ? width : 236));
}

/** Resize navigation without collapsing either pane or overriding the mobile layout. */
function setReadingDeskSidebarWidth(width) {
  if (window.innerWidth <= 768) return;
  const layout = document.querySelector('.layout');
  const divider = document.getElementById('desk-sidebar-divider');
  const nextWidth = clampReadingDeskSidebarWidth(width, layout.clientWidth);
  document.body.style.setProperty('--desk-rail', nextWidth + 'px');
  divider.setAttribute('aria-valuemax', String(clampReadingDeskSidebarWidth(420, layout.clientWidth)));
  divider.setAttribute('aria-valuenow', String(Math.round(nextWidth)));
  divider.setAttribute('aria-valuetext', Math.round(nextWidth) + ' pixels navigation width');
  if (!document.getElementById('desk-divider').hidden) setReadingDeskSplit(readingDeskSplit);
}

/** Share native pointer capture and keyboard controls across both column boundaries. */
function initReadingDeskResize() {
  const divider = document.getElementById('desk-divider');
  const sidebarDivider = document.getElementById('desk-sidebar-divider');
  const layout = document.querySelector('.layout');
  const sidebar = document.getElementById('desk-sidebar');
  [divider, sidebarDivider].forEach(function(handle) {
    const isSidebar = handle === sidebarDivider;
    handle.addEventListener('pointerdown', function(event) {
      if (event.button !== 0) return;
      event.preventDefault();
      handle.focus();
      handle.setPointerCapture(event.pointerId);
      handle.classList.add('is-dragging');
      layout.classList.add('is-resizing');
    });
    handle.addEventListener('pointermove', function(event) {
      if (handle.hidden || !handle.hasPointerCapture(event.pointerId)) return;
      if (isSidebar) {
        setReadingDeskSidebarWidth(event.clientX - layout.getBoundingClientRect().left);
      } else {
        const main = document.getElementById('main').getBoundingClientRect();
        const width = main.width + document.getElementById('paper-detail').getBoundingClientRect().width;
        setReadingDeskSplit((event.clientX - main.left) / width * 100, true);
        if (handle.hidden) handle.releasePointerCapture(event.pointerId);
      }
    });
    handle.addEventListener('lostpointercapture', function() {
      handle.classList.remove('is-dragging');
      layout.classList.remove('is-resizing');
    });
    handle.addEventListener('keydown', function(event) {
      const current = isSidebar ? sidebar.getBoundingClientRect().width : readingDeskSplit;
      const step = isSidebar ? 16 : 2;
      const next = { ArrowLeft: current - step, ArrowRight: current + step, Home: 0, End: isSidebar ? 420 : 100 }[event.key];
      if (next === undefined) return;
      event.preventDefault();
      if (isSidebar) setReadingDeskSidebarWidth(next);
      else setReadingDeskSplit(next, true);
    });
    handle.addEventListener('dblclick', function() {
      if (isSidebar) {
        document.body.style.removeProperty('--desk-rail');
        setReadingDeskSidebarWidth(sidebar.getBoundingClientRect().width);
      } else setReadingDeskSplit(47.5);
    });
  });
  document.getElementById('desk-show-details').addEventListener('click', function() {
    setReadingDeskDetailCollapsed(false);
    divider.focus();
  });
  window.addEventListener('resize', function() {
    setReadingDeskSidebarWidth(sidebar.getBoundingClientRect().width);
  });
  setReadingDeskSidebarWidth(sidebar.getBoundingClientRect().width);
}

/** Bind once; native buttons supply keyboard activation and the dialog handles Escape. */
function initReadingDesk() {
  applyReadingDeskTheme(readingDeskTheme);
  document.querySelectorAll('[data-theme-choice]').forEach(function(button) {
    button.addEventListener('click', function() {
      applyReadingDeskTheme(button.dataset.themeChoice);
      try { localStorage.setItem('loop-models-theme', readingDeskTheme); } catch (_) { /* Switching still works without persistence. */ }
    });
  });
  document.getElementById('sections-container').addEventListener('click', function(event) {
    const card = event.target.closest('.paper-card');
    const tagToggle = event.target.closest('.paper-tag-overflow');
    if (card && tagToggle) {
      const expanded = card.classList.toggle('show-all-tags');
      tagToggle.setAttribute('aria-expanded', String(expanded));
      tagToggle.textContent = expanded ? 'Fewer tags' : '+' + tagToggle.dataset.extraTags + ' tags';
      return;
    }
    if (!card || (event.target.closest('a, button, summary') && !event.target.closest('.desk-paper-select'))) return;
    if (readingDeskDetailCollapsed && readingDeskWide.matches && !event.target.closest('.desk-paper-select')) return;
    const paper = ALL_RESOURCES.find(function(record) { return record.id === card.dataset.id; });
    if (!paper) return;
    selectReadingDeskPaper(paper);
  });
  document.getElementById('paper-detail').addEventListener('close', syncReadingDeskButtons);
  readingDeskWide.addEventListener('change', function() {
    document.getElementById('paper-detail').close();
    syncReadingDeskPanel();
  });
  initReadingDeskResize();
  syncReadingDeskPanel();
}
