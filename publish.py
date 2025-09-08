#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os, re, shutil, datetime, json
from pathlib import Path
from urllib.parse import urljoin
import frontmatter, markdown
from slugify import slugify
from jinja2 import Template

# ---------- Paths ----------
ROOT = Path(__file__).resolve().parent
POSTS = ROOT / "posts"
IMAGES = ROOT / "images"
SITE   = ROOT / "site"
OUT_POSTS = SITE / "posts"
CAT_DIR   = SITE / "category"

BASE_URL = os.environ.get("BASE_URL", "/").rstrip("/") + "/"
BRAND    = os.environ.get("BRAND", "CacheMissed Blog")  # brand trên header

SITE.mkdir(exist_ok=True)
OUT_POSTS.mkdir(parents=True, exist_ok=True)
CAT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- CSS ----------
STYLE_CSS = r"""
:root{
  --brand:#7f4beb; --brand-ink:#3b1d77;
  --ink:#111; --muted:#666; --rule:#e6e6ee; --bg:#ffffff; --surface:#ffffff;
  --link:#1f6feb; --pill:#f2f3f8; --pill-ink:#111;
  --w: clamp(640px, 86vw, 820px);
  --head-h: 60px;
  --toc-offset: 18vh; /* ~1/3 màn hình. Tuỳ ý: 22vh, 30vh,... */

  /* dark */
  --d-bg:#0a0a0a; --d-ink:#f5d26b; --d-muted:#9c7f2b; --d-rule:#1a1a1a; --d-link:#ffd166; --d-pill:#121212; --d-pill-ink:#f5d26b;
}
@media (prefers-color-scheme: dark){
  :root{ --ink:var(--d-ink); --muted:var(--d-muted); --rule:var(--d-rule); --bg:var(--d-bg); --surface:var(--d-bg); --link:var(--d-link); --pill:var(--d-pill); --pill-ink:var(--d-pill-ink);}
}
:root[data-theme="light"]{
  --ink:#111; --muted:#666; --rule:#e6e6ee; --bg:#fff; --surface:#fff; --link:#1f6feb; --pill:#f2f3f8; --pill-ink:#111;
}
:root[data-theme="dark"]{
  --ink:var(--d-ink); --muted:var(--d-muted); --rule:var(--d-rule); --bg:var(--d-bg); --surface:var(--d-bg); --link:var(--d-link); --pill:var(--d-pill); --pill-ink:var(--d-pill-ink);
}

*{box-sizing:border-box} html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,"Noto Sans",sans-serif}
a{color:var(--link)} img{max-width:100%;height:auto}

/* ===== HEADER (sticky) + breadcrumb ===== */
.site-head{position:sticky;top:0;z-index:50;background:var(--surface);border-bottom:1px solid var(--rule)}
.head-inner{max-width:1200px;margin:0 auto;padding:14px 18px;display:flex;align-items:center;gap:12px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);font-weight:500;min-width:0}
.brand .logo{width:28px;height:28px;display:block;flex:0 0 auto}
.brand .logo-dark{display:none}
:root[data-theme="dark"] .brand .logo-dark{display:block}
:root[data-theme="dark"] .brand .logo-light{display:none}
.brand span.txt{display:block;max-width:26vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.brand-path{display:flex;align-items:center;gap:6px;min-width:0;color:var(--muted);font-weight:600}
.brand-path .sep{opacity:.6}
.docico{width:18px;height:18px;flex:0 0 auto;color:var(--muted)}
.crumb-txt{max-width:38vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink)}

.spacer{flex:1 1 auto}

/* Search */
.search{display:flex; align-items:center; gap:8px; border:1px solid var(--rule); padding:8px 12px; border-radius:999px; background:transparent; min-width:260px}
.search input{border:0; outline:0; background:transparent; color:var(--ink); width:180px}
.s-clear{display:none; border:0; background:transparent; color:var(--muted); cursor:pointer}
.search.has-text .s-clear{display:inline}
.s-ico-btn{display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:999px; border:0; background:transparent; cursor:pointer; color:var(--brand-ink)}
.s-ico-btn svg{width:18px; height:18px; stroke:currentColor}
:root[data-theme="dark"] .s-ico-btn{ color:var(--d-ink) }
.no-search .search{display:none} /* Ẩn search trên post */

/* Theme toggle */
.theme{display:inline-flex;align-items:center;gap:10px;border:0;background:none;cursor:pointer;padding:0}
.theme .label{font-weight:800;letter-spacing:.08em;font-size:12px;color:var(--muted);opacity:.35;transition:opacity .25s ease,color .25s ease}
:root[data-theme="light"] .theme .label-light{color:var(--ink);opacity:1}
:root[data-theme="light"] .theme .label-dark{opacity:.30}
:root[data-theme="dark"]  .theme .label-dark{color:var(--ink);opacity:1}
:root[data-theme="dark"]  .theme .label-light{opacity:.30}
.theme .track{position:relative;width:58px;height:28px;border-radius:999px;background:#e9edf3;border:1px solid var(--rule)}
:root[data-theme="dark"] .theme .track{background:#b7c0ce;border-color:#2a2a2a}
.theme .knob{position:absolute;top:3px;left:3px;width:22px;height:22px;border-radius:50%;transition:transform .25s ease,background .2s ease,box-shadow .2s ease}
:root[data-theme="dark"] .theme .knob{transform:none;background:transparent;box-shadow:none}
:root[data-theme="light"] .theme .knob{background:#ffd166;box-shadow:inset 0 0 0 2px rgba(0,0,0,.06);transform:translateX(28px)}
:root[data-theme="light"] .theme .knob::after{content:"";position:absolute;left:50%;top:50%;width:2px;height:2px;background:#ffd166;border-radius:1px;transform:translate(-50%,-50%);box-shadow:0 -9px 0 0 #ffd166,0 9px 0 0 #ffd166,9px 0 0 0 #ffd166,-9px 0 0 0 #ffd166,6.4px -6.4px 0 0 #ffd166,-6.4px -6.4px 0 0 #ffd166,6.4px  6.4px 0 0 #ffd166,-6.4px  6.4px 0 0 #ffd166}

/* Layouts chung */
main{max-width:var(--w); margin:28px auto; padding:0 16px}
h1{text-align:center;font-size:28px;margin:12px 0 18px}
.hr{height:2px;background:var(--rule);margin:16px 0 18px}
.pills{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin:6px 0 12px}
.pill{padding:8px 12px;border-radius:999px;background:var(--pill);color:var(--pill-ink);text-decoration:none;font-weight:700;font-size:14px;letter-spacing:.2px}
.post{margin:26px 0 34px}
.post .date{color:var(--muted);font-size:13px;margin-bottom:4px;letter-spacing:.2px}
.post h2{font-size:26px;line-height:1.25;margin:0}
.post a{text-decoration:none}
.post a:hover{text-decoration:underline}
article.content{max-width:var(--w);margin:28px auto;padding:0 16px}
article.content h1{font-size:34px;text-align:left;margin:0 0 10px}
.meta{color:var(--muted);font-size:14px;margin-bottom:12px}
footer{max-width:var(--w);margin:40px auto 60px;padding:0 16px;color:var(--muted);font-size:14px}

/* ===== TOC bên TRÁI (offset ~1/3 viewport) ===== */
.post-wrap{
  max-width:1200px;
  margin:28px auto;
  padding:0 18px;
  display:grid;
  grid-template-columns: 260px 1fr;   /* TOC | CONTENT */
  gap:28px;
}
.toc{
  position:sticky;
  top:calc(var(--head-h) + var(--toc-offset));
  align-self:start;
  max-height: calc(100vh - var(--head-h) - var(--toc-offset) - 20px);
  overflow:auto;
  padding-left:10px;
  border-left:2px solid var(--rule);
  font-size:13px; line-height:1.35; color:var(--muted);
}
.toc .toc-title{font-weight:700;color:var(--ink);margin:0 0 6px 0;line-height:1.1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.toc ul{list-style:none;margin:0;padding:0}
.toc li{margin:4px 0}
.toc a{color:var(--muted);text-decoration:none}
.toc a:hover{color:var(--link);text-decoration:underline}
.toc .lvl-2{padding-left:10px}
.toc .lvl-3{padding-left:18px}
#toc.collapsed .lvl-2, #toc.collapsed .lvl-3{ display:none }
.toc-tools{margin-top:8px;border-top:1px solid var(--rule);padding-top:8px;display:flex;flex-direction:column;gap:6px}
.toc-tools a{color:var(--muted);text-decoration:none;font-size:12.5px}
.toc-tools a:hover{color:var(--link);text-decoration:underline}

@media (max-width:1024px){
  .post-wrap{display:block}
  .toc{
    position:relative; top:auto; max-height:none;
    border-left:0; border-top:1px solid var(--rule);
    padding-left:0; padding-top:10px; margin:0 auto 12px; max-width:var(--w)
  }
}

/* ==== Fix moon icon (dark) – make it bold & always visible ==== */
:root[data-theme="dark"] .theme .knob{
  background: transparent !important;
  box-shadow: none !important;
  z-index: 1;
}
:root[data-theme="dark"] .theme .knob::after{
  content:"";
  position:absolute; left:50%; top:50%;
  width:20px; height:20px;
  transform:translate(-50%,-50%);
  background-repeat:no-repeat;
  background-position:center;
  background-size:20px 20px;
  /* Mặt trăng màu vàng, viền đen để nổi bật trên mọi nền */
  filter: drop-shadow(0 0 1px rgba(0,0,0,.45));
  background-image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>\
  <path d='M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z' \
        fill='%23f5d26b' stroke='%23000000' stroke-width='1.6'/>\
</svg>");
}

/* Sun (light) giữ nguyên – nếu muốn đậm hơn: */
:root[data-theme="light"] .theme .knob{
  background:#ffd166 !important;
  box-shadow: inset 0 0 0 2px rgba(0,0,0,.06);
  transform: translateX(28px);
}
:root[data-theme="light"] .theme .knob::after{
  content:"";
  position:absolute; left:50%; top:50%;
  width:2px; height:2px; background:#ffd166; border-radius:1px;
  transform:translate(-50%,-50%);
  box-shadow:
    0 -9px 0 0 #ffd166, 0 9px 0 0 #ffd166,
    9px 0 0 0 #ffd166, -9px 0 0 0 #ffd166,
    6.4px -6.4px 0 0 #ffd166, -6.4px -6.4px 0 0 #ffd166,
    6.4px  6.4px 0 0 #ffd166, -6.4px  6.4px 0 0 #ffd166;
}

"""

