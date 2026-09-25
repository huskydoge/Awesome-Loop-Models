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
const card = html.slice(html.indexOf('function renderCard(paper, query)'), html.indexOf('// ── State & Category Tree'));
assert.match(card, /class="desk-card-summary"/);
assert.match(card, /highlightQuery\(escapeHtml\(paper\.desc\), query\)/);
assert.match(card, /renderMetricsHtml\(paper\)/);
assert.match(card, /renderPaperTagHtml\(entry, 'paper-tag-' \+ entry\.group\)/);
assert.match(card, /aria-expanded="false" aria-controls="desk-card-tags-/);
assert.doesNotMatch(card + css, /desk-full-card|desk-paper-footer/);
assert.doesNotMatch(css, /\.desk-detail-collapsed #papers-panel/);
assert.match(css, /container: paper-list \/ inline-size/);
assert.match(css, /@container paper-list \(max-width: 640px\)/);
assert.match(css, /\.layout\.desk-detail-collapsed \{ grid-template-columns: var\(--desk-rail\) minmax\(0, 1fr\);/);
assert.match(html, /id="desk-show-details"[^>]+aria-controls="paper-detail"/);
assert.match(card, /renderPaperLinksHtml\(paper\)/);
assert.match(card, /paper-links desk-list-links/);
assert.match(card, /class="desk-card-preview"/);
assert.match(card, /loading="lazy" decoding="async" referrerpolicy="no-referrer"/);
assert.match(card, /onerror="this\.parentElement\.remove\(\)"/);
assert.match(html, /id="desk-divider"[^>]+role="separator"[^>]+aria-orientation="vertical"/);
assert.match(html, /id="desk-sidebar-divider"[^>]+role="separator"[^>]+aria-orientation="vertical"[^>]+aria-controls="desk-sidebar"/);
assert.match(css, /\.desk-divider\.desk-sidebar-divider \{[^}]*position: absolute;[^}]*left: calc\(var\(--desk-rail\) - 1px\);/);
assert.match(css.slice(css.indexOf('@media (max-width: 768px)')), /\.desk-sidebar-divider \{ display: none; \}/);
assert.match(html, /--font-body: Charter, Georgia/);
assert.doesNotMatch(html, /@media\s*\(prefers-color-scheme:\s*dark\)/);
assert.doesNotMatch(html, /category-disclaimer|desk-scope|About the classification/);
assert.doesNotMatch(html, /A field guide to recurrent depth|class="desk-subtitle"/);
assert.match(html, /<svg class="site-brand-mark"[^>]+aria-hidden="true">/);
assert.match(html, /<span class="site-brand-name">Awesome Loop Models<\/span>/);
assert.doesNotMatch(html, /id="sidebar-nav"|id="mobile-directory"/);
const filterPanel = html.slice(html.indexOf('<aside class="filter-sidebar"'), html.indexOf('<div class="top-level-panel" id="papers-panel"'));
assert.match(filterPanel, /<label for="category-filter"/);
assert.match(filterPanel, /id="category-filter" onchange="setCategoryFilter\(this.value\)"/);
assert.match(css, /\.reading-desk \.site-brand-name \{[^}]*max-width: none;/);
const watch = html.slice(html.indexOf('<section class="desk-watch"'), html.indexOf('<div class="desk-sidebar-bottom">'));
assert.match(watch, /aria-label="Catalog watch"/);
assert.doesNotMatch(watch, /desk-watch-title|<h2/);
assert.match(watch, /id="daily-watch-countdown"/);
assert.match(watch, /id="daily-briefing-body"/);
assert.doesNotMatch(watch, /<details|<summary/);
assert.match(css, /\.reading-desk \.daily-briefing-notice \{[^}]*font-size: 14px;[^}]*line-height: 1\.6;/);
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
  TAG_GROUP_LABELS: {},
  getReadingDeskThumbnailUrl: thumbnail,
  getPaperDisplayDate: paper => paper.published_date,
  renderCatalogFitBadgeHtml: () => '',
  renderCatalogFitNoteHtml: () => '',
});
vm.runInContext(html.slice(html.indexOf('function parseIsoDate(value) {'), html.indexOf('function buildDailyPublicationSeries(')), rendering);
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('function formatMetricCount(')), rendering);
vm.runInContext(html.slice(html.indexOf('function formatMetricCount('), html.indexOf('function getCurrentDailyWatchDateString(')), rendering);
vm.runInContext(card, rendering);
vm.runInContext(source.slice(source.indexOf('function renderReadingDeskDetail(paper) {'), source.indexOf('function syncReadingDeskSelection(')), rendering);
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
vm.runInContext(html.slice(html.indexOf('function renderTableTagLinksHtml('), html.indexOf('function renderTableView(')), rendering);
const example = {
  id: '2301.13196', title: 'A paper', _authorsText: 'Author One, Author Two',
  venue: 'ICML', year: 2026, published_date: '2026-09-16', desc: 'A complete summary.',
  citations: 3, github_stars: 7,
  links: { arxiv: 'https://arxiv.org/abs/2301.13196', github: 'https://github.com/example/code' },
  community_comments: [{ label: 'A <reading> note', url: 'https://example.test/note?a=1&b=2' }],
};
rendering.readingDeskDetailCollapsed = false;
const openCard = rendering.renderCard(example, '');
assert.match(openCard, />ICML 2026<\/span>/);
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
assert.match(rendering.renderCard(influentialExample, ''), /High influence/);
assert.match(rendering.renderTableRow(influentialExample, ''), /High influence/);
rendering.renderReadingDeskDetail(influentialExample);
assert.match(detailContent.innerHTML.split('</header>')[0], /High influence/);
rendering.readingDeskDetailCollapsed = true;
assert.equal(rendering.renderCard(example, ''), openCard);
for (const text of ['Author One, Author Two', '2026-09-16', '3 citations', 'A complete summary.', 'desk-card-preview']) {
  assert.ok(openCard.includes(text));
}
const cardVisual = openCard.split('<div class="desk-card-content">')[0];
assert.match(cardVisual, /class="desk-card-visual"><a[^>]*desk-card-preview[\s\S]*<\/a><div class="paper-metrics">/);
assert.match(cardVisual, /3 citations/);
assert.match(cardVisual, /7 stars/);
assert.equal((openCard.match(/class="paper-metrics"/g) || []).length, 1);
assert.doesNotMatch(openCard.split('<div class="desk-card-content">')[1], /paper-metrics/);
const cardWithoutPreview = rendering.renderCard({ ...example, id: 'non-arxiv-paper', links: {} }, '');
assert.doesNotMatch(cardWithoutPreview, /desk-card-preview/);
assert.match(cardWithoutPreview, /class="desk-card-visual"><div class="paper-metrics">/);
assert.match(cardWithoutPreview, /3 citations/);
const cardWithZeroMetrics = rendering.renderCard({ ...example, citations: 0, github_stars: 0 }, '');
assert.match(cardWithZeroMetrics, /0 citations/);
assert.match(cardWithZeroMetrics, /0 stars/);
assert.doesNotMatch(rendering.renderCard({ ...example, id: 'non-arxiv-paper', links: {}, citations: null, github_stars: null }, ''), /desk-card-visual|paper-metrics/);
assert.match(css, /\.desk-card-visual:empty \{ display: none;/);
assert.match(css, /\.desk-card-visual \.paper-metrics \{[^}]*flex-direction: column;[^}]*align-items: stretch;/);
assert.match(css.slice(css.indexOf('@container paper-list')), /\.desk-card-visual \{ float: right; width: 96px;/);
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
for (const title of ['Classification', 'Sources', 'Discussion']) assert.ok(scrollableBody.includes(title));
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
const activeTags = new Set(['mechanism::implicit-layer', 'focus::architecture']);
const filters = vm.createContext({
  ACTIVE_TAG_FILTERS: activeTags,
  URL_TAG_FILTER_KEYS: new Set(['mechanism::implicit-layer']),
  TAG_FILTER_LOOKUP: {
    'mechanism::implicit-layer': { group: 'mechanism', displayLabel: 'implicit-layer', count: 31 },
    'focus::architecture': { group: 'focus', displayLabel: 'architecture <tag>', count: 186 },
  },
  getPaperCountForTagKey: () => 30,
  getTagDrilldownGroupLabel: group => (group === 'mechanism' ? 'Mechanism' : 'Focus'),
  document: { getElementById: () => ({ value: 'recurrent' }) },
  updateTagFilterUI() {},
  doSearch(query) { assert.equal(query, 'recurrent'); },
});
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('function highlightQuery(')), filters);
vm.runInContext(html.slice(html.indexOf('function removeTagFilter(tagKey) {'), html.indexOf('function renderTagFilterGroups() {')), filters);
const tagSummary = filters.renderActiveTagFiltersHtml();
assert.equal((tagSummary.match(/class="tag-filter-active-remove"/g) || []).length, 2);
assert.match(tagSummary, /implicit-layer<\/span><span class="tag-filter-chip-count">30</);
assert.match(tagSummary, /architecture &lt;tag&gt;<\/span><span class="tag-filter-chip-count">186</);
assert.match(tagSummary, /aria-label="Remove Mechanism filter: implicit-layer"/);
assert.match(tagSummary, /<span aria-hidden="true">×<\/span><\/button>/);
filters.toggleTagFilter('focus::architecture');
assert.deepEqual([...activeTags], ['mechanism::implicit-layer']);
assert.equal((filters.renderActiveTagFiltersHtml().match(/class="tag-filter-active-remove"/g) || []).length, 1);
const filterHeading = html.slice(html.indexOf('<div class="tag-filter-header">'), html.indexOf('<div class="tag-filter-panel"'));
assert.ok(filterHeading.indexOf('</button>') < filterHeading.indexOf('id="tag-filter-summary"'));
assert.match(css, /\.reading-desk \.filter-sidebar-header \{[^}]*text-align: left;/);
const categorySelect = { value: '', innerHTML: '' };
const categories = vm.createContext({
  ACTIVE_CATEGORY_FILTER: '',
  CATEGORIES: { theory: { title: 'Theory & analysis' }, designs: { title: 'Architecture' } },
  getNodeCount: parts => parts[0] === 'theory' ? 2 : 3,
  document: { getElementById: () => categorySelect },
  rerenderCurrentResults() {},
});
vm.runInContext(html.slice(html.indexOf('function escapeHtml(str) {'), html.indexOf('function highlightQuery(')), categories);
vm.runInContext(html.slice(html.indexOf('function renderCategoryFilter() {'), html.indexOf('function paperMatchesActiveFilters(')), categories);
categories.renderCategoryFilter();
assert.match(categorySelect.innerHTML, /All categories/);
assert.match(categorySelect.innerHTML, /Theory &amp; analysis · 2/);
assert.equal(categories.matchCategoryFilter({ entry_type: 'blog' }), true);
categories.setCategoryFilter('theory');
assert.equal(categorySelect.value, 'theory');
assert.equal(categories.matchCategoryFilter({ category: 'theory' }), true);
assert.equal(categories.matchCategoryFilter({ category: 'designs' }), false);
assert.equal(categories.matchCategoryFilter({ category: 'theory', entry_type: 'blog' }), false);
categories.setCategoryFilter('designs');
assert.equal(categories.matchCategoryFilter({}), true);
categories.setCategoryFilter('invalid');
assert.equal(categorySelect.value, '');
assert.equal(categories.matchCategoryFilter({ entry_type: 'blog' }), true);
categories.CATALOG_DATA_READY = true;
categories.CURRENT_VIEW = 'category';
categories.window = { requestAnimationFrame() {} };
vm.runInContext(html.slice(html.indexOf('function restoreCategoryHashPosition(hash) {'), html.indexOf('function navigateToPaperSection(sectionId) {')), categories);
categories.setCategoryFilter('theory');
categories.restoreCategoryHashPosition('#section-theory');
assert.equal(categorySelect.value, 'theory');
categories.restoreCategoryHashPosition('#section-blogs');
assert.equal(categorySelect.value, 'theory');
categories.setCategoryFilter('theory');
categories.restoreCategoryHashPosition('#section-designs');
assert.equal(categorySelect.value, 'designs');
categories.restoreCategoryHashPosition('#section-missing');
assert.equal(categorySelect.value, 'designs');
assert.match(html, /if \(!isBlogs && ACTIVE_CATEGORY_FILTER\) count \+= 1;/);

