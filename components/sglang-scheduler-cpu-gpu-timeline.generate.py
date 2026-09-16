"""Generate the SGLang scheduler CPU/GPU timeline artifact (self-contained HTML+SVG).

Model (illustrative units, grounded in scheduler.py:1906 event_loop_normal and
scheduler.py:1941 event_loop_overlap):
  GPU forward+sample per batch = 6 units, CPU ingest+plan = 2, CPU process result = 2, launch = 0.5.
Overlap loop order per iteration: ingest/plan -> run_batch (launch only, appends to result_queue)
-> pop_and_process() of the PREVIOUS batch, which blocks on that batch's copy_done event and then
runs process_batch_result while the GPU computes the current batch.
"""
import html

PX_PER_UNIT = 18.0
LABEL_W = 112.0
GAP = 12.0
CHART_X0 = LABEL_W + GAP
PAD_R = 104.0

ROW_H = 34.0
ROW_GAP = 16.0

KIND_STYLE = {
    "plan":    {"fill": "var(--b-plan)",    "stroke": "var(--b-plan)",    "text": "var(--on-solid)"},
    "launch":  {"fill": "var(--b-launch)",  "stroke": "var(--b-launch)",  "text": "var(--on-solid)"},
    "wait":    {"fill": "url(#hatch-wait)", "stroke": "var(--b-wait)",    "text": "var(--ink-wait)"},
    "process": {"fill": "var(--b-process)", "stroke": "var(--b-process)", "text": "var(--on-solid)"},
    "gpu":     {"fill": "var(--b-gpu)",     "stroke": "var(--b-gpu)",     "text": "var(--on-solid)"},
    "idle":    {"fill": "url(#hatch-idle)", "stroke": "var(--b-idle)",    "text": "var(--ink-idle)"},
}

CPU = "CPU \u00b7 Scheduler"
GPU = "GPU \u00b7 \u524d\u5411 + \u91c7\u6837"

SYNC = {
    "title": "① \u540c\u6b65\uff1aevent_loop_normal\uff08scheduler.py:1906\uff09",
    "rows": [
        {"label": CPU, "bars": [
            (0, 2, "plan", "\u7ec4A"), (2, 6, "wait", "\u7b49 A\uff08\u963b\u585e\uff09"), (8, 2, "process", "\u5904\u7406A"),
            (10, 2, "plan", "\u7ec4B"), (12, 6, "wait", "\u7b49 B\uff08\u963b\u585e\uff09"), (18, 2, "process", "\u5904\u7406B"),
            (20, 2, "plan", "\u7ec4C"), (22, 6, "wait", "\u7b49 C\uff08\u963b\u585e\uff09"), (28, 2, "process", "\u5904\u7406C"),
        ]},
        {"label": GPU, "bars": [
            (0, 2, "idle", "\u7a7a\u8f6c"), (2, 6, "gpu", "\u7b97A"), (8, 4, "idle", "\u7a7a\u8f6c"),
            (12, 6, "gpu", "\u7b97B"), (18, 4, "idle", "\u7a7a\u8f6c"),
            (22, 6, "gpu", "\u7b97C"), (28, 2, "idle", "\u7a7a\u8f6c"),
        ]},
    ],
    "span": 30.0,
    "notes": [
        (2, 6, "run_batch \u8fd4\u56de\u65f6 GPU \u5df2\u7b97\u5b8c", 0),
        (8, 4, "GPU \u7a7a\u8f6c 12/30 \u5355\u4f4d", 1),
    ],
}