# ---------- Templates ----------
def header_html(base: str, brand_text: str | None = None, crumb_title: str | None = None) -> str:
    """Header fixed: 'CacheMissed Blog' + '/ [icon] Tên bài' (nếu có)."""
    txt = brand_text or BRAND
    doc_svg = """<svg class="docico" viewBox="0 0 24 24" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M14 2v6h6" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>"""
    crumb = f'<span class="brand-path"> <span class="sep">/</span> {doc_svg}<span class="crumb-txt">{crumb_title}</span></span>' if crumb_title else ""
    return f"""
<header class="site-head">
  <div class="head-inner">
    <a class="brand" href="{base}">
      <img class="logo logo-light" src="{base}images/logo-light.png" alt="logo">
      <img class="logo logo-dark"  src="{base}images/logo-dark.png"  alt="logo">
      <span class="txt">{txt}</span>
    </a>
    {crumb}
    <div class="spacer"></div>

    <label class="search" role="search" aria-label="Search site">
      <input id="q" placeholder="Search posts…" autocomplete="off">
      <button type="button" class="s-clear" id="qClear" aria-label="Clear">✕</button>
      <button type="button" class="s-ico-btn" id="qIcon" aria-label="Search">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </button>
    </label>

    <button class="theme" id="themeToggle" type="button" aria-pressed="false" title="Toggle theme">
      <span class="label label-dark">DARK</span>
      <span class="track"><span class="knob"></span></span>
      <span class="label label-light">LIGHT</span>
    </button>
  </div>
</header>
"""

