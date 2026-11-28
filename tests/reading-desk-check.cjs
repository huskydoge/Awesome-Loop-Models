/* Dependency-free regression check: node tests/reading-desk-check.cjs. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/reading-desk.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'assets/reading-desk.css'), 'utf8');

/** Boot the real script with the minimal browser surface needed before first paint. */
function boot(preference, dark, denyStorage = false) {
  const rootElement = { dataset: {} };
  const themeButton = { setAttribute(name, value) { this[name] = value; } };
  const media = { matches: dark, addEventListener() {} };
  const storage = {
    value: preference,
    getItem() { if (denyStorage) throw new Error('Denied'); return this.value; },
    setItem(key, value) { if (denyStorage) throw new Error('Denied'); this.value = value; },
  };
  const context = vm.createContext({
    window: { matchMedia: () => media },
    document: { documentElement: rootElement, getElementById: () => themeButton, querySelectorAll: () => [] },
    localStorage: storage,
  });
  vm.runInContext(source, context);
  return { context, rootElement, media, themeButton, storage };
}

for (const [preference, dark, expected] of [
  ['system', true, 'light'], ['system', false, 'light'], [null, true, 'light'],
  ['light', true, 'light'], ['dark', false, 'dark'], ['invalid', true, 'light'],
]) {
  assert.equal(boot(preference, dark).rootElement.dataset.theme, expected);
}
const denied = boot(null, true, true);
assert.equal(denied.rootElement.dataset.theme, 'light');
denied.context.toggleReadingDeskTheme();
assert.equal(denied.rootElement.dataset.theme, 'dark');
denied.context.toggleReadingDeskTheme();
assert.equal(denied.rootElement.dataset.theme, 'light');
const theme = boot('light', false);
theme.context.toggleReadingDeskTheme();
assert.equal(theme.rootElement.dataset.theme, 'dark');
assert.equal(theme.themeButton['aria-label'], 'Switch to light mode');
assert.equal(theme.storage.value, 'dark');
assert.equal(boot(theme.storage.value, false).rootElement.dataset.theme, 'dark');
theme.context.toggleReadingDeskTheme();
assert.equal(theme.rootElement.dataset.theme, 'light');
assert.equal(theme.themeButton.title, 'Switch to dark mode');
assert.equal(theme.storage.value, 'light');
assert.equal((html.match(/id="desk-theme-toggle"/g) || []).length, 1);
assert.doesNotMatch(html, /data-theme-choice/);
assert.doesNotMatch(source, /prefers-color-scheme/);
assert.match(css, /\.reading-desk \.research-prompt-launch-label \{[^}]*display: block;[^}]*white-space: normal;/);
assert.match(css, /\.desk-sidebar-bottom \{ margin-top: auto;/);
assert.match(html, /<div class="header-actions">[\s\S]*?<div class="desk-theme">[\s\S]*?id="desk-theme-toggle"[\s\S]*?<\/button>\s*<\/div>\s*<\/div>/);

const choose = denied.context.chooseReadingDeskPaper;
const records = [{ id: 'first' }, { id: 'second' }];
assert.equal(choose(records, 'second'), records[1]);
assert.equal(choose(records, 'filtered-out'), records[0]);
assert.equal(choose([], 'second'), null);
const toggling = boot(null, true);
const actions = [];
const dialog = {
  open: true,
  close() { this.open = false; actions.push('close-modal'); },
  showModal() { this.open = true; actions.push('open-modal'); },
};
toggling.context.document.getElementById = () => dialog;
toggling.context.renderReadingDeskDetail = paper => actions.push('render:' + paper.id);
toggling.context.setReadingDeskDetailCollapsed = collapsed => {
  vm.runInContext('readingDeskDetailCollapsed = ' + JSON.stringify(collapsed), toggling.context);
  dialog.open = !collapsed;
  actions.push(collapsed ? 'collapse' : 'expand');
};
toggling.context.selectReadingDeskPaper(records[0]);
toggling.context.selectReadingDeskPaper(records[0]);
assert.equal(dialog.open, false);
toggling.context.selectReadingDeskPaper(records[0]);
assert.equal(dialog.open, true);
toggling.context.selectReadingDeskPaper(records[1]);
assert.equal(dialog.open, true);
toggling.context.closeReadingDeskDetail();
assert.deepEqual(actions, ['render:first', 'collapse', 'render:first', 'expand', 'render:second', 'collapse']);
toggling.media.matches = false;
toggling.context.selectReadingDeskPaper(records[1]);
assert.equal(dialog.open, true);
toggling.context.closeReadingDeskDetail();
assert.equal(dialog.open, false);
assert.deepEqual(actions.slice(-3), ['render:second', 'open-modal', 'close-modal']);
const thumbnail = denied.context.getReadingDeskThumbnailUrl;
assert.equal(thumbnail({ id: '2301.13196' }), 'https://thumbnails.assets.alphaxiv.org/2301.13196v1.png');
assert.equal(thumbnail({ links: { arxiv: 'https://arxiv.org/pdf/2301.13196v2.pdf?download=1' } }), 'https://thumbnails.assets.alphaxiv.org/2301.13196v2.png');
assert.equal(thumbnail({ links: { alphaxiv: 'https://www.alphaxiv.org/abs/2301.13196v3' } }), 'https://thumbnails.assets.alphaxiv.org/2301.13196v3.png');
assert.equal(thumbnail({ arxiv_id: '1511.04491', id: 'custom-title' }), 'https://thumbnails.assets.alphaxiv.org/1511.04491v1.png');
assert.equal(thumbnail({ id: '2301.13196', entry_type: 'blog' }), '');
assert.equal(thumbnail({ links: { arxiv: 'https://arxiv.org.evil.example/abs/2301.13196' } }), '');
assert.equal(thumbnail({ id: '2301.13196" onerror="alert(1)' }), '');
assert.equal(thumbnail({ id: 'acl-paper' }), '');
const split = denied.context.clampReadingDeskSplit;
assert.equal(split(0, 1000), 36);
assert.equal(split(100, 1000), 78);
assert.equal(split(50, 1000), 50);
assert.equal(split(20, 720), 50);
assert.equal(split(80, 0), 50);
assert.equal(split(NaN, 1000), 47.5);
const collapse = denied.context.shouldCollapseReadingDeskSplit;
assert.equal(collapse(77.9, 1000), false);
assert.equal(collapse(78, 1000), true);
assert.equal(collapse(100, 1000), true);
assert.equal(collapse(75, 800), true);
assert.equal(collapse(NaN, 1000), false);
assert.equal(collapse(100, 0), false);
const sidebarWidth = denied.context.clampReadingDeskSidebarWidth;
assert.equal(sidebarWidth(-100, 1440), 200);
assert.equal(sidebarWidth(300, 1440), 300);
assert.equal(sidebarWidth(1000, 1440), 420);
assert.equal(sidebarWidth(420, 769), 409);
assert.equal(sidebarWidth(0, 0), 200);
assert.equal(sidebarWidth(NaN, 1440), 236);
const rail = boot(null, false);
const railAttributes = {};
const railStyles = {};
const detailDivider = { hidden: false };
const railLayout = { clientWidth: 1440 };
let splitUpdates = 0;
rail.context.window.innerWidth = 1440;
rail.context.document.querySelector = () => railLayout;
rail.context.document.body = { style: { setProperty(name, value) { railStyles[name] = value; } } };
rail.context.document.getElementById = id => id === 'desk-divider'
  ? detailDivider : { setAttribute(name, value) { railAttributes[name] = value; } };
rail.context.setReadingDeskSplit = (value, allowCollapse) => {
  assert.equal(allowCollapse, undefined);
  splitUpdates += 1;
};
rail.context.setReadingDeskSidebarWidth(-100);
assert.equal(railStyles['--desk-rail'], '200px');
assert.equal(railAttributes['aria-valuenow'], '200');
rail.context.setReadingDeskSidebarWidth(1000);
assert.equal(railStyles['--desk-rail'], '420px');
assert.equal(splitUpdates, 2);
assert.equal(vm.runInContext('readingDeskDetailCollapsed', rail.context), false);
detailDivider.hidden = true;
railLayout.clientWidth = 769;
rail.context.setReadingDeskSidebarWidth(420);
assert.equal(railStyles['--desk-rail'], '409px');
assert.equal(railAttributes['aria-valuemax'], '409');
assert.equal(splitUpdates, 2);
rail.context.window.innerWidth = 390;
rail.context.setReadingDeskSidebarWidth(200);
assert.equal(railStyles['--desk-rail'], '409px');
const card = html.slice(html.indexOf('// ── Render a single paper card'), html.indexOf('// ── State & Taxonomy'));
assert.match(card, /<article class="paper-card paper-row"/);
assert.match(card, /class="desk-paper-select"/);
assert.match(card, /formatCompactAuthors\(paper\)/);
assert.match(card, /paper-row-published/);
assert.match(card, /paper-row-added/);
assert.doesNotMatch(card + css, /desk-full-card|desk-paper-footer/);
assert.doesNotMatch(css, /\.desk-detail-collapsed #papers-panel/);
assert.match(css, /container: paper-list \/ inline-size/);
assert.match(css, /@container paper-list \(max-width: 640px\)/);
assert.match(css, /\.layout\.desk-detail-collapsed \{ grid-template-columns: var\(--desk-rail\) minmax\(0, 1fr\);/);
assert.match(html, /id="desk-show-details"[^>]+aria-controls="paper-detail"/);
assert.match(card, /class="paper-row-thumb"/);
assert.match(card, /loading="lazy" decoding="async" referrerpolicy="no-referrer"/);
assert.match(card, /onerror="this\.remove\(\)"/);
assert.match(html, /id="desk-divider"[^>]+role="separator"[^>]+aria-orientation="vertical"/);
assert.match(html, /id="desk-sidebar-divider"[^>]+role="separator"[^>]+aria-orientation="vertical"[^>]+aria-controls="desk-sidebar"/);
assert.match(css, /\.desk-divider\.desk-sidebar-divider \{[^}]*position: absolute;[^}]*left: calc\(var\(--desk-rail\) - 1px\);/);
assert.match(css.slice(css.indexOf('@media (max-width: 768px)')), /\.desk-sidebar-divider \{ display: none; \}/);
assert.match(html, /--font-body: Charter, Georgia/);
assert.doesNotMatch(html, /@media\s*\(prefers-color-scheme:\s*dark\)/);
assert.doesNotMatch(html, /category-disclaimer|desk-scope|About the classification/);
assert.doesNotMatch(html + source, /mechanism_tags|focus_tags|domain_tags|foundation|category/i, 'No trace of the retired taxonomy');
assert.doesNotMatch(html, /A field guide to recurrent depth|class="desk-subtitle"/);
assert.match(html, /<svg class="site-brand-mark"[^>]+aria-hidden="true">/);
assert.match(html, /<span class="site-brand-name">Awesome Loop Models<\/span>/);
assert.doesNotMatch(html, /id="sidebar-nav"|id="mobile-directory"/);
const filterPanel = html.slice(html.indexOf('<aside class="filter-sidebar"'), html.indexOf('<div class="top-level-panel" id="papers-panel"'));
assert.match(filterPanel, /<label for="section-filter"/);
assert.match(filterPanel, /id="section-filter" onchange="setSectionFilter\(this.value\)"/);
assert.match(filterPanel, /id="facet-filter-toggle"[\s\S]*Design axes/);
assert.match(css, /\.reading-desk \.site-brand-name \{[^}]*max-width: none;/);
const watch = html.slice(html.indexOf('<section class="desk-watch"'), html.indexOf('<div class="desk-sidebar-bottom">'));
assert.match(watch, /aria-label="Catalog watch"/);
assert.doesNotMatch(watch, /desk-watch-title|<h2/);
assert.match(watch, /id="daily-watch-countdown"/);
assert.doesNotMatch(watch, /daily-briefing|Today/, 'The briefing has its own page, not a sidebar box');
assert.doesNotMatch(watch, /<details|<summary/);
assert.doesNotMatch(html, /daily-briefing-notice|updateDailyBriefingNotice|hideStaleDailyBriefingNotice/);
assert.doesNotMatch(css, /daily-briefing-/);
assert.match(css, /\.reading-desk\.briefing-mode \.briefing-panel/);
assert.match(css, /\.briefing-page \{[^}]*max-width: 760px;/);
assert.match(css, /\.reading-desk \.daily-watch-countdown-meta \{[^}]*font-size: 12px;[^}]*line-height: 1\.6;/);
assert.match(css, /\.reading-desk \.daily-watch-countdown-value \{[^}]*font-size: 20px;[^}]*white-space: normal;/);
assert.ok(html.indexOf('assets/reading-desk.js') < html.indexOf('<style>'));
assert.match(html, /syncReadingDeskSelection\(filteredPapers\)/);
assert.match(html, /<dialog class="paper-detail"/);
assert.match(html, /class="desk-detail-close"[^>]+onclick="closeReadingDeskDetail\(\)"/);
assert.match(card, /aria-expanded="false"/);
assert.match(css, /\.desk-detail-close \{ display: grid;/);

// Use real card/link/metric/detail renderers; only unrelated taxonomy helpers are stubbed.
const detailContent = { innerHTML: '' };
const rendering = vm.createContext({
  Date,
  document: { getElementById: () => detailContent },
  LINK_CONFIG: {
    arxiv: { cls: 'link-arxiv', icon: '', label: 'arXiv' },
    github: { cls: 'link-github', icon: '', label: 'Code' },
  },
  SECTION_BY_ID: {
    'architecture/depth-control': { id: 'architecture/depth-control', number: '4.5', chapter: '4', title: 'Controlling recurrence depth' },
    'scaling/test-time': { id: 'scaling/test-time', number: '6.2', chapter: '6', title: 'Test-time scaling' },
  },
  ACTIVE_SECTION_FILTER: '',
  FACET_GROUPS: ['loop_topology', 'sharing', 'depth_control', 'claims', 'comparison'],
  formatSectionLabel: section => '§' + section.number + ' ' + section.title,
  getFacetDrilldownHref: (group, value) => '?' + group + '=' + encodeURIComponent(value) + '#papers',
  getFacetGroupLabel: group => ({ loop_topology: 'Loop topology', sharing: 'Sharing', depth_control: 'Depth control', claims: 'Claims', comparison: 'Looped-vs-untied comparison' })[group] || group,
  isFacetActive: () => false,
  getVisibleAxisEntries: paper => (paper._axisEntries || []).filter(entry => entry.value !== 'unspecified'),
  getReadingDeskThumbnailUrl: thumbnail,
  getPaperDisplayDate: paper => paper.published_date,
  renderCatalogFitBadgeHtml: () => '',
  renderCatalogFitNoteHtml: () => '',
});
vm.runInContext(html.slice(html.indexOf('function parseIsoDate(value) {'), html.indexOf('function buildDailyPublicationSeries(')), rendering);
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('function formatMetricCount(')), rendering);
vm.runInContext(html.slice(html.indexOf('function formatMetricCount('), html.indexOf('function getCurrentDailyWatchDateString(')), rendering);
vm.runInContext(card, rendering);
vm.runInContext(source.slice(source.indexOf('/** Describe every section placement'), source.indexOf('function syncReadingDeskSelection(')), rendering);
assert.match(rendering.renderMetricsHtml({ published_date: '2026-01-01', citations: 1000 }), /High influence/);
const influence = rendering.renderInfluenceBadgeHtml;
const influenceNow = new Date('2026-09-17T23:59:59Z');
assert.equal(influence({ published_date: '2026-04-17', citations: 5 }, influenceNow), '');
const highInfluence = influence({ published_date: '2026-04-17', citations: 6 }, influenceNow);
for (const text of ['6 citations', '5 completed months', '2026-04-17', '2026-09-17', 'not a quality assessment']) {
  assert.ok(highInfluence.includes(text), text);
}
assert.match(highInfluence, /<button type="button"[^>]*title="[^>]*aria-label="/);
assert.match(css, /\.metric-influence:hover \.influence-explanation\s*,\s*\.metric-influence:focus-visible \.influence-explanation\s*\{\s*display: block;/, 'Show the explanation on mouse hover as well as keyboard focus');
assert.match(css, /\.metric-influence:focus-visible \.influence-explanation/);
assert.match(css, /\.desk-detail-visual \.influence-explanation \{[^}]*top: auto;[^}]*bottom: calc\(100% \+ 6px\);/);
assert.match(css, /\.paper-table-number \.influence-explanation \{[^}]*position: fixed;[^}]*inset: auto;/, 'Table explanations must escape the table scroll clip');
const positioning = boot(null, false).context;
assert.equal(typeof positioning.positionInfluenceExplanation, 'function');
Object.assign(positioning.window, { innerWidth: 390, innerHeight: 600 });
const explanationBox = { offsetWidth: 260, offsetHeight: 110, style: {} };
const influenceButton = {
  closest: () => ({}), querySelector: () => explanationBox,
  getBoundingClientRect: () => ({ top: 230, bottom: 250, right: 380 }),
};
positioning.positionInfluenceExplanation(influenceButton);
assert.equal(explanationBox.style.left, '118px');
assert.equal(explanationBox.style.top, '250px');
influenceButton.getBoundingClientRect = () => ({ top: 560, bottom: 580, right: 100 });
positioning.positionInfluenceExplanation(influenceButton);
assert.equal(explanationBox.style.left, '12px');
assert.equal(explanationBox.style.top, '450px');
for (const [published_date, now, months] of [
  ['2026-09-17', influenceNow, 0], ['2026-09-01', influenceNow, 0],
  ['2026-08-18', influenceNow, 0], ['2026-08-17', influenceNow, 1],
  ['2026-04-18', influenceNow, 4], ['2026-12-31', new Date('2027-02-28T00:00:00Z'), 2],
  ['2023-12-31', new Date('2024-02-29T00:00:00Z'), 2],
  ['2023-12-31', new Date('2024-02-28T23:59:59Z'), 1],
]) {
  assert.equal(influence({ published_date, citations: months }, now), '', published_date);
  assert.match(influence({ published_date, citations: months + 1 }, now), /High influence/, published_date);
}
for (const citations of [null, undefined, '', '1000', -1, NaN, Infinity, 1.5]) {
  assert.equal(influence({ published_date: '2026-04-17', citations }, influenceNow), '');
}
for (const published_date of [null, '', '2026-02-30', '2026', '2026-09-18']) {
  assert.equal(influence({ published_date, citations: 1000 }, influenceNow), '');
}
assert.equal(influence({ entry_type: 'blog', published_date: '2026-04-17', citations: 1000 }, influenceNow), '');
assert.match(influence({ venue: 'arXiv', peer_reviewed: false, published_date: '2026-04-17', citations: 6 }, influenceNow), /High influence/, 'Citation influence is independent of peer-review status');
assert.equal(influence({ published_date: '2026-04-17', citations: 1000 }, new Date(NaN)), '');
Object.assign(rendering, { EXPANDED_TABLE_ROWS: new Set() });
vm.runInContext(html.slice(html.indexOf('function formatTableText('), html.indexOf('function getPaperDisplayDate(')), rendering);
vm.runInContext(html.slice(html.indexOf('function renderTableSectionHtml('), html.indexOf('function renderTableView(')), rendering);
const example = {
  id: '2301.13196', title: 'A paper', _authorsText: 'Author One, Author Two',
  venue: 'ICML', year: 2026, published_date: '2026-09-16', desc: 'A complete summary.',
  citations: 3, github_stars: 7,
  links: { arxiv: 'https://arxiv.org/abs/2301.13196', github: 'https://github.com/example/code' },
  community_comments: [{ label: 'A <reading> note', url: 'https://example.test/note?a=1&b=2' }],
  survey_core: true,
  _sections: ['architecture/depth-control', 'scaling/test-time'],
  _sectionLabel: '§4.5 Controlling recurrence depth',
  _axisEntries: [
    { group: 'loop_topology', value: 'whole-stack' }, { group: 'sharing', value: 'full' },
    { group: 'depth_control', value: 'unspecified' }, { group: 'claims', value: 'test-time-scaling' },
  ],
};
rendering.readingDeskDetailCollapsed = false;
const openCard = rendering.renderCard(example, '');
assert.match(openCard, /<article class="paper-card paper-row" data-id=/);
assert.match(openCard, /class="paper-row-thumb" aria-hidden="true"><img src="https:\/\/thumbnails\.assets\.alphaxiv\.org\//);
assert.match(openCard, /datetime="2026-09-16" title="Published">Sep 2026</);
assert.doesNotMatch(openCard, /desk-card-summary|paper-sections|data-facet-group|survey-core-badge|paper-links/, 'Rows leave details to the side panel');
assert.equal(rendering.formatCompactAuthors({ authors: ['A', 'B', 'C', 'D'] }), 'A, B, C and 1 other');
assert.equal(rendering.formatCompactAuthors({ authors: ['A', 'B', 'C', 'D', 'E'] }), 'A, B, C and 2 others');
assert.equal(rendering.formatCompactAuthors({ authors: ['A', 'B'] }), 'A, B');
assert.equal(rendering.formatRowDate('2026-10-04', true), 'Oct 4, 2026');
assert.equal(rendering.formatRowDate('2026-10-04', false), 'Oct 2026');
assert.equal(rendering.formatRowDate('soon', true), '');
assert.match(rendering.renderCard({ ...example, added_date: '2026-07-30' }, ''), /datetime="2026-07-30" title="Added to the collection">Jul 30, 2026</);
assert.match(rendering.renderCard({ ...example, added_date: undefined }, ''), /title="Added to the collection">—</);
const exampleRow = rendering.renderTableRow(example, '');
assert.match(exampleRow, /§4\.5 Controlling recurrence depth/);
assert.match(exampleRow, /data-facet-value="whole-stack"/);
assert.equal((exampleRow.match(/<td/g) || []).length, 9, 'Eight summary cells plus the detail cell');
assert.match(rendering.renderTableRow(example, ''), />ICML 2026<\/span>/);
assert.match(rendering.renderTableRow(example, ''), /ICML 2026 · 2026-09-16/);
rendering.renderReadingDeskDetail(example);
assert.match(detailContent.innerHTML, />ICML 2026<\/span>/);
for (const [paper, expected] of [
  [{ venue: 'ICLR', year: 2019, published_date: '2018-07-10' }, 'ICLR 2019'],
  [{ venue: 'Findings of ACL', year: 2026, published_date: '2025-08-22' }, 'Findings of ACL 2026'],
  [{ venue: 'COLM 2025 Workshop', year: 2025 }, 'COLM 2025 Workshop'],
  [{ venue: 'arXiv', year: 2026 }, 'arXiv'],
  [{ entry_type: 'blog', venue: 'Lab Blog', year: 2026 }, 'Lab Blog'],
  [{ venue: 'ICML', published_date: '2026-05-20' }, 'ICML'],
  [{ venue: 'ICML', year: 'invalid' }, 'ICML'],
  [{ year: 2026 }, ''],
]) assert.equal(rendering.getPaperVenueLabel(paper), expected);
const influentialExample = { ...example, published_date: '2026-01-01', citations: 1000 };
assert.match(rendering.renderTableRow(influentialExample, ''), /High influence/);
rendering.renderReadingDeskDetail(influentialExample);
assert.match(detailContent.innerHTML.split('</header>')[0], /High influence/);
rendering.readingDeskDetailCollapsed = true;
assert.equal(rendering.renderCard(example, ''), openCard);
for (const text of ['Author One, Author Two', 'Sep 2026']) {
  assert.ok(openCard.includes(text));
}
const cardWithoutPreview = rendering.renderCard({ ...example, id: 'non-arxiv-paper', links: {} }, '');
assert.match(cardWithoutPreview, /class="paper-row-thumb" aria-hidden="true"><\/div>/);
assert.match(css, /\.paper-row-thumb \{/);
assert.match(css.slice(css.indexOf('/* Compact catalog rows')), /@container paper-list \(max-width: 640px\)/);
assert.match(rendering.renderPaperLinksHtml(example), /Community Comments/);
assert.doesNotMatch(rendering.renderPaperLinksHtml(example, false), /Community Comments|reading/);
rendering.renderReadingDeskDetail(example);
const fixedHeader = detailContent.innerHTML.split('</header>')[0];
const scrollableBody = detailContent.innerHTML.split('</header>')[1];
assert.match(fixedHeader, /class="desk-detail-header"/);
assert.match(fixedHeader, /class="desk-card-preview desk-detail-preview"/);
assert.ok(fixedHeader.includes('src="' + thumbnail(example) + '"'));
assert.match(fixedHeader, /loading="eager" decoding="async" referrerpolicy="no-referrer"/);
assert.match(fixedHeader, /onerror="this\.parentElement\.remove\(\)"/);
assert.doesNotMatch(scrollableBody, /desk-detail-preview/);
assert.match(css, /\.desk-detail-visual \{[^}]*width: clamp\(96px, 25%, 144px\);/);
assert.match(css, /\.desk-detail-visual:empty \{ display: none;/);
assert.match(css, /\.reading-desk \.paper-detail \.paper-metrics \{[^}]*flex-direction: column;/);
assert.match(fixedHeader, /class="desk-detail-visual"><a[^>]*desk-detail-preview[\s\S]*<\/a><div class="paper-metrics">/);
assert.match(fixedHeader, /3 citations/);
assert.match(fixedHeader, /7 stars/);
assert.doesNotMatch(scrollableBody, /paper-metrics/);
assert.match(fixedHeader, /Author One, Author Two/);
assert.match(fixedHeader, /Open paper/);
assert.doesNotMatch(fixedHeader, /<h3>Summary/);
assert.match(scrollableBody, /^<div class="desk-detail-body" tabindex="0" role="region" aria-label="Resource details"><section class="desk-detail-section"><h3>Summary/);
for (const title of ['Topic-map placement', 'Sources', 'Discussion']) assert.ok(scrollableBody.includes(title));
const placement = scrollableBody.split('<h3>Topic-map placement</h3>')[1].split('</section>')[0];
assert.match(placement, /paper-section-badge is-primary/);
for (const label of ['Loop topology', 'Sharing', 'Depth control', 'Claims', 'Looped-vs-untied comparison']) assert.ok(placement.includes('<dt>' + label + '</dt>'), label);
assert.match(placement, /<dt>Depth control<\/dt><dd><span class="desk-axis-unspecified">unspecified/);
assert.match(placement, /<dt>Looped-vs-untied comparison<\/dt><dd><span class="desk-axis-unspecified">none recorded/);
assert.match(fixedHeader, />Core</);
assert.doesNotMatch(fixedHeader, /Survey/);
const primaryActions = detailContent.innerHTML.split('<div class="desk-primary-actions">')[1].split('</div>')[0];
assert.match(primaryActions, /Open paper/);
assert.doesNotMatch(primaryActions, /github|Code/);
assert.equal((detailContent.innerHTML.match(/https:\/\/github\.com\/example\/code/g) || []).length, 1);
const sourcesSection = detailContent.innerHTML.split('<h3 id="desk-sources-title">')[1].split('</section>')[0];
const discussionSection = detailContent.innerHTML.split('<h3 id="desk-discussion-title">')[1];
assert.match(sourcesSection, /https:\/\/arxiv\.org\/abs\/2301\.13196/);
assert.match(sourcesSection, /https:\/\/github\.com\/example\/code/);
assert.doesNotMatch(sourcesSection, /paper-metrics/);
assert.doesNotMatch(sourcesSection, /reading|Community Comments/);
assert.match(discussionSection, /A &lt;reading&gt; note/);
assert.match(discussionSection, /note\?a=1&amp;b=2/);
assert.doesNotMatch(discussionSection, /<details|<summary/);
rendering.renderReadingDeskDetail({ ...example, community_comments: [] });
assert.match(detailContent.innerHTML, /No community discussion links yet\./);
rendering.renderReadingDeskDetail({ ...example, entry_type: 'blog' });
assert.doesNotMatch(detailContent.innerHTML, /desk-detail-preview/);
rendering.renderReadingDeskDetail({ ...example, id: 'non-arxiv-paper', links: { paper: 'https://example.test/paper' } });
assert.doesNotMatch(detailContent.innerHTML, /desk-detail-preview/);
assert.match(detailContent.innerHTML.split('</header>')[0], /3 citations/);
rendering.renderReadingDeskDetail({ ...example, citations: 0, github_stars: 0 });
assert.match(detailContent.innerHTML, /0 citations/);
assert.match(detailContent.innerHTML, /0 stars/);
rendering.renderReadingDeskDetail({ ...example, id: 'non-arxiv-paper', links: {}, citations: null, github_stars: null });
assert.doesNotMatch(detailContent.innerHTML, /desk-detail-visual|paper-metrics/);
const modalCss = css.slice(css.indexOf('@media (max-width: 1119px)'), css.indexOf('@media (max-width: 768px)'));
assert.match(modalCss, /\.reading-desk \.paper-detail \{[^}]*inset: 0;[^}]*margin: auto;[^}]*height: calc\(100dvh - 48px\);[^}]*max-height: calc\(100dvh - 48px\)/);
assert.match(css, /\.reading-desk \.paper-detail \{ width: calc\(100vw - 24px\); height: calc\(100dvh - 24px\); max-height: calc\(100dvh - 24px\);/);
assert.match(css, /\.reading-desk \.paper-detail \{[^}]*overflow: hidden;/);
assert.match(css, /#paper-detail-content \{[^}]*display: flex;[^}]*flex-direction: column;[^}]*min-height: 0;/);
assert.match(css, /\.desk-detail-body \{[^}]*min-height: 0;[^}]*overflow-y: auto;/);
rendering.renderReadingDeskDetail(null);
assert.match(detailContent.innerHTML, /class="desk-detail-header"/);
assert.match(detailContent.innerHTML, /class="desk-detail-body"/);
// Design-axis filters: OR inside one axis, AND across axes, each removable on its own.
const axes = { loop_topology: { label: 'Loop topology', values: ['whole-stack', 'implicit-fixed-point', 'unspecified'] }, claims: { label: 'Claims', values: ['expressivity', 'stability'] } };
const facets = vm.createContext({
  SURVEY: { axes }, ACTIVE_FACET_FILTERS: {}, AXIS_CHIP_PREFIXES: { loop_topology: 'Topology', claims: 'Claim' },
  document: { getElementById: () => ({ value: 'recurrent' }) },
  syncFiltersToUrl(mode) { assert.equal(mode, 'replace'); }, updateFacetFilterUI() {},
  doSearch(query) { assert.equal(query, 'recurrent'); },
});
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('function highlightQuery(')), facets);
vm.runInContext(html.slice(html.indexOf('const FACET_GROUPS ='), html.indexOf('/** Serialize section, design-axis')), facets);
vm.runInContext(html.slice(html.indexOf('function getPaperAxisValues(paper, group) {'), html.indexOf('/** Return design-axis entries worth')), facets);
vm.runInContext(html.slice(html.indexOf('/** Match any selected value within an axis'), html.indexOf('function renderFacetFilterGroups() {')), facets);
const implicitPaper = { loop_topology: 'implicit-fixed-point', claims: ['stability'] };
const stackPaper = { loop_topology: 'whole-stack', claims: ['expressivity', 'stability'] };
facets.toggleFacetFilter('loop_topology', 'whole-stack');
facets.toggleFacetFilter('loop_topology', 'implicit-fixed-point');
assert.equal(facets.paperMatchesFacetFilters(implicitPaper) && facets.paperMatchesFacetFilters(stackPaper), true, 'OR within an axis');
facets.toggleFacetFilter('claims', 'expressivity');
assert.equal(facets.paperMatchesFacetFilters(implicitPaper), false, 'AND across axes');
assert.equal(facets.paperMatchesFacetFilters(stackPaper), true);
assert.equal(facets.getActiveFacetCount(), 3);
facets.toggleFacetFilter('claims', 'not-a-value');
assert.equal(facets.getActiveFacetCount(), 3, 'Unknown values are ignored');
const facetSummary = facets.renderActiveFacetFiltersHtml();
assert.equal((facetSummary.match(/class="facet-filter-active-remove"/g) || []).length, 3);
assert.match(facetSummary, /aria-label="Remove Loop topology filter: whole-stack"/);
assert.match(facetSummary, /<span aria-hidden="true">×<\/span><\/button>/);
facets.toggleFacetFilter('claims', 'expressivity');
assert.equal(facets.paperMatchesFacetFilters(implicitPaper), true);
assert.equal((facets.renderActiveFacetFiltersHtml().match(/class="facet-filter-active-remove"/g) || []).length, 2);
const filterHeading = html.slice(html.indexOf('<div class="facet-filter-header">'), html.indexOf('<div class="facet-filter-panel"'));
assert.ok(filterHeading.indexOf('</button>') < filterHeading.indexOf('id="facet-filter-summary"'));
assert.match(css, /\.reading-desk \.filter-sidebar-header \{[^}]*text-align: left;/);

