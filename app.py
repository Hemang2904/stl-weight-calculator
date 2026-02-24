"""
💎 STL Jewelry Weight & Price Calculator — Live Pricing Edition
Professional 3D Viewer with daily auto-updated India precious metal rates
Uses free APIs: Swissquote (metals) + Frankfurter (USD→INR)
"""

import streamlit as st
import numpy as np
from stl import mesh
import plotly.graph_objects as go
import tempfile
import os
import pandas as pd
import requests
import json
from datetime import datetime, timedelta, timezone

# ── Page Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💎 STL Jewelry Weight & Price Calculator",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');
    .main { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
    h1, h2, h3 {
        font-family: 'Cormorant Garamond', serif !important;
        color: #f0e6d2 !important; font-weight: 600 !important;
    }
    h1 { font-size: 3rem !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    [data-testid="stMetricValue"] {
        font-family: 'Space Mono', monospace !important;
        font-size: 1.8rem !important; color: #ffd700 !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'Cormorant Garamond', serif !important;
        color: #c0c0c0 !important; font-size: 1.05rem !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 100%);
        border-right: 2px solid #ffd700;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #ffd700 !important; }
    [data-testid="stFileUploader"] {
        background: rgba(255, 215, 0, 0.05);
        border: 2px dashed #ffd700; border-radius: 10px; padding: 20px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #1a1a2e; font-family: 'Space Mono', monospace; font-weight: 700;
        border: none; border-radius: 8px; padding: 0.75rem 2rem;
        transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px; background: rgba(255, 215, 0, 0.05);
        padding: 10px; border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Mono', monospace; background: transparent;
        color: #c0c0c0; border-radius: 6px; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #1a1a2e; font-weight: 700;
    }
    .price-card {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 215, 0, 0.02));
        border: 1px solid rgba(255, 215, 0, 0.3); border-radius: 12px;
        padding: 20px; margin: 10px 0; text-align: center;
    }
    .price-card h3 { margin: 0 0 8px 0; font-size: 1.1rem !important; }
    .price-value {
        font-family: 'Space Mono', monospace; font-size: 1.8rem;
        color: #ffd700; font-weight: 700;
    }
    .price-sub {
        font-family: 'Space Mono', monospace; font-size: 0.85rem;
        color: #c0c0c0; margin-top: 4px;
    }
    .ring-info {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.12), rgba(255, 180, 0, 0.05));
        border: 1px solid rgba(255, 215, 0, 0.4); border-radius: 12px;
        padding: 20px; margin: 10px 0;
    }
    .live-badge {
        display: inline-block; background: #00c853; color: #fff;
        font-family: 'Space Mono', monospace; font-weight: 700;
        padding: 3px 10px; border-radius: 12px; font-size: 0.7rem;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════════
# LIVE PRICE FETCHING
# ═══════════════════════════════════════════════════════════════════════════════════

TROY_OZ_TO_GRAM = 31.1035

# Density g/mm³ for each material
MATERIAL_DENSITIES = {
    '24K Gold (999)': 0.01932,
    '22K Gold (916)': 0.01788,
    '18K Gold (750)': 0.01540,
    '14K Gold (585)': 0.01310,
    '9K Gold (375)': 0.01115,
    'White Gold 18K': 0.01470,
    'Rose Gold 18K': 0.01500,
    'Sterling Silver (925)': 0.01040,
    'Fine Silver (999)': 0.01050,
    'Platinum (950)': 0.02140,
    'Platinum (900)': 0.02040,
    'Palladium (950)': 0.01200,
    'Rhodium': 0.01241,
    'Titanium': 0.00451,
    'Stainless Steel': 0.00800,
}

MATERIAL_COLORS = {
    '24K Gold (999)': '#FFD700', '22K Gold (916)': '#FFA500',
    '18K Gold (750)': '#DAA520', '14K Gold (585)': '#CD853F',
    '9K Gold (375)': '#B8860B', 'White Gold 18K': '#F5F5F5',
    'Rose Gold 18K': '#B76E79', 'Sterling Silver (925)': '#C0C0C0',
    'Fine Silver (999)': '#D3D3D3', 'Platinum (950)': '#E5E4E2',
    'Platinum (900)': '#E5E4E2', 'Palladium (950)': '#CED0DD',
    'Rhodium': '#E8E8E8', 'Titanium': '#878681', 'Stainless Steel': '#8B8D8F',
}

MATERIAL_INFO = {
    '24K Gold (999)': '99.9% pure gold – Investment grade, very soft for jewelry',
    '22K Gold (916)': '91.6% pure – Most popular in Indian jewelry',
    '18K Gold (750)': '75.0% pure – International jewelry standard',
    '14K Gold (585)': '58.5% pure – Common in Western everyday jewelry',
    '9K Gold (375)': '37.5% pure – Budget-friendly gold option',
    'White Gold 18K': '75% gold + white metals – Popular for diamond settings',
    'Rose Gold 18K': '75% gold + copper alloy – Romantic pink hue',
    'Sterling Silver (925)': '92.5% silver – Standard silver jewelry alloy',
    'Fine Silver (999)': '99.9% pure silver – Very soft, mainly for casting',
    'Platinum (950)': '95% pure – Premium jewelry, hypoallergenic',
    'Platinum (900)': '90% pure – Slightly harder platinum alloy',
    'Palladium (950)': '95% pure – Lightweight platinum-group metal',
    'Rhodium': 'Used for plating white gold and silver jewelry',
    'Titanium': "Lightweight, hypoallergenic – Modern men's rings",
    'Stainless Steel': 'Durable, affordable – Fashion jewelry',
}

# Gold purity multipliers relative to 24K
GOLD_PURITY = {
    '24K Gold (999)': 1.0,
    '22K Gold (916)': 0.9167,
    '18K Gold (750)': 0.7500,
    '14K Gold (585)': 0.5850,
    '9K Gold (375)': 0.3750,
    'White Gold 18K': 0.7500,
    'Rose Gold 18K': 0.7500,
}

# Maps each material to which base metal spot price to use
MATERIAL_BASE_METAL = {
    '24K Gold (999)': 'XAU', '22K Gold (916)': 'XAU',
    '18K Gold (750)': 'XAU', '14K Gold (585)': 'XAU',
    '9K Gold (375)': 'XAU', 'White Gold 18K': 'XAU',
    'Rose Gold 18K': 'XAU',
    'Sterling Silver (925)': 'XAG', 'Fine Silver (999)': 'XAG',
    'Platinum (950)': 'XPT', 'Platinum (900)': 'XPT',
    'Palladium (950)': 'XPD',
    'Rhodium': None,  # no free live feed — use fallback
    'Titanium': None,
    'Stainless Steel': None,
}

# Silver purity multipliers
SILVER_PURITY = {
    'Sterling Silver (925)': 0.925,
    'Fine Silver (999)': 1.0,
}

PLATINUM_PURITY = {
    'Platinum (950)': 0.95,
    'Platinum (900)': 0.90,
    'Palladium (950)': 0.95,
}

# Hardcoded fallback prices ₹/gram (for metals without live feeds)
FALLBACK_PRICES = {
    'Rhodium': 14500,
    'Titanium': 35,
    'Stainless Steel': 5,
}


@st.cache_data(ttl=3600)  # cache for 1 hour
def fetch_live_prices():
    """
    Fetch live spot prices for Gold, Silver, Platinum, Palladium in USD/oz
    from Swissquote (free, no API key), then convert to INR/gram using
    Frankfurter (free, no API key).

    Returns dict of material_name → ₹/gram and metadata.
    """
    prices_inr_per_gram = {}
    spot_usd_per_oz = {}
    usd_inr = None
    source_info = {"status": "fetching", "timestamp": None, "usd_inr": None, "errors": []}

    # 1) USD → INR exchange rate
    try:
        # Try yesterday's date first for "yesterday's rate"
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        resp = requests.get(
            f"https://api.frankfurter.dev/v1/{yesterday}?base=USD&symbols=INR",
            timeout=8
        )
        data = resp.json()
        usd_inr = data["rates"]["INR"]
        source_info["usd_inr"] = usd_inr
        source_info["fx_date"] = data.get("date", yesterday)
    except Exception as e:
        source_info["errors"].append(f"FX rate: {e}")
        # Fallback to latest
        try:
            resp = requests.get(
                "https://api.frankfurter.dev/v1/latest?base=USD&symbols=INR",
                timeout=8
            )
            data = resp.json()
            usd_inr = data["rates"]["INR"]
            source_info["usd_inr"] = usd_inr
            source_info["fx_date"] = data.get("date", "latest")
        except Exception as e2:
            source_info["errors"].append(f"FX fallback: {e2}")
            usd_inr = 91.0  # hardcoded emergency fallback
            source_info["usd_inr"] = usd_inr
            source_info["fx_date"] = "fallback"

    # 2) Spot metal prices in USD per troy oz from Swissquote
    metals = {"XAU": "Gold", "XAG": "Silver", "XPT": "Platinum", "XPD": "Palladium"}
    for symbol, name in metals.items():
        try:
            resp = requests.get(
                f"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/{symbol}/USD",
                timeout=8
            )
            data = resp.json()
            # Use the mid price from first entry
            bid = data[0]["spreadProfilePrices"][0]["bid"]
            ask = data[0]["spreadProfilePrices"][0]["ask"]
            mid = (bid + ask) / 2
            spot_usd_per_oz[symbol] = mid
        except Exception as e:
            source_info["errors"].append(f"{symbol}: {e}")
            spot_usd_per_oz[symbol] = None

    source_info["spot_usd_per_oz"] = spot_usd_per_oz
    source_info["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # 3) Calculate ₹/gram for each material
    for material in MATERIAL_DENSITIES:
        base = MATERIAL_BASE_METAL.get(material)

        if base is None:
            # Use hardcoded fallback
            prices_inr_per_gram[material] = FALLBACK_PRICES.get(material, 0)
            continue

        spot = spot_usd_per_oz.get(base)
        if spot is None:
            prices_inr_per_gram[material] = 0
            continue

        # Convert USD/troy oz → INR/gram
        inr_per_gram_pure = (spot * usd_inr) / TROY_OZ_TO_GRAM

        # Apply purity factor
        if base == "XAU":
            purity = GOLD_PURITY.get(material, 1.0)
        elif base == "XAG":
            purity = SILVER_PURITY.get(material, 1.0)
        elif base in ("XPT", "XPD"):
            purity = PLATINUM_PURITY.get(material, 1.0)
        else:
            purity = 1.0

        prices_inr_per_gram[material] = round(inr_per_gram_pure * purity, 2)

    # Add Indian market premium (~2-4% for gold due to import duty, GST on import etc.)
    # This is a rough approximation — actual jeweler rates will be higher
    INDIA_PREMIUM = 1.03  # ~3% premium over spot
    for mat in prices_inr_per_gram:
        base = MATERIAL_BASE_METAL.get(mat)
        if base in ("XAU",):
            prices_inr_per_gram[mat] = round(prices_inr_per_gram[mat] * INDIA_PREMIUM, 2)

    if not source_info["errors"]:
        source_info["status"] = "live"
    else:
        source_info["status"] = "partial"

    return prices_inr_per_gram, source_info


# ═══════════════════════════════════════════════════════════════════════════════════
# RING SIZE CHART
# ═══════════════════════════════════════════════════════════════════════════════════
RING_SIZE_CHART = [
    (1,  1,   'A',   12.04, 37.8),
    (2,  1.5, 'B',   12.45, 39.1),
    (3,  2,   'C',   12.85, 40.4),
    (4,  2.5, 'D',   13.26, 41.6),
    (5,  3,   'E',   13.67, 42.9),
    (6,  3.5, 'F',   14.07, 44.2),
    (7,  4,   'G',   14.48, 45.5),
    (8,  4.5, 'H',   14.88, 46.7),
    (9,  5,   'I/J', 15.29, 48.0),
    (10, 5.5, 'J/K', 15.49, 48.7),
    (11, 6,   'L',   15.90, 49.9),
    (12, 6.5, 'L/M', 16.31, 51.2),
    (13, 7,   'N',   16.71, 52.5),
    (14, 7.5, 'O',   17.12, 53.8),
    (15, 8,   'P',   17.53, 55.1),
    (16, 8.5, 'P/Q', 17.93, 56.3),
    (17, 9,   'Q/R', 18.34, 57.6),
    (18, 9.5, 'R/S', 18.75, 58.9),
    (19, 10,  'T',   19.15, 60.2),
    (20, 10.5,'T/U', 19.56, 61.4),
    (21, 11,  'U/V', 19.96, 62.7),
    (22, 11.5,'V/W', 20.37, 64.0),
    (23, 12,  'X',   20.78, 65.3),
    (24, 12.5,'Y',   21.18, 66.5),
    (25, 13,  'Z',   21.59, 67.8),
]


# ═══════════════════════════════════════════════════════════════════════════════════
# JEWELRY DETECTION
# ═══════════════════════════════════════════════════════════════════════════════════
def detect_jewelry_type(stats, volume):
    dims = stats['dimensions']
    x, y, z = sorted(dims)
    aspect_xy = max(dims[0], dims[1]) / (min(dims[0], dims[1]) + 0.001)
    max_dim = max(dims)
    min_dim = min(dims)
    bbox_vol = dims[0] * dims[1] * dims[2]
    fill_ratio = volume / (bbox_vol + 0.001)

    result = {'type': 'General Jewelry', 'icon': '💎', 'details': {}}

    if (aspect_xy < 1.8 and fill_ratio < 0.45 and
        min_dim > 2 and min_dim < 20 and max_dim > 10 and max_dim < 40):

        result['type'] = 'Ring'
        result['icon'] = '💍'

        sorted_dims = sorted(enumerate(dims), key=lambda d: d[1])
        ring_plane_dims = [dims[sorted_dims[1][0]], dims[sorted_dims[2][0]]]
        band_height = sorted_dims[0][1]
        outer_diameter = max(ring_plane_dims)

        R_outer = outer_diameter / 2.0
        ring_area = volume / (band_height + 0.001)
        r_squared = R_outer**2 - ring_area / np.pi
        inner_diameter = 2 * np.sqrt(r_squared) if r_squared > 0 else outer_diameter * 0.7

        if band_height > outer_diameter * 0.6:
            band_height = min(ring_plane_dims[0], z)

        result['details'] = {
            'outer_diameter': outer_diameter,
            'inner_diameter': inner_diameter,
            'band_height': band_height,
            'wall_thickness': (outer_diameter - inner_diameter) / 2.0,
        }
        closest = find_ring_size(inner_diameter)
        if closest:
            result['details']['ring_size'] = closest

    elif max_dim > 100 and fill_ratio < 0.15:
        result['type'] = 'Necklace/Chain'
        result['icon'] = '📿'
    elif min_dim < 3 and max_dim < 40 and aspect_xy > 2:
        result['type'] = 'Pendant'
        result['icon'] = '🔮'
    elif max_dim < 25 and min_dim < 15 and fill_ratio > 0.3:
        result['type'] = 'Earring'
        result['icon'] = '✨'
    elif max_dim > 40 and max_dim < 100 and fill_ratio < 0.25:
        result['type'] = 'Bangle/Bracelet'
        result['icon'] = '⭕'
        result['details'] = {
            'outer_diameter': max(dims[0], dims[1]),
            'inner_diameter': max(dims[0], dims[1]) * 0.85,
        }
    return result


def find_ring_size(inner_diameter_mm):
    if inner_diameter_mm < 10 or inner_diameter_mm > 25:
        return None
    closest, min_diff = None, float('inf')
    for indian, us, uk, dia, circ in RING_SIZE_CHART:
        diff = abs(dia - inner_diameter_mm)
        if diff < min_diff:
            min_diff = diff
            closest = {'indian': indian, 'us': us, 'uk': uk,
                       'diameter': dia, 'circumference': circ, 'diff_mm': diff}
    return closest


# ═══════════════════════════════════════════════════════════════════════════════════
# CORE CALCULATIONS
# ═══════════════════════════════════════════════════════════════════════════════════
def calculate_stl_volume(stl_mesh):
    volume = 0.0
    for triangle in stl_mesh.vectors:
        A, B, C = triangle[0], triangle[1], triangle[2]
        volume += np.dot(A, np.cross(B, C))
    return abs(volume) / 6.0


def calculate_weight(volume_mm3, material_name):
    return volume_mm3 * MATERIAL_DENSITIES[material_name]


def calculate_price(weight_grams, material_name, prices, making_charge_pct=0, gst_pct=3):
    rate = prices.get(material_name, 0)
    base_price = weight_grams * rate
    making = base_price * (making_charge_pct / 100.0)
    subtotal = base_price + making
    gst = subtotal * (gst_pct / 100.0)
    total = subtotal + gst
    return {'metal_cost': base_price, 'making_charges': making,
            'subtotal': subtotal, 'gst': gst, 'total': total, 'rate': rate}


def get_mesh_statistics(stl_mesh):
    all_points = stl_mesh.vectors.reshape(-1, 3)
    dims = all_points.max(axis=0) - all_points.min(axis=0)
    return {
        'num_triangles': len(stl_mesh.vectors),
        'num_vertices': len(all_points),
        'min_coords': all_points.min(axis=0),
        'max_coords': all_points.max(axis=0),
        'dimensions': dims,
        'surface_area': stl_mesh.areas.sum(),
        'center': all_points.mean(axis=0),
        'bbox_volume': dims[0] * dims[1] * dims[2],
    }


# ═══════════════════════════════════════════════════════════════════════════════════
# 3D VIEWER & CHARTS
# ═══════════════════════════════════════════════════════════════════════════════════
def create_3d_viewer(stl_mesh, volume, filename, selected_material):
    stats = get_mesh_statistics(stl_mesh)
    vertices = stl_mesh.vectors.reshape(-1, 3)
    n_tri = len(stl_mesh.vectors)
    i, j, k = np.arange(0, n_tri*3, 3), np.arange(1, n_tri*3, 3), np.arange(2, n_tri*3, 3)
    fig = go.Figure()
    mesh_color = MATERIAL_COLORS.get(selected_material, '#FFD700')
    fig.add_trace(go.Mesh3d(
        x=vertices[:,0], y=vertices[:,1], z=vertices[:,2], i=i, j=j, k=k,
        color=mesh_color, opacity=0.95, flatshading=False,
        lighting=dict(ambient=0.6, diffuse=0.9, specular=0.8, roughness=0.2, fresnel=0.5),
        lightposition=dict(x=100, y=100, z=100),
        hovertemplate='X: %{x:.2f} mm<br>Y: %{y:.2f} mm<br>Z: %{z:.2f} mm<extra></extra>',
        name='3D Model'
    ))
    ax = dict(backgroundcolor='rgb(20,20,30)', gridcolor='rgba(255,215,0,0.1)',
              showbackground=True, zerolinecolor='rgba(255,215,0,0.3)')
    fig.update_scenes(
        xaxis=dict(title='X (mm)', **ax), yaxis=dict(title='Y (mm)', **ax),
        zaxis=dict(title='Z (mm)', **ax),
        camera=dict(eye=dict(x=1.5,y=1.5,z=1.3)), aspectmode='data', bgcolor='rgb(15,15,25)'
    )
    fig.update_layout(
        title={'text': f"<b>{filename}</b>", 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 20, 'color': '#f0e6d2', 'family': 'Cormorant Garamond'}},
        showlegend=False, height=550,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0,r=0,t=50,b=0), font=dict(family='Space Mono', color='#c0c0c0')
    )
    return fig, stats