INDEX_HTML = Template("""
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<link rel="stylesheet" href="{{ base }}style.css">
</head><body>
{{ header | safe }}

<div class="catbar">
  {% if pills %}<nav class="pills">{% for p in pills %}<a class="pill" href="{{ p.href }}">{{ p.label }}</a>{% endfor %}</nav>{% endif %}
</div>

<main>
  <div class="hr"></div>
  <div id="list">
  {% for p in posts %}
    <article class="post" data-title="{{ p.title | e }}">
      <div class="date">{{ p.date_human }}</div>
      <h2><a href="{{ p.url }}">{{ p.title }}</a></h2>
    </article>
  {% endfor %}
  </div>
</main>

<footer><div class="hr"></div><p>© {{ year }} • CacheMissed</p></footer>

<script>
(function(){const k='pref-theme',r=document.documentElement,b=document.getElementById('themeToggle');const s=localStorage.getItem(k);r.setAttribute('data-theme',(s==='dark'||s==='light')?s:'light');function x(){b.setAttribute('aria-pressed',r.getAttribute('data-theme')==='dark')}x();b.addEventListener('click',()=>{const c=r.getAttribute('data-theme')==='dark'?'light':'dark';r.setAttribute('data-theme',c);localStorage.setItem(k,c);x()});})();
(function(){const q=document.getElementById('q'),go=document.getElementById('qIcon'),cl=document.getElementById('qClear'),L=document.getElementById('list');if(!q||!L)return;function ap(){const t=q.value.trim().toLowerCase();L.querySelectorAll('.post').forEach(p=>{const h=p.dataset.title.toLowerCase().includes(t);p.style.display=h?'':'none'});q.parentElement.classList.toggle('has-text',t.length>0)}q.addEventListener('input',ap);go.addEventListener('click',()=>{ap();const f=[...L.querySelectorAll('.post')].find(p=>p.style.display!=='none');if(f){f.scrollIntoView({behavior:'smooth',block:'center'})}});cl.addEventListener('click',()=>{q.value='';ap();q.focus()});ap();})();
</script>
</body></html>
""".strip())

