"""Packaged educational animations for the existing Methods Atlas.

Rendering is a build-time task. Reading and exporting these assets requires no
image, plotting or Markdown dependency in an installed EchoTime wheel.
"""

from __future__ import annotations

import json
from functools import lru_cache
from html import escape
from pathlib import Path


FAMILY_LABELS = {
    "native": ("EchoTime comparison layer", "EchoTime 原生比较分项"),
    "lock-step": ("Aligned, pointwise comparison", "逐点比较"),
    "sliding": ("Shifts and lead–lag relationships", "平移与领先滞后"),
    "elastic": ("Elastic alignment and edit operations", "弹性对齐与编辑操作"),
    "kernel": ("Kernel constructions", "核函数构造"),
    "feature-based": ("Explicit features", "显式特征"),
    "model-based": ("Fitted dynamics and models", "动力学与模型"),
    "embedding": ("Representation and comparison", "表示与比较"),
}

DEFINITION_LABELS = {
    "echotime": ("Checked against EchoTime", "已与 EchoTime 计算核对"),
    "reference": ("Reference-formula demonstration", "参考公式演示"),
    "protocol": ("Specified illustrative protocol", "明确设定的流程示例"),
}


def animation_root() -> Path:
    return Path(__file__).with_name("data") / "method_animations"