// Exercise the actual scope/filter pipeline: paper-only filters cannot hide Blogs.
Object.assign(categories, {
  ACTIVE_TOP_LEVEL_TAB: 'papers',
  ALL_PAPERS: [{ id: 'p', category: 'theory', venue: 'ICML', peer_reviewed: true, added_date: '2026-09-16' }],
  ALL_BLOGS: [{ id: 'b', entry_type: 'blog' }],
  ACTIVE_TAG_FILTERS: new Set(),
  ACCEPTED_ONLY: true,
  HIGH_INFLUENCE_ONLY: false,
  getHighInfluenceMonths: paper => rendering.getHighInfluenceMonths(paper, influenceNow),
  NEWLY_ARRIVED_ONLY: true,
  LATEST_ADDED_DATE: '2026-09-16',
  HAS_CODE_ONLY: false,
  HAS_COMMENTS_ONLY: false,
  CURRENT_SORT: 'date',
  CURRENT_VIEW: 'category',
  normalizeDateInputValue: value => value || null,
  matchPublicationDate: () => true,
  paperMatchesTagFilters: () => true,
  paperMatchesQuery: (record, query) => !query || record.id === query,
  getPublicationDateFilter: () => ({ active: false }),
});
vm.runInContext(html.slice(html.indexOf('function matchAcceptedOnly(paper) {'), html.indexOf('function renderCategoryFilter() {')), categories);
vm.runInContext(html.slice(html.indexOf('function paperMatchesActiveFilters('), html.indexOf('function setFilterSidebarOpen(')), categories);
vm.runInContext(html.slice(html.indexOf('function normalizeTopLevelTab(tab) {'), html.indexOf('function getTagDrilldownKeysFromUrl() {')), categories);
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
const catalogPapers = JSON.parse(fs.readFileSync(path.join(root, 'papers.json'), 'utf8')).papers;
const eqr = catalogPapers.find(paper => paper.id === '2605.21488');
assert.ok(eqr, 'EqR must be present in the canonical catalog');
assert.equal(categories.matchAcceptedOnly(eqr), true, 'EqR must not need a successful metadata refresh to retain its ICML status');
for (const paper of catalogPapers.filter(paper => paper.venue && paper.venue !== 'arXiv' && paper.peer_reviewed !== false)) {
  assert.equal(categories.matchAcceptedOnly(paper), true, paper.id + ': retain the curated publication venue');
}
categories.setCategoryFilter('theory');
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'p');
assert.equal(categories.getFilterSidebarActiveCount(), 3);
categories.ACTIVE_TOP_LEVEL_TAB = 'blogs';
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'b');
assert.equal(categories.getFilteredPapers('p', {}).length, 0);
assert.equal(categories.getFilterSidebarActiveCount(), 0);
categories.ACTIVE_TOP_LEVEL_TAB = 'papers';
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'p');
assert.equal(categories.ACTIVE_CATEGORY_FILTER, 'theory');