POST_HTML = Template("""
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<link rel="stylesheet" href="{{ base }}style.css">
<link rel="canonical" href="{{ canonical }}">
</head><body class="no-search">
{{ header | safe }}

<div class="post-wrap">
  <!-- TOC (left) -->
  <aside class="toc collapsed" id="toc">
    <div class="toc-title" id="tocTitle">{{ title }}</div>
    <nav id="tocList"></nav>
    <div class="toc-tools">
      <a href="#" id="tocToggle">Expand all</a>
      <a href="#" id="tocTop">Back to top</a>
      <a href="#" id="tocBottom">Go to bottom</a>
    </div>
  </aside>

  <!-- CONTENT (right) -->
  <article class="content">
    <h1>{{ title }}</h1>
    <div class="meta">{{ date_human }}{% if category %} • {{ category }}{% endif %}</div>
    <div class="md" id="postBody">{{ content | safe }}</div>
  </article>
</div>

<footer><div class="hr"></div><p style="max-width:var(--w);margin:0 auto 40px;padding:0 16px;color:var(--muted)">© {{ year }} • CacheMissed</p></footer>

<script>
(function(){const k='pref-theme',r=document.documentElement,b=document.getElementById('themeToggle');const s=localStorage.getItem(k);r.setAttribute('data-theme',(s==='dark'||s==='light')?s:'light');function x(){b.setAttribute('aria-pressed',r.getAttribute('data-theme')==='dark')}x();b.addEventListener('click',()=>{const c=r.getAttribute('data-theme')==='dark'?'light':'dark';r.setAttribute('data-theme',c);localStorage.setItem(k,c);x()});})();

(function(){
  const body = document.getElementById('postBody');
  if(!body) return;
  function slugify(s){
    return String(s).toLowerCase()
      .normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')
      .replace(/[^a-z0-9\\s-]/g,'').trim()
      .replace(/\\s+/g,'-').replace(/-+/g,'-');
  }
  const hs  = body.querySelectorAll('h1,h2,h3');
  const toc = document.getElementById('toc');
  const list= document.getElementById('tocList');
  if(!hs.length){ toc.style.display='none'; return; }

  const ul = document.createElement('ul');
  hs.forEach(h=>{
    const lvl = +h.tagName.substring(1);
    if(!h.id) h.id = slugify(h.textContent);
    const li = document.createElement('li'); li.className='lvl-'+lvl;
    const a  = document.createElement('a'); a.href = '#'+h.id; a.textContent = h.textContent;
    li.appendChild(a); ul.appendChild(li);
  });
  list.appendChild(ul);

  const btn = document.getElementById('tocToggle');
  function setLabel(){ btn.textContent = toc.classList.contains('collapsed') ? 'Expand all' : 'Collapse all'; }
  setLabel();
  btn.addEventListener('click', e=>{
    e.preventDefault(); toc.classList.toggle('collapsed'); setLabel();
  });
  document.getElementById('tocTop').addEventListener('click', e=>{
    e.preventDefault(); window.scrollTo({top:0,behavior:'smooth'});
  });
  document.getElementById('tocBottom').addEventListener('click', e=>{
    e.preventDefault(); window.scrollTo({top:document.body.scrollHeight,behavior:'smooth'});
  });
})();
</script>
</body></html>
""".strip())

