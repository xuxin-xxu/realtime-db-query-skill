#!/usr/bin/env python3
"""
Chart generation utilities for db-query skill.
Auto-installs matplotlib + CJK fonts if needed (user-level, no sudo), then generates charts.

Supports:
- Bar chart (vertical/horizontal)
- Pie chart
- Line chart
"""

import os
import sys
import urllib.request

# ── Image Generation Only (Delivery delegated to OpenClaw Agent) ─────────────


# ── Auto-install matplotlib + CJK fonts (user-level, no sudo) ─────────────

def _ensure_matplotlib():
    """Check and auto-install matplotlib if not available."""
    try:
        import matplotlib
        return True
    except ImportError:
        print("📦 Installing matplotlib...", file=sys.stderr)
        subprocess_run_quiet([sys.executable, "-m", "pip", "install", "matplotlib", "--break-system-packages", "-q"])
        return True


def _ensure_cjk_fonts():
    """
    Ensure a CJK font is available for matplotlib.
    
    Strategy (tiered, user-level only — NO sudo/apt-get):
      1. Check common system font paths.
      2. Check user-local font directory (~/.local/share/fonts).
      3. Download Noto Sans CJK SC OTF from GitHub if missing.
    
    This replaces the old sudo apt-get install fonts-noto-cjk approach.
    """
    system_font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    if any(os.path.exists(p) for p in system_font_paths):
        return

    # Check user-local fonts directory
    user_font_dir = os.path.expanduser("~/.local/share/fonts")
    user_font_ttc = os.path.join(user_font_dir, "NotoSansCJK-Regular.ttc")
    user_font_otf = os.path.join(user_font_dir, "NotoSansCJKsc-Regular.otf")

    if os.path.exists(user_font_ttc) or os.path.exists(user_font_otf):
        return

    # Download from official Noto CJK GitHub release (OTF, Simplified Chinese)
    # No sudo required — user-writable destination
    os.makedirs(user_font_dir, exist_ok=True)
    font_url_regular = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
    font_url_bold = "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Bold.otf"
    user_font_bold_otf = os.path.join(user_font_dir, "NotoSansCJKsc-Bold.otf")
    
    print(f"📦 Downloading Noto Sans CJK regular & bold fonts (~60MB, first-time only)...", file=sys.stderr)
    try:
        urllib.request.urlretrieve(font_url_regular, user_font_otf)
        urllib.request.urlretrieve(font_url_bold, user_font_bold_otf)
        print(f"✅ Fonts downloaded to {user_font_dir}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Font download failed: {e}", file=sys.stderr)
        # Fallback: try a smaller subset font
        try:
            fallback_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJK-Regular.otf"
            fallback_bold_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJK-Bold.otf"
            urllib.request.urlretrieve(fallback_url, user_font_otf)
            urllib.request.urlretrieve(fallback_bold_url, user_font_bold_otf)
        except Exception:
            print("⚠️ Could not download CJK font. Chinese characters may not render correctly.", file=sys.stderr)


def subprocess_run_quiet(cmd: list, **kwargs):
    """Run subprocess without sudo, suppressing output."""
    import subprocess
    kwargs.setdefault("check", True)
    kwargs.setdefault("capture_output", True)
    return subprocess.run(cmd, **kwargs)


def ensure_dependencies():
    """Ensure all chart dependencies are installed."""
    _ensure_matplotlib()
    _ensure_cjk_fonts()


# ── Chart rendering ─────────────────────────────────────────────────────────

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import to_rgba

# Find a usable CJK font (system → user-local)
_font_search_paths = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    os.path.expanduser("~/.local/share/fonts/NotoSansCJK-Regular.ttc"),
    os.path.expanduser("~/.local/share/fonts/NotoSansCJKsc-Regular.otf"),
    os.path.expanduser("~/.local/share/fonts/NotoSansCJK-Bold.ttc"),
]

_cjk_font = None
for _path in _font_search_paths:
    if os.path.exists(_path):
        _cjk_font = _path
        break

_font_prop = fm.FontProperties(fname=_cjk_font) if _cjk_font else None
_font_bold_prop = fm.FontProperties(fname=_cjk_font.replace("Regular","Bold")) if _cjk_font and "Regular" in _cjk_font else None

