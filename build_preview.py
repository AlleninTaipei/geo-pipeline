"""
讀取 6 個 JSON-LD 檔，生成單一自包含 HTML 預覽頁面。
"""

import json

CATEGORIES = [
    ("AIO",      "AIO.json",      "一體式水冷"),
    ("DT",       "DT.json",       "迷你桌機"),
    ("MB",       "MB.json",       "主機板"),
    ("Monitors", "Monitors.json", "顯示器"),
    ("PSU",      "PSU.json",      "電源供應器"),
    ("VGA",      "VGA.json",      "顯示卡"),
]

all_data = {}
for key, fname, _ in CATEGORIES:
    with open(f"D:/geo/{fname}", encoding="utf-8") as f:
        all_data[key] = json.load(f)

data_json = json.dumps(all_data, ensure_ascii=False)

cats_meta = json.dumps(
    [{"key": k, "label": l, "count": len(all_data[k])} for k, _, l in CATEGORIES],
    ensure_ascii=False
)

HTML = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ASRock Schema.org JSON-LD 預覽</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #f4f6f9;
    --sidebar-bg: #1e2533;
    --sidebar-hover: #2d3548;
    --accent: #e8450a;
    --card-bg: #ffffff;
    --border: #e2e6ea;
    --text: #1a1d23;
    --muted: #6b7280;
    --code-bg: #1e2533;
    --code-text: #a8d8b9;
    --tag-bg: #fff3ee;
    --tag-text: #e8450a;
  }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    min-height: 100vh;
  }}

  /* ── Sidebar ── */
  #sidebar {{
    width: 220px;
    min-width: 220px;
    background: var(--sidebar-bg);
    color: #c9d1e0;
    display: flex;
    flex-direction: column;
    position: sticky;
    top: 0;
    height: 100vh;
    overflow-y: auto;
  }}
  #sidebar .logo {{
    padding: 20px 18px 14px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: #fff;
    border-bottom: 1px solid #2d3548;
  }}
  #sidebar .logo span {{
    display: block;
    font-size: 10px;
    font-weight: 400;
    color: #6b7a99;
    margin-top: 2px;
    letter-spacing: .04em;
    text-transform: none;
  }}
  .cat-btn {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 18px;
    cursor: pointer;
    border: none;
    background: transparent;
    color: #9aa5be;
    font-size: 13.5px;
    text-align: left;
    width: 100%;
    transition: background .15s, color .15s;
  }}
  .cat-btn:hover {{ background: var(--sidebar-hover); color: #fff; }}
  .cat-btn.active {{ background: var(--accent); color: #fff; }}
  .cat-btn .badge {{
    background: rgba(255,255,255,.15);
    border-radius: 10px;
    padding: 1px 7px;
    font-size: 11px;
    min-width: 28px;
    text-align: center;
  }}
  .cat-btn.active .badge {{ background: rgba(255,255,255,.3); }}

  /* ── Main ── */
  #main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }}

  /* ── Topbar ── */
  #topbar {{
    background: #fff;
    border-bottom: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 14px;
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  #topbar h1 {{
    font-size: 15px;
    font-weight: 600;
    white-space: nowrap;
    color: var(--text);
  }}
  #search {{
    flex: 1;
    padding: 8px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 13.5px;
    outline: none;
    transition: border-color .2s;
  }}
  #search:focus {{ border-color: var(--accent); }}
  #result-count {{
    font-size: 12.5px;
    color: var(--muted);
    white-space: nowrap;
  }}

  /* ── Grid ── */
  #grid {{
    padding: 20px 24px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
    align-content: start;
  }}

  /* ── Card ── */
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    transition: box-shadow .2s;
  }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,.08); }}
  .card-head {{
    padding: 14px 16px 10px;
    border-bottom: 1px solid var(--border);
  }}
  .card-name {{
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
    line-height: 1.4;
  }}
  .card-tag {{
    display: inline-block;
    background: var(--tag-bg);
    color: var(--tag-text);
    font-size: 10.5px;
    font-weight: 600;
    padding: 1px 7px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: .04em;
  }}
  .card-desc {{
    padding: 10px 16px;
    font-size: 12.5px;
    color: var(--muted);
    line-height: 1.55;
    flex: 1;
    /* clamp to 3 lines */
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .card-footer {{
    padding: 8px 16px;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }}
  .toggle-btn, .copy-btn {{
    font-size: 11.5px;
    padding: 4px 10px;
    border-radius: 5px;
    border: 1px solid var(--border);
    cursor: pointer;
    background: transparent;
    color: var(--muted);
    transition: background .15s, color .15s;
  }}
  .toggle-btn:hover {{ background: var(--bg); color: var(--text); }}
  .copy-btn:hover {{ background: #eafaf0; color: #1a7f4b; border-color: #b2dfcc; }}
  .copy-btn.copied {{ background: #eafaf0; color: #1a7f4b; border-color: #b2dfcc; }}

  .code-block {{
    display: none;
    background: var(--code-bg);
    padding: 12px 14px;
    font-family: "Fira Code", "Cascadia Code", monospace;
    font-size: 11px;
    line-height: 1.6;
    color: var(--code-text);
    overflow-x: auto;
    border-top: 1px solid #2d3548;
    white-space: pre;
  }}
  .code-block.open {{ display: block; }}

  /* ── Pagination ── */
  #pagination {{
    padding: 16px 24px 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    flex-wrap: wrap;
  }}
  .page-btn {{
    padding: 5px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: #fff;
    cursor: pointer;
    font-size: 13px;
    color: var(--text);
    transition: background .15s;
  }}
  .page-btn:hover {{ background: var(--bg); }}
  .page-btn.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .page-btn:disabled {{ opacity: .4; cursor: default; }}
  #page-info {{ font-size: 12.5px; color: var(--muted); margin: 0 8px; }}

  /* ── Empty state ── */
  #empty {{
    display: none;
    padding: 60px 24px;
    text-align: center;
    color: var(--muted);
    font-size: 14px;
  }}
</style>
</head>
<body>

<nav id="sidebar">
  <div class="logo">
    ASRock
    <span>Schema.org JSON-LD 預覽</span>
  </div>
  <div id="cat-list"></div>
</nav>

<div id="main">
  <div id="topbar">
    <h1 id="topbar-title">產品總覽</h1>
    <input id="search" type="search" placeholder="搜尋產品型號或描述...">
    <span id="result-count"></span>
  </div>
  <div id="grid"></div>
  <div id="empty">找不到符合的產品</div>
  <div id="pagination"></div>
</div>

<script>
const DATA = {data_json};
const CATS = {cats_meta};
const PAGE_SIZE = 24;

let currentCat = CATS[0].key;
let currentQuery = '';
let currentPage = 1;
let filteredItems = [];

// ── Build sidebar ──
const catList = document.getElementById('cat-list');
CATS.forEach(c => {{
  const btn = document.createElement('button');
  btn.className = 'cat-btn' + (c.key === currentCat ? ' active' : '');
  btn.dataset.key = c.key;
  btn.innerHTML = `<span>${{c.label}}<br><small style="font-size:11px;opacity:.7">${{c.key}}</small></span><span class="badge">${{c.count}}</span>`;
  btn.addEventListener('click', () => selectCat(c.key));
  catList.appendChild(btn);
}});

function selectCat(key) {{
  currentCat = key;
  currentPage = 1;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('active', b.dataset.key === key));
  const meta = CATS.find(c => c.key === key);
  document.getElementById('topbar-title').textContent = meta.label + '（' + meta.key + '）';
  applyFilter();
}}

// ── Search ──
document.getElementById('search').addEventListener('input', e => {{
  currentQuery = e.target.value.trim().toLowerCase();
  currentPage = 1;
  applyFilter();
}});

function applyFilter() {{
  const items = DATA[currentCat] || [];
  if (currentQuery) {{
    filteredItems = items.filter(p =>
      p.name.toLowerCase().includes(currentQuery) ||
      p.description.toLowerCase().includes(currentQuery)
    );
  }} else {{
    filteredItems = items;
  }}
  document.getElementById('result-count').textContent =
    filteredItems.length + ' / ' + items.length + ' 筆';
  render();
}}

// ── Render cards ──
function render() {{
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  grid.innerHTML = '';

  const start = (currentPage - 1) * PAGE_SIZE;
  const page = filteredItems.slice(start, start + PAGE_SIZE);

  if (filteredItems.length === 0) {{
    empty.style.display = 'block';
    renderPagination(0);
    return;
  }}
  empty.style.display = 'none';

  const catMeta = CATS.find(c => c.key === currentCat);

  page.forEach((product, idx) => {{
    const jsonStr = JSON.stringify(product, null, 2);
    const cardId = 'card-' + start + '-' + idx;

    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-head">
        <div class="card-name">${{esc(product.name)}}</div>
        <span class="card-tag">${{esc(catMeta.key)}}</span>
      </div>
      <div class="card-desc">${{esc(product.description)}}</div>
      <div class="card-footer">
        <button class="toggle-btn" onclick="toggleCode('${{cardId}}', this)">JSON-LD</button>
        <button class="copy-btn" onclick="copyCode('${{cardId}}', this)">複製</button>
      </div>
      <pre class="code-block" id="${{cardId}}">${{esc(jsonStr)}}</pre>
    `;
    grid.appendChild(card);
  }});

  renderPagination(filteredItems.length);
}}

function esc(s) {{
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}}

// ── Toggle JSON-LD block ──
function toggleCode(id, btn) {{
  const block = document.getElementById(id);
  const open = block.classList.toggle('open');
  btn.textContent = open ? '收起' : 'JSON-LD';
}}

// ── Copy ──
function copyCode(id, btn) {{
  const text = document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(() => {{
    btn.textContent = '已複製 ✓';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = '複製'; btn.classList.remove('copied'); }}, 1500);
  }});
}}

// ── Pagination ──
function renderPagination(total) {{
  const pag = document.getElementById('pagination');
  pag.innerHTML = '';
  const totalPages = Math.ceil(total / PAGE_SIZE);
  if (totalPages <= 1) return;

  const prev = document.createElement('button');
  prev.className = 'page-btn';
  prev.textContent = '‹ 上一頁';
  prev.disabled = currentPage === 1;
  prev.onclick = () => {{ currentPage--; render(); scrollToTop(); }};
  pag.appendChild(prev);

  const info = document.createElement('span');
  info.id = 'page-info';
  info.textContent = `第 ${{currentPage}} / ${{totalPages}} 頁`;
  pag.appendChild(info);

  // page number buttons (show window of 5)
  const start = Math.max(1, currentPage - 2);
  const end   = Math.min(totalPages, currentPage + 2);
  for (let p = start; p <= end; p++) {{
    const btn = document.createElement('button');
    btn.className = 'page-btn' + (p === currentPage ? ' active' : '');
    btn.textContent = p;
    btn.onclick = (pp => () => {{ currentPage = pp; render(); scrollToTop(); }})(p);
    pag.appendChild(btn);
  }}

  const next = document.createElement('button');
  next.className = 'page-btn';
  next.textContent = '下一頁 ›';
  next.disabled = currentPage === totalPages;
  next.onclick = () => {{ currentPage++; render(); scrollToTop(); }};
  pag.appendChild(next);
}}

function scrollToTop() {{
  document.getElementById('grid').scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

// ── Init ──
selectCat(CATS[0].key);
</script>
</body>
</html>"""

out_path = "D:/geo/preview.html"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"已生成：{out_path}")
import os
print(f"檔案大小：{os.path.getsize(out_path)/1024:.1f} KB")