// The filter and badge share one rule, including zero completed months.
const highPaper = { id: 'high', category: 'theory', venue: 'ICML', published_date: '2026-04-17', citations: 6 };
categories.ALL_PAPERS = [highPaper,
  { ...highPaper, id: 'equal', citations: 5 },
  { ...highPaper, id: 'preprint', venue: 'arXiv' },
  { ...highPaper, id: 'other-category', category: 'designs' },
];
categories.NEWLY_ARRIVED_ONLY = false;
const quickFilterStates = {};
categories.setToggleButtonState = (id, active) => { quickFilterStates[id] = active; };
vm.runInContext(html.slice(html.indexOf('function updateQuickFilterButtons() {'), html.indexOf('function updateViewToggleButtons() {')), categories);
vm.runInContext(html.slice(html.indexOf('function toggleAcceptedOnly() {'), html.indexOf('function setView(view) {')), categories);
vm.runInContext(html.slice(html.indexOf('function getActiveFilterLabel('), html.indexOf('function sortPapers(')), categories);
categories.toggleHighInfluenceOnly();
assert.equal(quickFilterStates['high-influence-only-toggle'], true);
assert.equal(categories.getFilteredPapers('', {}).map(record => record.id).join(','), 'high');
assert.equal(categories.getFilterSidebarActiveCount(), 3);
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
assert.equal(categories.getTopLevelTabFromHash('#section-designs'), 'papers');
assert.equal(categories.normalizeTopLevelTab('blogs'), 'blogs');
assert.match(html, /id="blogs-tab" role="tab" aria-controls="papers-panel"/);
assert.doesNotMatch(html, /class="desk-blogs-link"/);
assert.doesNotMatch(html, /Category view|function createCategorySection/);
assert.match(html, /id="view-category-toggle"[^>]*>List view<\/button>/);
const grids = html.slice(html.indexOf('function renderAllGrids(q) {'), html.indexOf('function createTreeNode('));
assert.doesNotMatch(grids, /if \(!hasActiveFilter\)/);
assert.match(grids, /syncSectionVisibility\(\);/);