def create_comparison_chart(volume, prices):
    materials = list(MATERIAL_DENSITIES.keys())
    weights = [calculate_weight(volume, m) for m in materials]
    colors = [MATERIAL_COLORS[m] for m in materials]
    costs = [weights[i] * prices.get(materials[i], 0) for i in range(len(materials))]
    fig = go.Figure(data=[go.Bar(
        x=materials, y=weights,
        marker=dict(color=colors, line=dict(color='#1a1a2e', width=2)),
        text=[f"{w:.3f}g" for w in weights], textposition='outside',
        textfont=dict(size=11, color='#f0e6d2', family='Space Mono'),
        hovertemplate='<b>%{x}</b><br>Weight: %{y:.4f}g<br>Cost: ₹%{customdata:,.0f}<extra></extra>',
        customdata=costs
    )])
    fig.update_layout(
        title={'text': f"<b>Weight Comparison</b><br><sub>Volume: {volume:.2f} mm³</sub>",
               'x': 0.5, 'xanchor': 'center',
               'font': {'size': 18, 'color': '#f0e6d2', 'family': 'Cormorant Garamond'}},
        xaxis_title="<b>Material</b>", yaxis_title="<b>Weight (grams)</b>",
        height=500, showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Space Mono', color='#c0c0c0', size=10),
        xaxis=dict(tickangle=-45, gridcolor='rgba(255,215,0,0.1)'),
        yaxis=dict(gridcolor='rgba(255,215,0,0.1)')
    )
    return fig