CAT_HTML = Template("""
<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<link rel="stylesheet" href="{{ base }}style.css">
</head><body>
{{ header | safe }}

<main>
  <h1>{{ cat_name }}</h1>
  <div class="hr"></div>
</main>

<div class="catbar">
  {% if pills %}<nav class="pills">{% for p in pills %}<a class="pill" href="{{ p.href }}">{{ p.label }}</a>{% endfor %}</nav>{% endif %}
</div>

<main>
  <div id="list">
  {% for p in posts %}
    <article class="post" data-title="{{ p.title | e }}">
      <div class="date">{{ p.date_human }}</div>
      <h2><a href="{{ p.url }}">{{ p.title }}</a></h2>
    </article>
  {% endfor %}
  </div>
</main>

<footer><div class="hr"></div><p>© {{ year }} • CacheMissed</p></footer>

<script>
(function(){const k='pref-theme',r=document.documentElement,b=document.getElementById('themeToggle');const s=localStorage.getItem(k);r.setAttribute('data-theme',(s==='dark'||s==='light')?s:'light');function x(){b.setAttribute('aria-pressed',r.getAttribute('data-theme')==='dark')}x();b.addEventListener('click',()=>{const c=r.getAttribute('data-theme')==='dark'?'light':'dark';r.setAttribute('data-theme',c);localStorage.setItem(k,c);x()});})();
(function(){const q=document.getElementById('q'),go=document.getElementById('qIcon'),cl=document.getElementById('qClear'),L=document.getElementById('list');if(!q||!L)return;function ap(){const t=q.value.trim().toLowerCase();L.querySelectorAll('.post').forEach(p=>{const h=p.dataset.title.toLowerCase().includes(t);p.style.display=h?'':'none'});q.parentElement.classList.toggle('has-text',t.length>0)}q.addEventListener('input',ap);go.addEventListener('click',()=>{ap();const f=[...L.querySelectorAll('.post')].find(p=>p.style.display!=='none');if(f){f.scrollIntoView({behavior:'smooth',block:'center'})}});cl.addEventListener('click',()=>{q.value='';ap();q.focus()});ap();})();
</script>
</body></html>
""".strip())

# ---------- helpers ----------
def ensure_style(): (SITE/"style.css").write_text(STYLE_CSS, encoding="utf-8")

def copy_images():
    if not IMAGES.exists(): return
    dst = SITE / "images"
    dst.mkdir(parents=True, exist_ok=True)
    for p in IMAGES.rglob("*"):
        if p.is_file():
            rel = p.relative_to(IMAGES)
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst / rel)

def parse_date(meta_date, name_hint):
  if meta_date: return datetime.date.fromisoformat(str(meta_date)[:10])
  m = re.search(r"(\d{4})[-_](\d{2})[-_](\d{2})", name_hint)
  if m: y,mo,d = map(int,m.groups()); return datetime.date(y,mo,d)
  return datetime.date.today()

def human(d): return d.strftime("%Y %b %d")

def collect_categories(meta):
  cats=[]
  if meta.get("category"): cats.append(str(meta["category"]))
  if meta.get("categories"):
    c = meta["categories"]
    if isinstance(c,str): cats.append(c)
    else: cats.extend(c)
  return [x.strip() for x in cats if str(x).strip()]