// Survey-section filter: chapter-grouped options, membership matching, chapter-wide values.
const sectionSelect = { value: '', innerHTML: '' };
const surveyTaxonomy = {
  parts: [{ id: 'foundations', title: 'Part I. Foundations' }, { id: 'building', title: 'Part III. Building, Training and Deploying' }],
  chapters: [{ number: '2', part: 'foundations', title: 'From Recurrent Computation to Iterative Depth' }, { number: '4', part: 'building', title: 'Architecture & Design' }],
  sections: [
    { id: 'foundations/implicit', number: '2.3', chapter: '2', title: 'Deep equilibrium and implicit models' },
    { id: 'architecture/topology', number: '4.1', chapter: '4', title: 'Loop topology' },
    { id: 'architecture/depth-control', number: '4.5', chapter: '4', title: 'Controlling recurrence depth' },
  ],
  axes: {},
};
const sections = vm.createContext({
  ACTIVE_SECTION_FILTER: '', ACTIVE_TOP_LEVEL_TAB: 'papers', FACET_GROUPS: [],
  document: { getElementById: () => sectionSelect },
  syncFiltersToUrl() {}, rerenderCurrentResults() {},
  CATALOG_ADJACENT_NOTE: '',
});
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('function highlightQuery(')), sections);
vm.runInContext(html.slice(html.indexOf('/** Index the taxonomy parts, chapters and sections'), html.indexOf('/** Return a record\'s controlled values')), sections);
vm.runInContext(html.slice(html.indexOf('/** Return whether a section-filter value names'), html.indexOf('/** Return whether a design-axis value is currently selected.')), sections);
vm.runInContext(html.slice(html.indexOf('/** Return the DOM id of a chapter heading'), html.indexOf('/**\n * Scroll the list view')), sections);
vm.runInContext(html.slice(html.indexOf('function getPaperAxisValues(paper, group) {'), html.indexOf('/** Return design-axis entries worth')), sections);
vm.runInContext(html.slice(html.indexOf('function preparePaperRecord(paper) {'), html.indexOf('/** Count each design-axis value')), sections);
vm.runInContext(html.slice(html.indexOf('/** Populate chapter-grouped section choices'), html.indexOf('/** Blogs carry taxonomy sections only')), sections);
sections.setSurveyTaxonomy(surveyTaxonomy);
sections.restoreDerivedLinks = links => links;
const deqPaper = sections.preparePaperRecord({ id: 'deq', title: 'DEQ', survey_section: ['foundations/implicit', 'architecture/depth-control', 'retired/value'] });
assert.deepEqual([...deqPaper._sections], ['foundations/implicit', 'architecture/depth-control'], 'Unknown sections are dropped, order kept');
assert.equal(deqPaper._primarySection, 'foundations/implicit');
assert.equal(deqPaper._primaryChapter, '2');
assert.equal(deqPaper._sectionLabel, '§2.3 Deep equilibrium and implicit models');
assert.match(deqPaper._searchText, /§4\.5 controlling recurrence depth/);
const topoPaper = sections.preparePaperRecord({ id: 'topo', survey_section: ['architecture/topology'] });
sections.ALL_PAPERS = [deqPaper, topoPaper];
sections.ALL_BLOGS = [];
sections.renderSectionFilter();
assert.match(sectionSelect.innerHTML, /<option value="">All sections<\/option>/);
assert.match(sectionSelect.innerHTML, /<optgroup label="§4 Architecture &amp; Design"><option value="4">All of §4 · 2<\/option>/);
assert.match(sectionSelect.innerHTML, /§4\.5 Controlling recurrence depth · 1/);
sections.setSectionFilter('architecture/depth-control');
assert.equal(sectionSelect.value, 'architecture/depth-control');
assert.equal(sections.matchSectionFilter(deqPaper), true, 'Secondary placements match');
assert.equal(sections.matchSectionFilter(topoPaper), false);
sections.setSectionFilter('2');
assert.equal(sections.matchSectionFilter(deqPaper) && !sections.matchSectionFilter(topoPaper), true, 'Chapter values match any section in the chapter');
assert.equal(sections.getSectionFilterLabel(), '§2 From Recurrent Computation to Iterative Depth');
sections.setSectionFilter('analysis');
assert.equal(sectionSelect.value, '', 'Retired values are ignored');
assert.equal(sections.matchSectionFilter(topoPaper), true);
assert.equal(sections.getSectionDomId({ number: '4.5' }), 'section-4-5');
assert.match(html, /if \(!isBlogs\) count \+= getActiveFacetCount\(\);/);