def create_price_chart(volume, prices, source_info):
    materials = list(MATERIAL_DENSITIES.keys())
    weights = [calculate_weight(volume, m) for m in materials]
    costs = [weights[i] * prices.get(materials[i], 0) for i in range(len(materials))]
    colors = [MATERIAL_COLORS[m] for m in materials]
    fig = go.Figure(data=[go.Bar(
        x=materials, y=costs,
        marker=dict(color=colors, line=dict(color='#1a1a2e', width=2)),
        text=[f"₹{p:,.0f}" for p in costs], textposition='outside',
        textfont=dict(size=10, color='#f0e6d2', family='Space Mono'),
        hovertemplate='<b>%{x}</b><br>Metal Cost: ₹%{y:,.2f}<br>Weight: %{customdata:.4f}g<extra></extra>',
        customdata=weights
    )])
    ts = source_info.get("timestamp", "N/A")
    fig.update_layout(
        title={'text': f"<b>Metal Cost Comparison (Live India Rates)</b><br><sub>Updated: {ts} · excl. making & GST</sub>",
               'x': 0.5, 'xanchor': 'center',
               'font': {'size': 18, 'color': '#f0e6d2', 'family': 'Cormorant Garamond'}},
        xaxis_title="<b>Material</b>", yaxis_title="<b>Price (₹)</b>",
        height=500, showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Space Mono', color='#c0c0c0', size=10),
        xaxis=dict(tickangle=-45, gridcolor='rgba(255,215,0,0.1)'),
        yaxis=dict(gridcolor='rgba(255,215,0,0.1)')
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════════
def main():
    st.markdown("""
        <h1 style='text-align:center; margin-bottom:0;'>💎 STL Jewelry Weight & Price Calculator</h1>
        <p style='text-align:center; color:#c0c0c0; font-family:"Space Mono",monospace; font-size:1rem;'>
            Professional 3D Viewer · <span class="live-badge">LIVE</span> India Metal Rates · Ring Size Detection
        </p>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # ── Fetch live prices ────────────────────────────────────────────────────────
    prices, source_info = fetch_live_prices()

    # ── Sidebar ──────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        jewelry_type_hint = st.selectbox(
            "Jewelry Type", ['Auto-Detect', 'Ring', 'Pendant', 'Earring',
                             'Bangle/Bracelet', 'Necklace/Chain', 'Other'], index=0)

        st.markdown("---")
        st.markdown("### 🏅 Select Material")
        material_category = st.selectbox("Category",
            ['Gold', 'Silver', 'Platinum Group', 'Other Metals'], index=0)

        cat_mats = {
            'Gold': ['24K Gold (999)', '22K Gold (916)', '18K Gold (750)',
                     '14K Gold (585)', '9K Gold (375)', 'White Gold 18K', 'Rose Gold 18K'],
            'Silver': ['Sterling Silver (925)', 'Fine Silver (999)'],
            'Platinum Group': ['Platinum (950)', 'Platinum (900)', 'Palladium (950)', 'Rhodium'],
            'Other Metals': ['Titanium', 'Stainless Steel'],
        }
        selected_material = st.selectbox("Material", cat_mats[material_category], index=0)

        rate = prices.get(selected_material, 0)
        color = MATERIAL_COLORS[selected_material]
        st.markdown(f"""
        <div style='background:rgba(255,215,0,0.08); border-left:4px solid {color};
                    padding:12px; border-radius:8px; margin:10px 0;'>
            <b style='color:{color};'>{selected_material}</b><br>
            <span style='color:#c0c0c0; font-size:0.85rem;'>{MATERIAL_INFO[selected_material]}</span><br>
            <span style='color:#ffd700; font-family:"Space Mono"; font-size:0.9rem;'>
                Density: {MATERIAL_DENSITIES[selected_material]:.5f} g/mm³<br>
                Rate: ₹{rate:,.2f}/gram <span class="live-badge">LIVE</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 💰 Pricing Options")
        making_charge = st.slider("Making Charges (%)", 0, 35, 12,
                                   help="Jeweller's craftsmanship charges (8-25% typical)")
        gst_rate = st.selectbox("GST Rate (%)", [3.0, 5.0, 0.0], index=0)

        st.markdown("---")
        st.markdown("### 📏 Display")
        show_comparison = st.checkbox("Weight comparison chart", True)
        show_price_chart = st.checkbox("Price comparison chart", True)

        # Price source info
        st.markdown("---")
        status_color = "#00c853" if source_info["status"] == "live" else "#ff9900"
        usd_inr = source_info.get("usd_inr", "N/A")
        fx_date = source_info.get("fx_date", "N/A")
        ts = source_info.get("timestamp", "N/A")
        spot = source_info.get("spot_usd_per_oz", {})

        st.markdown(f"""
        <div style='background:rgba(0,200,80,0.08); border:1px solid {status_color};
                    border-radius:8px; padding:10px;'>
            <span style='color:{status_color}; font-size:0.8rem; font-weight:700;'>
                ● PRICE SOURCE: {source_info["status"].upper()}</span><br>
            <span style='color:#ccc; font-size:0.75rem;'>
                Metals: Swissquote (free)<br>
                FX: Frankfurter ({fx_date})<br>
                USD/INR: ₹{usd_inr}<br>
                Gold: ${spot.get("XAU", "N/A"):.2f}/oz<br>
                Silver: ${spot.get("XAG", "N/A"):.2f}/oz<br>
                Platinum: ${spot.get("XPT", "N/A"):.2f}/oz<br>
                Updated: {ts}
            </span>
        </div>
        """, unsafe_allow_html=True)

        if source_info["errors"]:
            st.warning(f"Some prices may be approximate: {', '.join(source_info['errors'])}")

        if st.button("🔄 Refresh Prices"):
            st.cache_data.clear()
            st.rerun()

    # ── Main Content ─────────────────────────────────────────────────────────────
    col_main, col_side = st.columns([2.2, 1])

    with col_main:
        st.markdown("### 📤 Upload STL File")
        uploaded_file = st.file_uploader("Choose an STL file", type=['stl'],
            help="Upload 3D jewelry model in STL format (units must be mm)",
            label_visibility="collapsed")

        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            try:
                with st.spinner('Loading 3D model...'):
                    stl_mesh = mesh.Mesh.from_file(tmp_path)

                volume = calculate_stl_volume(stl_mesh)
                fig_3d, stats = create_3d_viewer(stl_mesh, volume, uploaded_file.name, selected_material)

                jewelry_info = detect_jewelry_type(stats, volume)
                if jewelry_type_hint != 'Auto-Detect':
                    jewelry_info['type'] = jewelry_type_hint
                    jewelry_info['icon'] = {'Ring':'💍','Pendant':'🔮','Earring':'✨',
                        'Bangle/Bracelet':'⭕','Necklace/Chain':'📿','Other':'💎'}[jewelry_type_hint]

                st.plotly_chart(fig_3d, use_container_width=True)

                # ── Exact Dimensions ─────────────────────────────────────
                st.markdown("### 📐 Exact Dimensions & Measurements")
                dims = stats['dimensions']
                min_c, max_c = stats['min_coords'], stats['max_coords']

                d1, d2, d3, d4 = st.columns(4)
                with d1: st.metric("Length (X)", f"{dims[0]:.3f} mm")
                with d2: st.metric("Width (Y)", f"{dims[1]:.3f} mm")
                with d3: st.metric("Height (Z)", f"{dims[2]:.3f} mm")
                with d4: st.metric("Detected Type", f"{jewelry_info['icon']} {jewelry_info['type']}")

                with st.expander("📍 Detailed Coordinate Bounds"):
                    st.dataframe(pd.DataFrame({
                        'Axis': ['X', 'Y', 'Z'],
                        'Min (mm)': [f"{min_c[i]:.4f}" for i in range(3)],
                        'Max (mm)': [f"{max_c[i]:.4f}" for i in range(3)],
                        'Span (mm)': [f"{dims[i]:.4f}" for i in range(3)],
                        'Center (mm)': [f"{stats['center'][i]:.4f}" for i in range(3)],
                    }), use_container_width=True, hide_index=True)

                # ── Ring Info ────────────────────────────────────────────
                if jewelry_info['type'] == 'Ring' and jewelry_info.get('details'):
                    det = jewelry_info['details']
                    st.markdown("### 💍 Ring Analysis")
                    r1, r2, r3, r4 = st.columns(4)
                    with r1: st.metric("Outer Diameter", f"{det['outer_diameter']:.2f} mm")
                    with r2: st.metric("Inner Diameter", f"{det['inner_diameter']:.2f} mm")
                    with r3: st.metric("Band Height", f"{det['band_height']:.2f} mm")
                    with r4: st.metric("Wall Thickness", f"{det['wall_thickness']:.2f} mm")

                    if det.get('ring_size'):
                        rs = det['ring_size']
                        st.markdown(f"""
                        <div class="ring-info">
                            <h3 style='margin:0 0 10px 0;'>🔍 Estimated Ring Size (inner ⌀ {det['inner_diameter']:.2f} mm)</h3>
                            <table style='width:100%; color:#f0e6d2; font-family:"Space Mono",monospace;'>
                                <tr>
                                    <td style='padding:8px;'><b>🇮🇳 Indian:</b> <span style='color:#ffd700; font-size:1.3rem;'>{rs['indian']}</span></td>
                                    <td style='padding:8px;'><b>🇺🇸 US:</b> <span style='color:#ffd700; font-size:1.3rem;'>{rs['us']}</span></td>
                                    <td style='padding:8px;'><b>🇬🇧 UK:</b> <span style='color:#ffd700; font-size:1.3rem;'>{rs['uk']}</span></td>
                                </tr>
                                <tr>
                                    <td style='padding:8px;'>Std ⌀: {rs['diameter']:.2f} mm</td>
                                    <td style='padding:8px;'>Circ: {rs['circumference']:.1f} mm</td>
                                    <td style='padding:8px;'>Deviation: ±{rs['diff_mm']:.2f} mm</td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)

                # ── Mesh Stats ───────────────────────────────────────────
                with st.expander("📊 Mesh Statistics", expanded=True):
                    s1, s2, s3, s4 = st.columns(4)
                    with s1: st.metric("Triangles", f"{stats['num_triangles']:,}")
                    with s2: st.metric("Volume", f"{volume:.2f} mm³")
                    with s3: st.metric("Surface Area", f"{stats['surface_area']:.2f} mm²")
                    with s4:
                        fill = (volume / stats['bbox_volume'] * 100) if stats['bbox_volume'] > 0 else 0
                        st.metric("BBox Fill", f"{fill:.1f}%")

                st.markdown("---")

                # ── Weight & Pricing ─────────────────────────────────────
                st.markdown("### ⚖️ Weight & Price Analysis")
                weight_g = calculate_weight(volume, selected_material)
                pricing = calculate_price(weight_g, selected_material, prices, making_charge, gst_rate)
                troy_oz = weight_g / 31.1035
                dwt = weight_g / 1.55517

                st.markdown(f"""
                <div style='display:flex; gap:15px; flex-wrap:wrap;'>
                    <div class="price-card" style='flex:1; min-width:180px;'>
                        <h3 style='color:#c0c0c0 !important;'>Weight ({selected_material})</h3>
                        <div class="price-value">{weight_g:.4f} g</div>
                        <div class="price-sub">{troy_oz:.4f} troy oz · {dwt:.4f} dwt</div>
                    </div>
                    <div class="price-card" style='flex:1; min-width:180px;'>
                        <h3 style='color:#c0c0c0 !important;'>Metal Cost <span class="live-badge">LIVE</span></h3>
                        <div class="price-value">₹{pricing['metal_cost']:,.2f}</div>
                        <div class="price-sub">@ ₹{pricing['rate']:,.2f}/g</div>
                    </div>
                    <div class="price-card" style='flex:1; min-width:180px;'>
                        <h3 style='color:#c0c0c0 !important;'>Making ({making_charge}%)</h3>
                        <div class="price-value">₹{pricing['making_charges']:,.2f}</div>
                        <div class="price-sub">Craftsmanship fee</div>
                    </div>
                    <div class="price-card" style='flex:1; min-width:180px; border-color:rgba(255,215,0,0.6);'>
                        <h3 style='color:#ffd700 !important;'>Total Estimated Price</h3>
                        <div class="price-value" style='font-size:2rem;'>₹{pricing['total']:,.2f}</div>
                        <div class="price-sub">incl. {gst_rate}% GST (₹{pricing['gst']:,.2f})</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Tabs ─────────────────────────────────────────────────
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📋 All Materials", "📊 Weight Chart", "💰 Price Chart",
                    "🧮 Calculator", "📏 Ring Sizes"])

                with tab1:
                    rows = []
                    for mat in MATERIAL_DENSITIES:
                        wt = calculate_weight(volume, mat)
                        pr = calculate_price(wt, mat, prices, making_charge, gst_rate)
                        rows.append({
                            'Material': mat,
                            'Density': f"{MATERIAL_DENSITIES[mat]:.5f}",
                            'Weight (g)': f"{wt:.4f}",
                            'Troy oz': f"{wt/31.1035:.4f}",
                            'Rate (₹/g)': f"₹{pr['rate']:,.2f}",
                            'Metal (₹)': f"₹{pr['metal_cost']:,.2f}",
                            f'Total +{making_charge}%MC +GST': f"₹{pr['total']:,.2f}",
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

                with tab2:
                    if show_comparison:
                        st.plotly_chart(create_comparison_chart(volume, prices), use_container_width=True)

                with tab3:
                    if show_price_chart:
                        st.plotly_chart(create_price_chart(volume, prices, source_info), use_container_width=True)

                with tab4:
                    st.markdown("#### Quick Calculator")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        calc_mat = st.selectbox("Material", list(MATERIAL_DENSITIES.keys()),
                            index=list(MATERIAL_DENSITIES.keys()).index(selected_material), key="calc_mat")
                    with cc2:
                        calc_vol = st.number_input("Volume (mm³)", min_value=0.0,
                            value=float(volume), step=0.1, format="%.2f")
                    calc_mc = st.slider("Making (%)", 0, 35, making_charge, key="calc_mc")
                    cw = calculate_weight(calc_vol, calc_mat)
                    cp = calculate_price(cw, calc_mat, prices, calc_mc, gst_rate)
                    rc1, rc2, rc3, rc4 = st.columns(4)
                    with rc1: st.metric("Weight", f"{cw:.4f} g")
                    with rc2: st.metric("Metal", f"₹{cp['metal_cost']:,.2f}")
                    with rc3: st.metric("MC + GST", f"₹{cp['making_charges']+cp['gst']:,.2f}")
                    with rc4: st.metric("Total", f"₹{cp['total']:,.2f}")

                with tab5:
                    st.markdown("#### Indian / US / UK Ring Size Reference")
                    st.dataframe(pd.DataFrame(RING_SIZE_CHART,
                        columns=['Indian', 'US', 'UK', 'Inner ⌀ (mm)', 'Circ (mm)']),
                        use_container_width=True, hide_index=True)

                os.unlink(tmp_path)

            except Exception as e:
                st.error(f"Error processing STL file: {str(e)}")
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        else:
            st.info("👆 Upload an STL file to begin analysis")
            st.markdown("""
            ### 🎯 Features
            - **Live India Pricing** – Auto-fetches metal spot rates daily (Swissquote + Frankfurter FX)
            - **Exact 3D Dimensions** – X, Y, Z to 0.001mm precision
            - **Ring Detection** – Inner/outer diameter, wall thickness, Indian/US/UK ring size
            - **15 Precious Metals** – Gold (9K–24K), Silver, Platinum, Palladium, more
            - **Full Price Breakdown** – Metal cost → making charges → GST → total
            - **Interactive 3D Viewer** – Rotate, zoom, inspect

            ### 🚀 How to Use
            1. Upload STL file (in **millimeters**)
            2. Select material from sidebar
            3. Adjust making charges & GST
            4. View dimensions, ring size, weight & live pricing
            """)

    with col_side:
        st.markdown(f"### 💰 Live India Metal Rates")
        st.markdown(f"<small style='color:#999;'><span class='live-badge'>LIVE</span> {source_info.get('timestamp','')}</small>",
                    unsafe_allow_html=True)

        key_metals = ['24K Gold (999)', '22K Gold (916)', '18K Gold (750)',
                      'Sterling Silver (925)', 'Platinum (950)', 'Palladium (950)']
        for mat in key_metals:
            r = prices.get(mat, 0)
            c = MATERIAL_COLORS[mat]
            st.markdown(f"""
            <div style='background:rgba(255,215,0,0.05); border-left:4px solid {c};
                        padding:10px 14px; margin-bottom:8px; border-radius:6px;'>
                <b style='color:{c}; font-size:0.9rem;'>{mat}</b><br>
                <span style='color:#ffd700; font-family:"Space Mono"; font-size:1.1rem; font-weight:700;'>
                    ₹{r:,.2f}/g
                </span>
                <span style='color:#888; font-size:0.75rem; margin-left:8px;'>
                    ₹{r*10:,.0f}/10g
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 📏 Quick Reference")
        st.markdown("""
        - **1 troy oz** = 31.1035 g
        - **1 pennyweight** = 1.55517 g
        - **1 tola** = 11.664 g
        - **1 cm³** = 1000 mm³
        - **GST on jewelry** = 3%
        """)
        st.markdown("---")
        st.markdown("### 🧮 Formula")
        st.latex(r"W = V \times \rho")
        st.latex(r"P = W \times R \times (1{+}MC\%) \times (1{+}GST\%)")
        st.markdown("""
        <p style='font-size:0.8rem; color:#999; font-style:italic;'>
        W=weight, V=volume, ρ=density, R=live rate/g, MC=making charges
        </p>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