OVERLAP = {
    "title": "② Overlap\uff1aevent_loop_overlap\uff08scheduler.py:1941\uff09",
    "rows": [
        {"label": CPU, "bars": [
            (0, 2, "plan", "\u7ec4A"), (2, 0.5, "launch", ""),
            (2.5, 2, "plan", "\u7ec4B"), (4.5, 0.5, "launch", ""),
            (5, 3.5, "wait", "\u7b49A\u8fd4\u56de"), (8.5, 2, "process", "\u5904\u7406A"),
            (10.5, 2, "plan", "\u7ec4C"), (12.5, 0.5, "launch", ""),
            (13, 1.5, "wait", "\u7b49B"), (14.5, 2, "process", "\u5904\u7406B"),
            (16.5, 4, "wait", "\u7b49C\u8fd4\u56de"), (20.5, 2, "process", "\u5904\u7406C"),
        ]},
        {"label": GPU, "bars": [
            (0, 2.5, "idle", "\u7a7a\u8f6c"), (2.5, 6, "gpu", "\u7b97A"), (8.5, 6, "gpu", "\u7b97B"), (14.5, 6, "gpu", "\u7b97C"),
        ]},
    ],
    "span": 22.5,
    "notes": [
        (4.5, 0.5, "launch B \u65e9\u4e8e\u7b97A \u7ed3\u675f \u2192 GPU \u4e0d\u7a7a\u8f6c", 0),
        (8.5, 2, "\u5904\u7406A \u4e0e \u7b97B \u91cd\u53e0", 1),
        (16.5, 4, "\u7b49\u5f85\u4e0a\u4e00\u6279\uff08copy_done\uff09", 1),
    ],
}

CHARTS = [SYNC, OVERLAP]
AXIS_MAX = 30.0


def x_of(t):
    return CHART_X0 + t * PX_PER_UNIT


def fmt(v):
    return "%g" % v


def bars_svg(row, y):
    out = []
    for start, dur, kind, text in row["bars"]:
        style = KIND_STYLE[kind]
        x, w = x_of(start), dur * PX_PER_UNIT
        if w < 1.5:
            continue
        out.append(
            f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(ROW_H)}" rx="4" '
            f'fill="{style["fill"]}" stroke="{style["stroke"]}"/>'
        )
        if not text:
            continue
        if w >= 24:
            out.append(
                f'<text class="bar-label" x="{fmt(x + w / 2)}" y="{fmt(y + ROW_H / 2 + 4)}" '
                f'fill="{style["text"]}">{html.escape(text)}</text>'
            )
        else:
            out.append(
                f'<text class="bar-tip" x="{fmt(x + w / 2)}" y="{fmt(y + ROW_H + 12)}">{html.escape(text)}</text>'
            )
    return "\n".join(out)


def panel_svg(panel, y0):
    out = [f'<text class="panel-title" x="0" y="{fmt(y0)}">{html.escape(panel["title"])}</text>']
    y = y0 + 18
    for row in panel["rows"]:
        out.append(f'<text class="row-label" x="0" y="{fmt(y + ROW_H / 2 + 4)}">{html.escape(row["label"])}</text>')
        out.append(bars_svg(row, y))
        y += ROW_H + ROW_GAP
    y -= ROW_GAP

    span_x = x_of(panel["span"])
    out.append(f'<line class="span-guide" x1="{fmt(span_x)}" y1="{fmt(y0 + 4)}" x2="{fmt(span_x)}" y2="{fmt(y + 6)}"/>')
    out.append(f'<text class="span-label" x="{fmt(span_x + 8)}" y="{fmt(y0 + 12)}">{fmt(panel["span"])} \u5355\u4f4d</text>')

    for i, (start, dur, text, row) in enumerate(panel["notes"]):
        ny = y + 20 + row * 17
        out.append(
            f'<line class="note-guide" x1="{fmt(x_of(start))}" y1="{fmt(y + 8)}" x2="{fmt(x_of(start + dur))}" y2="{fmt(y + 8)}"/>'
        )
        out.append(f'<text class="note-label" x="{fmt(x_of(start + dur / 2))}" y="{fmt(ny)}">{html.escape(text)}</text>')
    return "\n".join(out), y + 20 + (max(n[3] for n in panel["notes"]) + 1) * 17