// Exercise the actual scope/filter pipeline: paper-only filters cannot hide Blogs.
const categories = sections;
Object.assign(categories, {
  ACTIVE_SECTION_FILTER: '',
  ALL_PAPERS: [{ id: 'p', _primarySection: 'foundations/implicit', _sectionSet: new Set(['foundations/implicit']), _chapterSet: new Set(['2']), venue: 'ICML', peer_reviewed: true, added_date: '2026-09-16' }],
  ALL_BLOGS: [{ id: 'b', entry_type: 'blog', _sectionSet: new Set(['architecture/topology']), _chapterSet: new Set(['4']) }],
  ACTIVE_FACET_FILTERS: {},
  getActiveFacetCount: () => 0,
  ACCEPTED_ONLY: true,
  HIGH_INFLUENCE_ONLY: false,
  getHighInfluenceMonths: paper => rendering.getHighInfluenceMonths(paper, influenceNow),
  NEWLY_ARRIVED_ONLY: true,
  LATEST_ADDED_DATE: '2026-09-16',
  HAS_CODE_ONLY: false,
  HAS_COMMENTS_ONLY: false,
  CURRENT_SORT: 'date',
  CURRENT_VIEW: 'list',
  normalizeDateInputValue: value => value || null,
  matchPublicationDate: () => true,
  paperMatchesFacetFilters: () => true,
  paperMatchesQuery: (record, query) => !query || record.id === query,
  getPublicationDateFilter: () => ({ active: false }),
});
vm.runInContext(html.slice(html.indexOf('function matchAcceptedOnly(paper) {'), html.indexOf('/** Populate chapter-grouped section choices')), categories);
vm.runInContext(html.slice(html.indexOf('/** Blogs carry taxonomy sections only'), html.indexOf('function setFilterSidebarOpen(')), categories);
vm.runInContext(html.slice(html.indexOf('function normalizeTopLevelTab(tab) {'), html.indexOf('/** Design-axis filter groups in taxonomy order')), categories);
assert.match(filterPanel, /id="accepted-only-toggle"[^>]*>Peer-reviewed<\/button>/);
assert.match(filterPanel, /id="high-influence-only-toggle"[^>]*aria-pressed="false"[^>]*onclick="toggleHighInfluenceOnly\(\)"[^>]*>High influence<\/button>/);
assert.match(css, /\.blogs-mode #high-influence-only-toggle/);
assert.doesNotMatch(html, /Accepted only|accepted only/);
for (const [paper, expected] of [
  [{ venue: 'ICML', peer_reviewed: true }, true],
  [{ venue: 'ICML' }, true], [{ venue: 'ICLR' }, true],
  [{ venue: 'CompLearn Workshop @ ICML' }, true], [{ venue: 'IEEE Access' }, true],
  [{ venue: 'ICML', peer_reviewed: false }, false], [{ venue: 'Workshop', peer_reviewed: 'true' }, false],
  [{ venue: 'arXiv' }, false], [{ venue: ' arxiv ' }, false], [{ venue: 'Preprint' }, false],
  [{ venue: 'ICML (submitted)' }, false], [{ venue: 'Under review' }, false],
  [{ venue: 'Unknown' }, false], [{ venue: '' }, false], [{}, false],
  [{ entry_type: 'blog', venue: 'ICML' }, false],
  [{ venue: 'arXiv', peer_reviewed: false }, false], [{ entry_type: 'blog', peer_reviewed: true }, false],
]) assert.equal(categories.matchAcceptedOnly(paper), expected);
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'papers.json'), 'utf8'));
const catalogPapers = manifest.paper_chunks.flatMap(chunk => JSON.parse(fs.readFileSync(path.join(root, chunk.path), 'utf8')).papers);
assert.equal(catalogPapers.length, manifest.meta.paper_total);
for (const paper of catalogPapers) {
  assert.ok(Array.isArray(paper.survey_section) && paper.survey_section.length, paper.id + ': survey_section');
  for (const retired of ['category', 'foundation', 'mechanism_tags', 'focus_tags', 'domain_tags', 'tags']) assert.ok(!(retired in paper), paper.id + ': ' + retired);
}
const eqr = catalogPapers.find(paper => paper.id === '2605.21488');
assert.ok(eqr, 'EqR must be present in the canonical catalog');
assert.equal(categories.matchAcceptedOnly(eqr), true, 'EqR must not need a successful metadata refresh to retain its ICML status');
for (const paper of catalogPapers.filter(paper => paper.venue && paper.venue !== 'arXiv' && paper.peer_reviewed !== false)) {
  assert.equal(categories.matchAcceptedOnly(paper), true, paper.id + ': retain the curated publication venue');
}
categories.ACTIVE_SECTION_FILTER = '2';
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'p');
assert.equal(categories.getFilterSidebarActiveCount(), 3);
categories.ACTIVE_TOP_LEVEL_TAB = 'blogs';
assert.equal(categories.getFilteredPapers('', {}).length, 0, 'The section filter also applies to Blogs');
categories.ACTIVE_SECTION_FILTER = '';
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'b');
assert.equal(categories.getFilteredPapers('p', {}).length, 0);
assert.equal(categories.getFilterSidebarActiveCount(), 0);
categories.ACTIVE_TOP_LEVEL_TAB = 'papers';
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'p');

