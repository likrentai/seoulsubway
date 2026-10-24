"""Plotly look that follows the Streamlit theme in .streamlit/config.toml."""

import plotly.graph_objects as go
import streamlit as st

from app import settings as S


def colors():
    g = st.get_option
    return {"bg": g("theme.backgroundColor"), "panel": g("theme.secondaryBackgroundColor"), "text": g("theme.textColor"), "accent": g("theme.primaryColor"), "border": g("theme.borderColor"), "series": g("theme.chartCategoricalColors"), "muted": S.COLOR_MUTED}


def font_name(option="theme.font"):
    """Font name from a config.toml font setting, for example "'IBM Plex Sans KR'"."""
    value = st.get_option(option) or "sans-serif"
    return value.split(":http")[0] + ", sans-serif"


def style(fig, height=300):
    c = colors()
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=c["text"], size=13, family=font_name()), showlegend=False, hoverlabel=dict(bgcolor=c["panel"], bordercolor=c["border"], font_color=c["text"]))
    fig.update_xaxes(gridcolor=c["border"], zeroline=False, linecolor=c["border"], tickfont=dict(color=c["muted"]))
    fig.update_yaxes(gridcolor=c["border"], zeroline=False, linecolor=c["border"], tickfont=dict(color=c["muted"]))
    return fig


CHART_CONFIG = {"displayModeBar": False, "responsive": True}


def css():
    """Small style additions: KPI tiles and section titles."""
    c = colors()
    st.markdown(f"""<style>
.kpi {{background:{c['panel']};border:1px solid {c['border']};border-radius:0.6rem;padding:0.7rem 0.9rem;height:100%;min-height:118px}}
.kpi .lab {{font-size:0.78rem;color:{c['muted']};text-transform:uppercase;letter-spacing:0.06em;margin:0}}
.kpi .val {{font-size:1.65rem;font-weight:600;color:{c['text']};margin:0.15rem 0 0;line-height:1.2}}
.kpi .val.small {{font-size:1.15rem}}
.kpi .sub {{font-size:0.8rem;color:{c['muted']};margin:0.2rem 0 0}}
.kpi .up {{color:{S.COLOR_GOOD}}} .kpi .down {{color:{S.COLOR_BAD}}}
.kpi {{border-top:2px solid {c['accent']}}}
.sec {{font-size:0.85rem;color:{c['muted']};text-transform:uppercase;letter-spacing:0.08em;margin:0.4rem 0 0.2rem}}
.badge {{display:inline-block;font-size:0.75rem;padding:0.1rem 0.6rem;border:1px solid {S.COLOR_GOOD};color:{S.COLOR_GOOD};border-radius:1rem;margin-left:0.6rem;vertical-align:middle}}
.note {{font-size:0.78rem;color:{c['muted']}}}
.block-container {{padding-top:1.6rem}}
</style>""", unsafe_allow_html=True)


def tile(label, value, sub="", delta=None, delta_text="", small=False):
    """One KPI tile. delta > 0 shows mint, < 0 coral."""
    d = ""
    if delta is not None:
        cls = "up" if delta >= 0 else "down"
        arrow = "▲" if delta >= 0 else "▼"
        d = f'<span class="{cls}">{arrow} {delta_text}</span> '
    v_cls = "val small" if small else "val"
    return f'<div class="kpi"><p class="lab">{label}</p><p class="{v_cls}">{value}</p><p class="sub">{d}{sub}</p></div>'