def build_svg():
    body, y = [], 30.0
    for i, panel in enumerate(CHARTS):
        if i:
            y += 28.0
        markup, bottom = panel_svg(panel, y)
        body.append(markup)
        y = bottom
    axis_y = y + 16
    total_w = x_of(AXIS_MAX) + PAD_R
    total_h = axis_y + 34
    ticks = []
    t = 0.0
    while t <= AXIS_MAX:
        big = abs(t % 5) < 1e-9
        ticks.append(
            f'<line class="tick" x1="{fmt(x_of(t))}" y1="{fmt(axis_y)}" x2="{fmt(x_of(t))}" y2="{fmt(axis_y + (8 if big else 5))}"/>'
        )
        if big:
            ticks.append(f'<text class="tick-label" x="{fmt(x_of(t))}" y="{fmt(axis_y + 22)}">{fmt(t)}</text>')
        t += 1.0
    return f'''<svg class="timeline" viewBox="0 0 {fmt(total_w)} {fmt(total_h)}" role="img"
     aria-label="SGLang Scheduler \u540c\u6b65\u4e0e overlap \u4e8b\u4ef6\u5faa\u73af\u7684 CPU GPU \u65f6\u95f4\u7ebf">
  <defs>
    <pattern id="hatch-wait" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="7" height="7" fill="var(--b-wait-bg)"/>
      <line x1="0" y1="0" x2="0" y2="7" stroke="var(--b-wait)" stroke-width="2.4"/>
    </pattern>
    <pattern id="hatch-idle" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="7" height="7" fill="var(--b-idle-bg)"/>
      <line x1="0" y1="0" x2="0" y2="7" stroke="var(--b-idle)" stroke-width="2"/>
    </pattern>
  </defs>
{chr(10).join(body)}
  <line class="axis" x1="{fmt(CHART_X0)}" y1="{fmt(axis_y)}" x2="{fmt(x_of(AXIS_MAX))}" y2="{fmt(axis_y)}"/>
  {chr(10).join(ticks)}
  <text class="axis-label" x="{fmt(x_of(AXIS_MAX) + 14)}" y="{fmt(axis_y + 4)}">\u65f6\u95f4 \u2192</text>
</svg>'''


PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scheduler \u540c\u6b65 / Overlap \u4e8b\u4ef6\u5faa\u73af\uff1aCPU\u2013GPU \u65f6\u95f4\u7ebf</title>
<style>
  :root {
    color-scheme: light dark;
    --bg: #f6f7f9; --panel: #ffffff; --border: #e3e6ea; --ink: #16181d; --muted: #6b7280;
    --accent: #0891b2; --chip: #f1f3f5;
    --b-plan: #0891b2; --b-launch: #0e7490; --b-wait: #d97706; --b-wait-bg: #fef3c7;
    --b-process: #7c3aed; --b-gpu: #ea580c; --b-idle: #9ca3af; --b-idle-bg: #f3f4f6;
    --on-solid: #ffffff; --ink-wait: #92400e; --ink-idle: #4b5563;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1216; --panel: #161a20; --border: #262b33; --ink: #e8eaed; --muted: #9aa1ab;
      --accent: #22d3ee; --chip: #1e232b;
      --b-plan: #22d3ee; --b-launch: #0e7490; --b-wait: #f59e0b; --b-wait-bg: #2a2113;
      --b-process: #a78bfa; --b-gpu: #fb923c; --b-idle: #6b7280; --b-idle-bg: #1c2128;
      --on-solid: #08111a; --ink-wait: #fcd34d; --ink-idle: #9aa1ab;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 48px 24px 64px; background: var(--bg); color: var(--ink); line-height: 1.6;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", Roboto, Helvetica, Arial, sans-serif;
  }
  main { max-width: 1060px; margin: 0 auto; }
  h1 { margin: 0 0 8px; font-size: 26px; letter-spacing: -0.01em; }
  .lede { margin: 0 0 6px; color: var(--muted); font-size: 13.5px; }
  code {
    background: var(--chip); border-radius: 4px; padding: 1px 6px;
    font-family: ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, monospace; font-size: 12.5px;
  }
  .stage { margin: 26px 0 16px; padding: 20px 24px 12px; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }
  svg.timeline { width: 100%; height: auto; display: block; }
  .panel-title { font-size: 13.5px; font-weight: 700; fill: var(--ink); }
  .row-label { font-size: 12px; fill: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  .bar-label { font-size: 11px; text-anchor: middle; font-weight: 600; }
  .bar-tip { font-size: 10px; text-anchor: middle; fill: var(--muted); }
  .span-guide { stroke: var(--border); stroke-width: 1; stroke-dasharray: 3 3; }
  .span-label { font-size: 11px; fill: var(--muted); font-weight: 600; }
  .note-guide { stroke: var(--accent); stroke-width: 1; stroke-dasharray: 2 2; opacity: .8; }
  .note-label { font-size: 10.5px; fill: var(--accent); text-anchor: middle; }
  .axis { stroke: var(--border); stroke-width: 1.2; }
  .tick { stroke: var(--border); stroke-width: 1; }
  .tick-label { font-size: 10px; fill: var(--muted); text-anchor: middle; }
  .axis-label { font-size: 10.5px; fill: var(--muted); }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 2px 0 0; padding: 0; list-style: none; font-size: 12.5px; color: var(--muted); }
  .legend li { display: flex; align-items: center; gap: 7px; }
  .swatch { width: 14px; height: 10px; border-radius: 3px; display: inline-block; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; margin-top: 22px; }
  .card { padding: 16px 18px; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; }
  .card h3 { margin: 0 0 8px; font-size: 14px; }
  .card ul { margin: 0; padding-left: 18px; font-size: 12.5px; color: var(--muted); }
  .card li { margin-bottom: 5px; }
  .note { margin-top: 18px; color: var(--muted); font-size: 12.5px; }
  footer { margin-top: 26px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12.5px; }
  footer a { color: var(--accent); }