# ---------- build ----------
def render_post(md_path: Path, slug_hint: str, entries: list, cats_map: dict):
  fm = frontmatter.load(md_path)
  html = markdown.markdown(fm.content, extensions=["extra","toc","tables","codehilite"])
  title = fm.get("title") or md_path.stem.replace("-"," ").title()
  d = parse_date(fm.get("date"), md_path.as_posix())
  date_human = human(d)
  slug = fm.get("slug") or slugify(slug_hint or title)
  out = OUT_POSTS / f"{slug}.html"
  out.parent.mkdir(parents=True, exist_ok=True)

  cats = collect_categories(fm.metadata)
  main_cat = cats[0] if cats else None
  post_url = f"{BASE_URL}posts/{out.name}"
  for c in cats:
    cats_map.setdefault(c, []).append({"title": title, "date": d, "date_human": date_human, "url": post_url})

  page = POST_HTML.render(
    title=title, date_human=date_human, content=html, category=main_cat,
    header=header_html(BASE_URL, brand_text="CacheMissed Blog", crumb_title=title),
    year=datetime.date.today().year,
    base=BASE_URL, canonical=urljoin(BASE_URL, f"posts/{out.name}")
  )
  out.write_text(page, encoding="utf-8")

  entries.append({"title": title, "date": d, "date_human": date_human,
                  "url": post_url, "categories": cats})

def build_all():
  ensure_style(); copy_images()
  entries=[]; cats_map={}
  for p in POSTS.rglob("*"):
    if p.is_file() and p.suffix.lower()==".md": render_post(p, p.stem, entries, cats_map)
    elif p.is_dir() and (p/"index.md").exists(): render_post(p/"index.md", p.name, entries, cats_map)

  entries.sort(key=lambda x:x["date"], reverse=True)

  unique_cats = sorted({c for e in entries for c in e["categories"]}) if entries else []
  pills = [{"href": f"{BASE_URL}category/{slugify(c)}.html", "label": c} for c in unique_cats]

  index = INDEX_HTML.render(
    title="CacheMissed Blog",
    header=header_html(BASE_URL, brand_text="CacheMissed Blog"),
    pills=pills,
    posts=entries,
    year=datetime.date.today().year,
    base=BASE_URL
  )
  (SITE/"index.html").write_text(index, encoding="utf-8")

  for cat, posts in cats_map.items():
    posts.sort(key=lambda x:x["date"], reverse=True)
    page = CAT_HTML.render(
      title=cat,
      header=header_html(BASE_URL, brand_text="CacheMissed Blog"),
      cat_name=cat,
      pills=pills,
      posts=posts,
      year=datetime.date.today().year,
      base=BASE_URL
    )
    (CAT_DIR/f"{slugify(cat)}.html").write_text(page, encoding="utf-8")

  # RSS
  items=[]
  for e in entries[:50]:
    items.append(f"""<item>
  <title><![CDATA[{e['title']}]]></title>
  <link>{e['url']}</link>
  <guid isPermaLink="false">{e['url']}</guid>
  <pubDate>{e['date'].strftime('%a, %d %b %Y 00:00:00 +0000')}</pubDate>
</item>""")
  feed=f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>CacheMissed Blog</title><link>{BASE_URL}</link><description>RSS</description>
{''.join(items)}
</channel></rss>"""
  (SITE/"feed.xml").write_text(feed.strip(), encoding="utf-8")

  # Sitemap + index.json
  urls=[BASE_URL]+[e["url"] for e in entries]
  urls+=[f"{BASE_URL}category/{slugify(c)}.html" for c in cats_map.keys()]
  sm=["<?xml version='1.0' encoding='UTF-8'?>","<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
  for u in urls: sm.append(f"<url><loc>{u}</loc></url>")
  sm.append("</urlset>")
  (SITE/"sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
  (SITE/"index.json").write_text(json.dumps([
    {"title":e["title"],"date":e["date"].isoformat(),"url":e["url"],"categories":e["categories"]} for e in entries
  ], ensure_ascii=False, indent=2), encoding="utf-8")

  print(f"Built {len(entries)} post(s), {len(cats_map)} category page(s) → {SITE}")

if __name__ == "__main__":
  build_all()