// The filter and badge share one rule, including zero completed months.
const highPaper = { id: 'high', _sectionSet: new Set(), _chapterSet: new Set(), venue: 'ICML', published_date: '2026-04-17', citations: 6 };
categories.ALL_PAPERS = [highPaper,
  { ...highPaper, id: 'equal', citations: 5 },
  { ...highPaper, id: 'preprint', venue: 'arXiv' },
];
categories.NEWLY_ARRIVED_ONLY = false;
const quickFilterStates = {};
categories.setToggleButtonState = (id, active) => { quickFilterStates[id] = active; };
categories.updateFilterSidebarSummary = () => {};
vm.runInContext(html.slice(html.indexOf('function updateQuickFilterButtons() {'), html.indexOf('function updateViewToggleButtons() {')), categories);
vm.runInContext(html.slice(html.indexOf('function toggleAcceptedOnly() {'), html.indexOf('function setView(view) {')), categories);
vm.runInContext(html.slice(html.indexOf('function getActiveFilterLabel('), html.indexOf('function sortPapers(')), categories);
categories.toggleHighInfluenceOnly();
assert.equal(quickFilterStates['high-influence-only-toggle'], true);
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'high');
assert.equal(categories.getFilterSidebarActiveCount(), 2);
assert.match(categories.getActiveFilterLabel('', {}), /high influence/);
categories.toggleAcceptedOnly();
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'high,preprint');
for (const paper of catalogPapers) {
  assert.equal(categories.matchHighInfluenceOnly(paper), Boolean(influence(paper, influenceNow)), paper.id + ': filter must match the badge');
}
assert.equal(rendering.getHighInfluenceMonths({ published_date: '2026-09-17', citations: 1 }, influenceNow), 0);
categories.ACTIVE_TOP_LEVEL_TAB = 'blogs';
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'b');
assert.equal(categories.getFilterSidebarActiveCount(), 0);
assert.doesNotMatch(categories.getActiveFilterLabel('', {}), /high influence/);
categories.ACTIVE_TOP_LEVEL_TAB = 'papers';
categories.toggleHighInfluenceOnly();
assert.equal(quickFilterStates['high-influence-only-toggle'], false);
assert.equal(categories.getFilteredPapers('', {}).length, 3);
for (const hash of ['#blogs', '#section-blogs']) {
  assert.equal(categories.getTopLevelTabFromHash(hash), 'blogs');
}
for (const hash of ['#section-4-5', '#chapter-4', '#section-designs']) assert.equal(categories.getTopLevelTabFromHash(hash), 'papers');
assert.equal(categories.normalizeTopLevelTab('blogs'), 'blogs');
assert.match(html, /id="blogs-tab" role="tab" aria-controls="papers-panel"/);
assert.doesNotMatch(html, /class="desk-blogs-link"/);
assert.match(html, /id="view-list-toggle"[^>]*>List view<\/button>/);
assert.match(html, /<nav class="survey-nav" id="survey-nav" aria-label="Chapters"/);
const grids = html.slice(html.indexOf('/** Count filtered papers by primary chapter'), html.indexOf('// ── Daily briefing page'));