</style>
</head>
<body>
<main>
  <h1>Scheduler \u540c\u6b65 / Overlap \u4e8b\u4ef6\u5faa\u73af\uff1aCPU\u2013GPU \u65f6\u95f4\u7ebf</h1>
  <p class="lede">
    \u6a2a\u8f74\u4e3a\u65f6\u95f4\uff0c\u4e24\u4e2a\u9762\u677f\u5171\u7528\u540c\u4e00\u523b\u5ea6\u3001\u540c\u4e00\u8d77\u70b9\uff1a\u4e0a\u9762\u662f <code>event_loop_normal</code>\uff0c\u4e0b\u9762\u662f <code>event_loop_overlap</code>\uff1b\u5404 3 \u6279\uff08A/B/C\uff09\u3002
  </p>
  <p class="lede">
    \u540c\u8272\u5757 = CPU \u5360\u7528\uff1b\u6a59\u8272 = GPU \u524d\u5411 + \u91c7\u6837\uff1b\u7eb1\u7eb9 = \u7b49\u5f85\uff08CPU \u963b\u585e / GPU \u7a7a\u8f6c\uff09\u3002
  </p>

  <div class="stage">
__SVG__
  </div>
  <ul class="legend">
    <li><span class="swatch" style="background: var(--b-plan)"></span>\u6536\u4e0e\u7ec4\u6279\uff08ingest_requests / get_next_batch_to_run\uff09</li>
    <li><span class="swatch" style="background: var(--b-launch)"></span>launch\uff08run_batch \u4ec5\u4e0b\u53d1\uff09</li>
    <li><span class="swatch" style="background: var(--b-wait)"></span>CPU \u963b\u585e\u7b49\u5f85</li>
    <li><span class="swatch" style="background: var(--b-process)"></span>\u5904\u7406\u7ed3\u679c\uff08process_batch_result\uff09</li>
    <li><span class="swatch" style="background: var(--b-gpu)"></span>GPU \u524d\u5411 + \u91c7\u6837</li>
    <li><span class="swatch" style="background: var(--b-idle)"></span>GPU \u7a7a\u8f6c</li>
  </ul>

  <div class="cards">
    <div class="card">
      <h3>\u4ee3\u7801\u5bf9\u7167</h3>
      <ul>
        <li>\u540c\u6b65\uff1a<code>result = self.run_batch(batch)</code> \u8fd4\u56de\u65f6 GPU \u5df2\u7b97\u5b8c\uff0c\u968f\u540e <code>process_batch_result</code></li>
        <li>Overlap\uff1a<code>run_batch</code> \u53ea\u5728 forward_stream \u4e0a launch\uff0c\u7acb\u5373\u8fd4\u56de\uff0c\u7ed3\u679c\u5165 <code>result_queue</code></li>
        <li>\u540c\u4e00\u8fed\u4ee3\u5185\u7684 <code>pop_and_process()</code> \u5904\u7406\u4e0a\u4e00\u6279\uff08\u6b64\u65f6 GPU \u5728\u7b97\u5f53\u524d\u6279\uff09</li>
        <li>\u7b49\u5f85\u70b9\uff1a<code>process_batch_result</code> \u5185\u90e8\u5bf9 <code>result.copy_done.synchronize()</code></li>
      </ul>
    </div>
    <div class="card">
      <h3>\u4e3a\u4ec0\u4e48\u5b83\u80fd\u91cd\u53e0</h3>
      <ul>
        <li>\u4e24\u6761 CUDA stream\uff1a\u8c03\u5ea6\u4fa7 <code>schedule_stream</code> \u4e0e\u524d\u5411 <code>forward_stream</code></li>
        <li>\u6bcf\u8f6e\u53ea\u9700 CPU \u5b8c\u6210\u201c\u6536\u4ef6 + \u7ec4\u6279 + launch\u201d\uff0c\u603b\u91cf\u5c0f\u4e8e\u4e00\u6279 GPU \u8ba1\u7b97\u65f6\u95f4\uff0cGPU \u5c31\u4e0d\u4f1a\u65ad\u6599</li>
        <li>\u6bcf\u8f6e <code>_apply_war_barrier()</code> \u4fdd\u8bc1\u8c03\u5ea6\u4fa7\u4e0b\u4e00\u6b21\u5199\u5165\u4e0d\u8d8a\u8fc7\u524d\u5411\u7684\u8bfb</li>
      </ul>
    </div>
    <div class="card">
      <h3>\u4f55\u65f6\u9000\u56de\u540c\u6b65</h3>
      <ul>
        <li>\u9996\u6279\u65e0\u53ef\u91cd\u53e0\uff1b\u65e0 batch \u65f6\u8d70 <code>on_idle()</code></li>
        <li>\u8fde\u7eed\u4e24\u4e2a prefill \u6279\u4f1a\u88ab <code>is_disable_overlap_for_batch</code> \u62c9\u56de\u540c\u6b65\uff08\u6362 TTFT\uff09</li>
        <li>\u9700\u8981 grammar \u540c\u6b65\u7684\u6295\u673a\u573a\u666f\u540c\u6837\u4e0d\u91cd\u53e0</li>
      </ul>
    </div>
  </div>

  <p class="note">
    \u523b\u5ea6\u4e3a\u793a\u610f\u503c\uff08\u4e00\u6279 GPU \u524d\u5411 + \u91c7\u6837 = 6 \u5355\u4f4d\uff0cCPU \u6536\u4e0e\u7ec4\u6279 = 2\u3001\u5904\u7406\u7ed3\u679c = 2\u3001launch = 0.5\uff09\uff0c
    \u7528\u4e8e\u8bf4\u660e\u91cd\u53e0\u5173\u7cfb\u800c\u975e\u5b9e\u6d4b\u8017\u65f6\uff1b\u771f\u5b9e\u6bd4\u4f8b\u53d6\u51b3\u4e8e\u6a21\u578b\u3001batch size \u4e0e prefill/decode \u6bd4\u4f8b\u3002
    \u884c\u4e3a\u4f9d\u636e <code>sgl-project/sglang @ bdf8886a</code>\u3002
  </p>

  <footer>
    \u5355\u6587\u4ef6\u79bb\u7ebf\u53ef\u6253\u5f00\uff0c\u968f\u7cfb\u7edf\u6df1/\u6d45\u8272\u3002
    \u4f5c\u4e3a <a href="https://github.com/tt-a1i/archify">Archify</a> \u56fe\u96c6\u7684\u8865\u5145\uff1aArchify \u4e94\u79cd\u56fe\u578b\u4e2d\u6700\u63a5\u8fd1\u7684\u662f sequence\uff08\u65f6\u95f4\u8f74\u5411\u4e0b\uff0c\u7528 activation \u8868\u8017\u65f6\uff09\uff0c\u6a2a\u5411\u7518\u7279\u56fe\u9700\u81ea\u5b9a\u4e49\u3002
  </footer>
</main>
</body>
</html>
"""

if __name__ == "__main__":
    svg = build_svg()
    out = PAGE.replace("__SVG__", svg)
    path = "sglang-scheduler-cpu-gpu-timeline.html"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote", path, len(out), "bytes")