// Render the same globally sorted results in list and table views, across categories.
const listElements = {
  'papers-grid': { innerHTML: '' }, 'blogs-grid': { innerHTML: '' },
  'papers-table-body': { children: [], textContent: '' },
  'search-count': {}, 'no-results': { style: {} }, 'no-results-query': {},
  'search': { value: '' }, 'category-filter': categorySelect,
};
let tableOrder = '';
Object.assign(categories, {
  ACTIVE_CATEGORY_FILTER: '', SORT_DIRECTIONS: {},
  ALL_PAPERS: [
    { id: 'a', category: 'theory', published_date: '2026-09-17', citations: 2, github_stars: 10 },
    { id: 'b', category: 'designs', published_date: '2026-09-15', citations: 5, github_stars: 30, foundation: true },
    { id: 'c', category: 'theory', published_date: '2026-09-16', citations: 1, github_stars: 20 },
    { id: 'd', category: 'designs' },
  ],
  document: { getElementById: id => listElements[id] || null, querySelectorAll: () => [] },
  updateSortButtons() {}, syncDynamicCounts() {}, syncReadingDeskSelection() {},
  syncSectionVisibility() {}, syncTreeVisibility() {}, updateFilterSidebarSummary() {}, applyViewMode() {},
  renderCard: paper => paper.id + ';',
  renderTableView: (query, papers) => { tableOrder = papers.map(paper => paper.id + ';').join(''); },
});
vm.runInContext(html.slice(html.indexOf('function getPaperSortDateValue('), html.indexOf('function updateSortButtons(')), categories);
vm.runInContext(html.slice(html.indexOf('function sortPapers('), html.indexOf('function setSort(')), categories);
vm.runInContext(grids, categories);
for (const [sort, order] of [['date', 'a;c;b;d;'], ['stars', 'b;c;a;d;'], ['citations', 'b;a;c;d;'], ['default', 'b;a;c;d;']]) {
  categories.CURRENT_SORT = sort;
  categories.CURRENT_VIEW = 'category';
  categories.renderAllGrids('');
  assert.equal(listElements['papers-grid'].innerHTML, order, sort + ': list must sort across category boundaries');
  categories.CURRENT_VIEW = 'table';
  categories.renderAllGrids('');
  assert.equal(tableOrder, order, sort + ': list and table must agree');
}
categories.CURRENT_SORT = 'stars';
categories.setCategoryFilter('theory');
categories.renderAllGrids('');
assert.equal(listElements['papers-grid'].innerHTML, 'c;a;', 'Category remains a filter on the unified list');
categories.ACTIVE_TOP_LEVEL_TAB = 'blogs';
categories.renderAllGrids('');
assert.equal(listElements['papers-grid'].innerHTML, '');
assert.equal(listElements['blogs-grid'].innerHTML, 'b;');
categories.ACTIVE_TOP_LEVEL_TAB = 'papers';
categories.renderAllGrids('missing');
assert.equal(listElements['papers-grid'].innerHTML, '');
assert.equal(listElements['blogs-grid'].innerHTML, '');
assert.equal(listElements['no-results'].style.display, 'block');
console.log('Reading desk: theme, selection, resizing, thumbnails, tags, category, isolated Blogs, peer-review and influence checks passed.');