// The list groups by Part → Chapter → primary Section and keeps the sort inside each section; the table is one global order.
const listElements = {
  'papers-grid': { innerHTML: '' }, 'blogs-grid': { innerHTML: '' }, 'blogs-count': {},
  'papers-table-body': { children: [], textContent: '' },
  'search-count': {}, 'no-results': { style: {} }, 'no-results-query': {},
  'search': { value: '' }, 'section-filter': sectionSelect,
};
let tableOrder = '';
const placed = (id, section, extra) => ({ id, _primarySection: section, _primaryChapter: section.startsWith('foundations') ? '2' : '4', _sectionSet: new Set([section]), _chapterSet: new Set(), ...extra });
Object.assign(categories, {
  ACTIVE_SECTION_FILTER: '', SORT_DIRECTIONS: {}, ACCEPTED_ONLY: false,
  ALL_PAPERS: [
    placed('a', 'architecture/depth-control', { published_date: '2026-09-17', citations: 2, github_stars: 10 }),
    placed('b', 'foundations/implicit', { published_date: '2026-09-15', citations: 5, github_stars: 30, survey_core: true }),
    placed('c', 'architecture/depth-control', { published_date: '2026-09-16', citations: 1, github_stars: 20 }),
    placed('d', 'architecture/topology', {}),
  ],
  document: { getElementById: id => listElements[id] || null, querySelectorAll: () => [] },
  updateSortButtons() {}, syncReadingDeskSelection() {}, observeSurveyChapters() {},
  updateFilterSidebarSummary() {}, applyViewMode() {},
  renderCard: paper => paper.id + ';',
  renderTableView: (query, papers) => { tableOrder = papers.map(paper => paper.id + ';').join(''); },
});
vm.runInContext(html.slice(html.indexOf('function getPaperSortDateValue('), html.indexOf('function updateSortButtons(')), categories);
vm.runInContext(html.slice(html.indexOf('function sortPapers('), html.indexOf('function setSort(')), categories);
vm.runInContext(html.slice(html.indexOf('/** Split "Part III.'), html.indexOf('/** Return a record\'s controlled values')), categories);
vm.runInContext(grids, categories);
const listOrder = () => listElements['papers-grid'].innerHTML.match(/\b[a-d];/g).join('');
for (const [sort, order, grouped] of [
  ['date', 'a;c;b;d;', 'b;d;a;c;'], ['stars', 'b;c;a;d;', 'b;d;c;a;'],
  ['citations', 'b;a;c;d;', 'b;d;a;c;'], ['default', 'b;a;c;d;', 'b;d;a;c;'],
]) {
  categories.CURRENT_SORT = sort;
  categories.CURRENT_VIEW = 'list';
  categories.renderAllGrids('');
  assert.equal(listOrder(), grouped, sort + ': list follows topic-map order, then the sort inside each section');
  categories.CURRENT_VIEW = 'table';
  categories.renderAllGrids('');
  assert.equal(tableOrder, order, sort + ': table sorts globally');
}
categories.CURRENT_VIEW = 'list';
categories.renderAllGrids('');
const listHtml = listElements['papers-grid'].innerHTML;
for (const fragment of ['id="part-foundations"', 'Part I</span>', 'id="chapter-4"', '§4</span>', 'id="section-4-5"', 'Controlling recurrence depth']) {
  assert.ok(listHtml.includes(fragment), fragment);
}
assert.ok(listHtml.indexOf('id="section-4-1"') < listHtml.indexOf('id="section-4-5"'), 'Sections follow topic-map order');
assert.match(listHtml, /id="chapter-4"[\s\S]*?<span class="survey-count"[^>]*>3<\/span>/, 'Chapter count is filtered primary count');
assert.doesNotMatch(listHtml, /id="section-2-3"[\s\S]*id="part-foundations"/);
categories.ACTIVE_SECTION_FILTER = 'architecture/depth-control';
categories.renderAllGrids('');
assert.equal(listOrder(), 'a;c;');
assert.doesNotMatch(listElements['papers-grid'].innerHTML, /part-foundations|section-4-1/, 'Empty groups are not rendered');
categories.ACTIVE_SECTION_FILTER = '';
categories.ACTIVE_TOP_LEVEL_TAB = 'blogs';
categories.renderAllGrids('');
assert.equal(listElements['papers-grid'].innerHTML, '');
assert.equal(listElements['blogs-grid'].innerHTML, 'b;');
categories.ACTIVE_TOP_LEVEL_TAB = 'papers';
categories.renderAllGrids('missing');
assert.equal(listElements['papers-grid'].innerHTML, '');
assert.equal(listElements['blogs-grid'].innerHTML, '');
assert.equal(listElements['no-results'].style.display, 'block');
// The Briefing tab renders briefing-latest.json with a small, escape-first Markdown renderer.
const briefingSource = html.slice(html.indexOf('// ── Daily briefing page'), html.indexOf('function createBlogSection() {'));
const briefingIntervals = [];
const briefingElements = {
  'briefing-tab-badge': { hidden: true },
  'briefing-tab-count': { textContent: '' },
};
const briefing = vm.createContext({
  CURRENT_NY_DATE: '2026-10-14',
  LATEST_BRIEFING_SUMMARY: null,
  setInterval: (fn, ms) => briefingIntervals.push(ms),
  document: { getElementById: (id) => briefingElements[id] || null },
});
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('/** Display the recorded publication year')), briefing);
vm.runInContext("function getCurrentDailyWatchDateString() { return CURRENT_NY_DATE; }", briefing);
vm.runInContext(briefingSource, briefing);
assert.deepEqual(briefingIntervals, [60000]);
const md = (text, options) => briefing.renderBriefingMarkdown(text, options);
assert.equal(md('# Daily Loop-Model Briefing\n\n## Outcome\n\nOne\nparagraph.', { dropLeadingTitle: true }), '<h2>Outcome</h2>\n<p>One paragraph.</p>');
assert.equal(md('# Title'), '<h2>Title</h2>', 'Body headings never outrank the page title');
assert.equal(md('### Paper\n#### Detail'), '<h3>Paper</h3>\n<h4>Detail</h4>');
assert.equal(
  md('**TL;DR:** Loops *help* with `K=4` [arXiv:2610.14252](https://arxiv.org/abs/2610.14252).'),
  '<p><strong>TL;DR:</strong> Loops <em>help</em> with <code>K=4</code> <a href="https://arxiv.org/abs/2610.14252" target="_blank" rel="noopener noreferrer">arXiv:2610.14252</a>.</p>'
);
assert.equal(
  md('- **Setup:** first\n  continued line\n- second\n\n1. one\n2. two'),
  '<ul><li><strong>Setup:</strong> first continued line</li><li>second</li></ul>\n<ol><li>one</li><li>two</li></ol>'
);
assert.equal(md('> quoted\n> text\n\n---\n\n```\n<b>x</b>\n```'), '<blockquote><p>quoted text</p></blockquote>\n<hr>\n<pre><code>&lt;b&gt;x&lt;/b&gt;</code></pre>');
// Raw HTML is escaped and unsafe link targets lose their link.
assert.equal(md('<script>alert(1)</script> <img src=x onerror=alert(1)>'), '<p>&lt;script&gt;alert(1)&lt;/script&gt; &lt;img src=x onerror=alert(1)&gt;</p>');
for (const target of ['javascript:alert(1)', 'JaVaScRiPt:void', 'data:text/html,x', 'vbscript:x', '//evil.example/x', '\\\\evil', 'java%0ascript:x']) {
  const rendered = md('[click](' + target + ')');
  assert.doesNotMatch(rendered, /<a\b/, target);
  assert.match(rendered, /click/, target);
}
assert.equal(md('[click](javascript:void)'), '<p>click</p>');
assert.equal(md('[mail](mailto:a@b.c) [rel](../papers/x.yaml) [frag](#added)'),
  '<p><a href="mailto:a@b.c">mail</a> <a href="../papers/x.yaml">rel</a> <a href="#added">frag</a></p>');