@lru_cache(maxsize=1)
def animation_catalog() -> dict:
    path = animation_root() / "catalog.json"
    if not path.is_file():
        raise FileNotFoundError(
            "Missing method-animation assets. In a source checkout run "
            "python tools/build_method_animations.py; otherwise reinstall EchoTime."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def animation_assets() -> dict[str, bytes | str]:
    """Return the complete, self-contained asset subtree for a static export."""
    root = animation_root()
    animation_catalog()  # Fail explicitly on incomplete installations.
    return {
        "assets/method-animations/" + path.relative_to(root).as_posix():
        path.read_text(encoding="utf-8") if path.suffix == ".json" else path.read_bytes()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def animation_link(method_id: str) -> str:
    return f"<a class='animation-jump' href='#animation-{escape(method_id, quote=True)}'>Animated explanation / 动图详解</a>"


def _language_block(entry: dict, language: str) -> str:
    suffix = "zh" if language == "zh" else "en"
    definition = DEFINITION_LABELS[entry["definition"]][language == "zh"]
    steps = "".join(f"<li>{escape(step)}</li>" for step in entry[f"steps_{suffix}"])
    caveats = "".join(f"<li>{escape(item)}</li>" for item in entry[f"caveats_{suffix}"])
    heading = "计算步骤" if language == "zh" else "How the calculation works"
    boundary = "解释与使用边界" if language == "zh" else "Interpretation and limits"
    label = "示例性质" if language == "zh" else "Demonstration"
    return (
        f"<div data-animation-lang='{language}' lang='{'zh-CN' if language == 'zh' else 'en'}'>"
        f"<p class='animation-definition'><strong>{label}:</strong> {escape(definition)}</p>"
        f"<p>{escape(entry[f'intro_{suffix}'])}</p>"
        f"<h4>{heading}</h4><ol class='animation-steps'>{steps}</ol>"
        f"<h4>{boundary}</h4><ul>{caveats}</ul></div>"
    )


def _method_card(entry: dict, asset_prefix: str) -> str:
    method_id = entry["id"]
    media = f"{asset_prefix}media/{method_id}"
    result = entry["result"]
    sources = "; ".join(
        f"<a href='{escape(source['url'], quote=True)}'>{escape(source['label'])}</a>"
        for source in entry["sources"]
    )
    parameters = escape(json.dumps(entry["parameters"], ensure_ascii=False, indent=2))
    search = " ".join([method_id, entry["title"], entry["family"], entry["intro_en"], entry["intro_zh"]]).lower()
    definition = DEFINITION_LABELS[entry["definition"]][0]
    alt = f"{entry['title']}: static final state of the documented numerical example. {result['label']} = {result['value']:.6g}."
    return f"""
    <details class='animation-method' id='animation-{escape(method_id)}' data-search='{escape(search, quote=True)}'>
      <summary><strong>{escape(entry['title'])}</strong> <code>{escape(method_id)}</code><span class='animation-status'>{escape(definition)}</span></summary>
      <div class='animation-content'>
        <figure class='animation-figure'>
          <img src='{media}.png' data-poster='{media}.png' data-gif='{media}.gif' width='1000' height='650' loading='lazy' decoding='async' alt='{escape(alt, quote=True)}'>
          <figcaption>
            <button type='button' class='animation-play' aria-pressed='false' hidden>Play GIF / 播放</button>
            <a href='{media}.gif'>Open GIF / 打开动图</a>
            <a href='{media}.png'>Static image / 静态图</a>
            <a href='{asset_prefix}traces/{escape(method_id)}.json'>Inputs and trace / 输入与计算过程</a>
          </figcaption>
        </figure>
        <p class='animation-result'><strong>Illustrative {escape(result['label'])}:</strong> <code>{result['value']:.8g}</code> — {escape(result['detail'])}</p>
        <p><strong>EchoTime coverage:</strong> {escape(entry['echotime_status'])}{' · ' + escape(entry['echotime_api']) if entry.get('echotime_api') else ''}</p>
        <p class='formula-chip'>{escape(entry['formula'])}</p>
        {_language_block(entry, 'en')}
        {_language_block(entry, 'zh')}
        <details class='animation-parameters'><summary>Example parameters / 示例参数</summary><pre><code>{parameters}</code></pre></details>
        <p class='animation-sources'><strong>Definition sources / 定义来源:</strong> {sources}</p>
      </div>
    </details>"""


def method_animations_html(*, asset_prefix: str = "../assets/method-animations/") -> str:
    catalog = animation_catalog()
    entries = catalog["methods"]
    families = []
    for family, labels in FAMILY_LABELS.items():
        members = [entry for entry in entries if entry["family"] == family]
        if not members:
            continue
        cards = "".join(_method_card(entry, asset_prefix) for entry in members)
        families.append(
            f"<details class='animation-family' id='animation-family-{family}'>"
            f"<summary>{labels[0]} / {labels[1]} <span>{len(members)}</span></summary>{cards}</details>"
        )
    return f"""
    <section class='docs-card method-animations' id='method-animations'>
      <span class='pill blue'>Animated method explanations / 方法动图详解</span>
      <h2>Watch the calculation, then read its assumptions</h2>
      <p>Each of the {len(entries)} entries has a GIF, a static summary, four explanatory stages and a reproducible numerical trace. Inputs are small, synthetic teaching examples. Scores describe those examples and carry no performance ranking.</p>
      <p lang='zh-CN'>这里覆盖 10 个原生分项与 127 个方法条目。每项包含动图、静态总结、四步说明及可复现的计算过程。示例使用小规模合成序列，分数只描述对应示例。图中会标明当前实现、参考公式或具体流程设定。</p>
      <p>Animations stay still until requested. Play one at a time; Stop restores the static summary. / 动图默认静止；可逐项播放和停止。</p>
      <div class='animation-toolbar'>
        <label for='animation-search'>Find a method / 查找方法 <input id='animation-search' type='search' placeholder='DTW, lag, spectrum, 频谱…' autocomplete='off'></label>
        <div class='animation-language-controls' hidden><button type='button' data-set-language='en' aria-pressed='true'>English</button><button type='button' data-set-language='zh' aria-pressed='false'>中文</button></div>
      </div>
      <p id='animation-match-count' role='status' aria-live='polite'>{len(entries)} method explanations</p>
      <noscript><p>Open a family and method below. Both languages and the static images are available; use “Open GIF” to play the animation.</p></noscript>
      {''.join(families)}
    </section>
    {ANIMATION_SCRIPT}
    """


ANIMATION_CSS = """
.method-animations { margin: 24px 0; }
.method-animations, .animation-method { scroll-margin-top:140px; }
.animation-toolbar { display:flex; flex-wrap:wrap; align-items:end; gap:16px; margin-top:20px; }
.animation-toolbar label { display:grid; gap:6px; flex:1; min-width:220px; font-weight:600; }
.animation-toolbar input { width:100%; box-sizing:border-box; padding:12px; font:inherit; color:var(--text-900, #fff); background:var(--surface-strong, #111); border:1px solid var(--border, #ccd4de); border-radius:8px; }
.method-animations button { cursor:pointer; font:inherit; border:1px solid var(--border, #ccd4de); border-radius:8px; padding:9px 13px; background:#e6f2f2; color:#123b46; }
.method-animations button[aria-pressed='true'] { background:#173c50; color:#fff; }
.method-animations :focus-visible { outline:3px solid #188aa1; outline-offset:3px; }
.animation-family { border-top:1px solid var(--border, #ccd4de); padding:14px 0; }
.animation-family > summary { cursor:pointer; font-weight:700; font-size:1.04rem; }
.animation-family > summary span { margin-left:8px; font-weight:400; }
.animation-method { margin:12px 0 0; border:1px solid var(--border, #ccd4de); border-radius:10px; overflow:hidden; }
.animation-method > summary { cursor:pointer; padding:15px; line-height:1.65; }
.animation-method > summary code { font-size:0.85rem; overflow-wrap:anywhere; margin-left:8px; }
.animation-status { display:block; margin-left:20px; font-size:0.78rem; font-weight:400; color:var(--text-600, #526377); }
.animation-content { padding:0 18px 18px; }
.animation-figure { margin:8px 0 18px; }
.animation-figure img { display:block; width:100%; max-width:1000px; height:auto; border-radius:8px; background:#101e2b; }
.animation-figure figcaption { display:flex; flex-wrap:wrap; align-items:center; gap:10px 18px; margin-top:10px; font-size:0.88rem; }
.animation-result { border-left:3px solid #2c9eab; padding-left:12px; }
.animation-steps li { padding:3px 0; }
.animation-parameters pre { overflow-x:auto; white-space:pre-wrap; overflow-wrap:anywhere; }
.animation-sources { font-size:0.85rem; overflow-wrap:anywhere; }
.animation-content a { text-decoration:underline; text-underline-offset:3px; }
.animation-jump { display:inline-block; margin-top:7px; font-size:0.85rem; }
.method-animations[data-enhanced][data-language='en'] [data-animation-lang='zh'],
.method-animations[data-enhanced][data-language='zh'] [data-animation-lang='en'] { display:none; }
.method-animations [hidden] { display:none !important; }
@media (max-width:650px) { .method-animations, .animation-method { scroll-margin-top:220px; } .animation-content { padding:0 8px 12px; } .animation-method > summary { padding:12px; } }
"""


ANIMATION_SCRIPT = """<script>
(() => {
  const root = document.getElementById('method-animations');
  if (!root) return;
  root.dataset.enhanced = 'true';
  root.dataset.language = 'en';
  const cards = Array.from(root.querySelectorAll('.animation-method'));
  const families = Array.from(root.querySelectorAll('.animation-family'));
  const status = root.querySelector('#animation-match-count');
  function stop(card) {
    const image = card.querySelector('img[data-gif]');
    const button = card.querySelector('.animation-play');
    if (button.getAttribute('aria-pressed') === 'true') image.src = image.dataset.poster;
    button.setAttribute('aria-pressed', 'false');
    button.textContent = 'Play GIF / 播放';
  }
  function stopAll() { cards.forEach(stop); }
  cards.forEach(card => {
    const button = card.querySelector('.animation-play');
    const image = card.querySelector('img[data-gif]');
    button.hidden = false;
    button.addEventListener('click', () => {
      const playing = button.getAttribute('aria-pressed') === 'true';
      stopAll();
      if (!playing) {
        image.src = image.dataset.gif;
        button.setAttribute('aria-pressed', 'true');
        button.textContent = 'Stop / 停止';
      }
    });
    card.addEventListener('toggle', () => { if (!card.open) stop(card); });
  });
  families.forEach(family => family.addEventListener('toggle', () => {
    if (!family.open) family.querySelectorAll('.animation-method').forEach(stop);
  }));
  root.querySelector('.animation-language-controls').hidden = false;
  root.querySelectorAll('[data-set-language]').forEach(button => {
    button.addEventListener('click', () => {
      root.dataset.language = button.dataset.setLanguage;
      root.querySelectorAll('[data-set-language]').forEach(item => {
        item.setAttribute('aria-pressed', String(item === button));
      });
    });
  });
  const search = root.querySelector('#animation-search');
  search.addEventListener('input', () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    cards.forEach(card => {
      card.hidden = !card.dataset.search.includes(query);
      if (card.hidden) stop(card); else visible++;
    });
    families.forEach(family => {
      family.hidden = !Array.from(family.querySelectorAll('.animation-method')).some(card => !card.hidden);
      if (query && !family.hidden) family.open = true;
    });
    status.textContent = visible + ' / ' + cards.length + ' method explanations / 方法';
  });
  function openHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (!id.startsWith('animation-')) return;
    const target = document.getElementById(id);
    if (!target || !root.contains(target)) return;
    search.value = '';
    search.dispatchEvent(new Event('input'));
    for (let node = target; node && node !== root; node = node.parentElement) {
      if (node.tagName === 'DETAILS') node.open = true;
    }
    requestAnimationFrame(() => target.scrollIntoView({block:'start'}));
  }
  window.addEventListener('hashchange', openHash);
  openHash();
  document.addEventListener('visibilitychange', () => { if (document.hidden) stopAll(); });
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (motion.addEventListener) motion.addEventListener('change', stopAll);
})();
</script>"""