plt.rcParams['axes.unicode_minus'] = False


def _py_str(val):
    """Coerce a Java String (or any non-str) to Python str."""
    if val is None:
        return None
    if hasattr(val, '__str__'):
        return str(val)
    return val


def _to_float(val):
    """Safely convert a value to float."""
    if val is None:
        return 0.0
    try:
        return float(_py_str(val))
    except (ValueError, TypeError):
        return 0.0


def _get_font_prop(size: int = 12, bold: bool = False):
    """Get a FontProperties object for CJK rendering."""
    if _cjk_font is None:
        return None
    if bold and _font_bold_prop:
        fp = _font_bold_prop
    else:
        fp = _font_prop
    if fp:
        fp.set_size(size)
    return fp


# ── Public API ─────────────────────────────────────────────────────────────

CHART_DIR = None  # Set dynamically at call time


def _get_chart_dir():
    global CHART_DIR
    if CHART_DIR is None:
        # Infer from this file's location: skills/db-query/scripts/chart_utils.py
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        CHART_DIR = skill_dir
    return CHART_DIR


def render_bar_chart(
    labels: list,
    values: list,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    color: str = "#4A90D9",
    orientation: str = "vertical",
    sort_desc: bool = True,
    output_path: str = None,
    bg_color: str = "white",
) -> str:
    ensure_dependencies()

    # Sort if requested — high to low
    if sort_desc:
        paired = sorted(zip(values, labels), key=lambda x: _to_float(x[0]), reverse=True)
        values, labels = zip(*paired)
        values = list(values)
        labels = list(labels)
    else:
        values = list(values)
        labels = list(labels)

    display_labels = [l if _to_float(v) > 0 else f"{l} (无数据)" for l, v in zip(labels, values)]
    display_values = [_to_float(v) for v in values]

    colors = []
    for i, v in enumerate(display_values):
        if v <= 0:
            colors.append('#DDDDDD')
        elif i == 0:
            colors.append('#FFD700')
        elif i == 1:
            colors.append('#C0C0C0')
        elif i == 2:
            colors.append('#CD7F32')
        else:
            colors.append('#4A90D9')

    chart_dir = _get_chart_dir()
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    if orientation == "horizontal":
        y = range(len(display_labels))
        bars = ax.barh(y, display_values, color=colors, height=0.6, edgecolor='white')
        ax.set_yticks(y)
        ax.set_yticklabels(display_labels, fontproperties=_get_font_prop(11), color='#333333')
        ax.set_xlabel(ylabel or "Value", fontproperties=_get_font_prop(12), color='#333333')
        ax.set_xlim(0, max(display_values) * 1.15 if display_values else 10)
        for bar, val in zip(bars, display_values):
            if val > 0:
                ax.text(bar.get_width() + max(display_values) * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f'{val:,.2f}', va='center', ha='left',
                        fontsize=11, fontweight='bold', color='#333333',
                        fontproperties=_get_font_prop(11))
            else:
                ax.text(5, bar.get_y() + bar.get_height() / 2,
                        '无数据', va='center', ha='left',
                        fontsize=10, color='#999999', fontproperties=_get_font_prop(10))
    else:
        x = range(len(display_labels))
        bars = ax.bar(x, display_values, color=colors, width=0.6, edgecolor='white')
        ax.set_xticks(x)
        ax.set_xticklabels(display_labels, fontproperties=_get_font_prop(11), color='#333333')
        ax.set_ylabel(ylabel or "Value", fontproperties=_get_font_prop(12), color='#333333')
        ax.set_ylim(0, max(display_values) * 1.2 if display_values else 10)
        for bar, val in zip(bars, display_values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(display_values) * 0.01,
                        f'{val:,.2f}', ha='center', va='bottom',
                        fontsize=11, fontweight='bold', color='#333333',
                        fontproperties=_get_font_prop(11))
            else:
                ax.text(bar.get_x() + bar.get_width() / 2, 5,
                        '无数据', ha='center', va='bottom',
                        fontsize=10, color='#999999', fontproperties=_get_font_prop(10))

    ax.set_title(title, fontsize=15, fontweight='bold',
                 color='#222222', fontproperties=_get_font_prop(15, bold=True), pad=12)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.spines['left'].set_color('#CCCCCC')
    ax.tick_params(colors='#555555')
    ax.grid(axis='y' if orientation == 'vertical' else 'x', alpha=0.3, color='#CCCCCC')
    ax.set_axisbelow(True)

    plt.tight_layout()
    out = output_path or os.path.join(chart_dir, "bar_chart.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=bg_color, edgecolor='none')
    plt.close()


    return out


def render_pie_chart(
    labels: list,
    values: list,
    title: str = "",
    sort_desc: bool = True,
    output_path: str = None,
    bg_color: str = "white",
    colors: list = None,
) -> str:
    ensure_dependencies()

    if sort_desc:
        paired = sorted(zip(values, labels), key=lambda x: _to_float(x[0]), reverse=True)
        values, labels = zip(*paired)
        values = list(values)
        labels = list(labels)

    data = [(l, _to_float(v)) for l, v in zip(labels, values) if _to_float(v) > 0]
    if not data:
        raise ValueError("No positive values to render pie chart")
    labels_nz, values_nz = zip(*data)

    if colors is None:
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#DDA0DD',
                  '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']

    chart_dir = _get_chart_dir()
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    wedges, texts, autotexts = ax.pie(
        values_nz,
        labels=labels_nz,
        colors=colors[:len(values_nz)],
        autopct='%1.0f%%',
        pctdistance=0.75,
        startangle=90,
        textprops={'fontproperties': _get_font_prop(12), 'color': '#333333'},
    )
    for t in texts:
        t.set_fontproperties(_get_font_prop(12))
        t.set_color('#222222')
    for a in autotexts:
        a.set_fontweight('bold')
        a.set_fontproperties(_get_font_prop(11))
        a.set_color('white')

    legend_labels = [f'{l}: {v:.0f}人' for l, v in zip(labels_nz, values_nz)]
    ax.legend(wedges, legend_labels, title='图例',
              title_fontproperties=_get_font_prop(12, bold=True),
              loc='center left', bbox_to_anchor=(1.02, 0.5),
              prop=_get_font_prop(11), labelcolor='#333333',
              facecolor=bg_color, edgecolor='#CCCCCC')

    ax.set_title(title, fontsize=15, fontweight='bold',
                 color='#222222', fontproperties=_get_font_prop(15, bold=True), pad=15)

    plt.tight_layout()
    out = output_path or os.path.join(chart_dir, "pie_chart.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=bg_color, edgecolor='none')
    plt.close()


    return out


def render_line_chart(
    labels: list,
    values: list,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    sort_desc: bool = False,
    output_path: str = None,
    bg_color: str = "white",
    color: str = "#4A90D9",
) -> str:
    ensure_dependencies()

    labels = list(labels)
    values = [_to_float(v) for v in values]

    chart_dir = _get_chart_dir()
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)

    x = range(len(labels))
    ax.plot(x, values, marker='o', linewidth=2.5, markersize=8, color=color)
    ax.fill_between(x, values, alpha=0.15, color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontproperties=_get_font_prop(11), color='#333333')
    ax.set_ylabel(ylabel or "Value", fontproperties=_get_font_prop(12), color='#333333')
    ax.set_xlabel(xlabel or "", fontproperties=_get_font_prop(12), color='#333333')
    ax.set_title(title, fontsize=15, fontweight='bold',
                 color='#222222', fontproperties=_get_font_prop(15, bold=True), pad=12)

    for i, val in enumerate(values):
        ax.text(i, val + max(values) * 0.02, f'{val:,.2f}',
                ha='center', va='bottom', fontsize=10, color='#333333',
                fontproperties=_get_font_prop(10))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.spines['left'].set_color('#CCCCCC')
    ax.grid(True, alpha=0.3, color='#CCCCCC')
    ax.set_axisbelow(True)

    plt.tight_layout()
    out = output_path or os.path.join(chart_dir, "line_chart.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=bg_color, edgecolor='none')
    plt.close()


    return out