assert.equal(md('[x](https://e.com/?a=1&b="2")'), '<p><a href="https://e.com/?a=1&amp;b=&quot;2&quot;" target="_blank" rel="noopener noreferrer">x</a></p>');
assert.equal(md('`<b>` and **`code`**'), '<p><code>&lt;b&gt;</code> and **<code>code</code>**</p>');
assert.equal(md('2 * 3 * 4 and snake_case_name'), '<p>2 * 3 * 4 and snake_case_name</p>');
assert.equal(briefing.getSafeBriefingHref(' https://ok.example '), 'https://ok.example');
assert.equal(briefing.getSafeBriefingHref('java\nscript:alert(1)'), '');
// The page shows the eyebrow, title, Today/Latest label, summary, highlights, rendered body and GitHub source.
const pagePayload = {
  date: '2026-10-14', title: 'Daily Loop-Model Briefing - 2026-10-14', status: 'added', summary: 'Two <b>additions</b>.',
  highlights: ['First & best.'], candidates: [{ verdict: 'added' }, { verdict: 'added' }, { verdict: 'near-miss' }],
  source_path: 'briefings/2026/10/2026-10-14.md', body_markdown: '# Daily Loop-Model Briefing - 2026-10-14\n\n## Added\n\n### A paper',
};
const pageHtml = briefing.renderBriefingPageHtml(pagePayload);
assert.match(pageHtml, /<div class="briefing-page-eyebrow">Daily briefing<\/div>/);
assert.match(pageHtml, /<h2 class="briefing-page-title" id="briefing-page-title">Daily Loop-Model Briefing - 2026-10-14<\/h2>/);
assert.match(pageHtml, /class="briefing-page-when is-today">Today<\/span>/);
assert.match(pageHtml, /<time datetime="2026-10-14">October 14, 2026<\/time>/);
assert.match(pageHtml, /<span>2 papers added<\/span>/);
assert.match(pageHtml, /<p class="briefing-page-summary">Two &lt;b&gt;additions&lt;\/b&gt;\.<\/p>/);
assert.match(pageHtml, /<li>First &amp; best\.<\/li>/);
assert.match(pageHtml, /<div class="briefing-page-body"><h2>Added<\/h2>\n<h3>A paper<\/h3><\/div>/);
assert.match(pageHtml, /href="https:\/\/github\.com\/huskydoge\/Awesome-Loop-Models\/blob\/main\/briefings\/2026\/10\/2026-10-14\.md"/);
briefing.CURRENT_NY_DATE = '2026-10-15';
assert.match(briefing.renderBriefingPageHtml(pagePayload), /class="briefing-page-when">Latest briefing<\/span>/);
assert.doesNotMatch(briefing.renderBriefingPageHtml({ ...pagePayload, source_path: 'javascript:alert(1)' }), /github\.com|javascript/);
assert.match(briefing.renderBriefingPageHtml({ date: null }), /No daily briefing has been published yet/);
// The tab badge only counts added papers while the newest briefing is today's.
briefing.LATEST_BRIEFING_SUMMARY = pagePayload;
briefing.updateBriefingTabBadge();
assert.equal(briefingElements['briefing-tab-badge'].hidden, true);
briefing.CURRENT_NY_DATE = '2026-10-14';
briefing.updateBriefingTabBadge();
assert.equal(briefingElements['briefing-tab-badge'].hidden, false);
assert.equal(briefingElements['briefing-tab-count'].textContent, '2');
briefing.CURRENT_NY_DATE = '';
briefing.updateBriefingTabBadge();
assert.equal(briefingElements['briefing-tab-badge'].hidden, true);
// Real briefings render without leaking raw markup.
const latestPage = JSON.parse(fs.readFileSync(path.join(root, 'briefing-latest.json'), 'utf8'));
const latestHtml = briefing.renderBriefingMarkdown(latestPage.body_markdown, { dropLeadingTitle: true });
assert.doesNotMatch(latestHtml, /<h1|\*\*|\]\(/);
assert.match(latestHtml, /<h2>/);
assert.match(latestHtml, /<a href="https:\/\/arxiv\.org\/abs\//);
console.log('Reading desk: theme, selection, resizing, thumbnails, taxonomy sections, design axes, isolated Blogs, peer-review, influence and briefing-page checks passed.');
