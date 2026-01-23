"""
💎 STL Weight Calculator - Professional Interactive 3D Viewer
A Streamlit application for calculating precious metal weights from STL files
"""

import streamlit as st
import numpy as np
from stl import mesh
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="hiiiii",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap');
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Headers with luxury font */
    h1, h2, h3 {
        font-family: 'Cormorant Garamond', serif !important;
        color: #f0e6d2 !important;
        font-weight: 600 !important;
    }
    
    h1 {
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-family: 'Space Mono', monospace !important;
        font-size: 2rem !important;
        color: #ffd700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Cormorant Garamond', serif !important;
        color: #c0c0c0 !important;
        font-size: 1.1rem !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1e 0%, #1a1a2e 100%);
        border-right: 2px solid #ffd700;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffd700 !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(255, 215, 0, 0.05);
        border: 2px dashed #ffd700;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #1a1a2e;
        font-family: 'Space Mono', monospace;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(255, 215, 0, 0.1);
        border-left: 4px solid #ffd700;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 215, 0, 0.05);
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Mono', monospace;
        background: transparent;
        color: #c0c0c0;
        border-radius: 6px;
        padding: 10px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #1a1a2e;
        font-weight: 700;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        font-family: 'Space Mono', monospace;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Cormorant Garamond', serif;
        font-size: 1.3rem;
        color: #ffd700 !important;
    }
</style>
""", unsafe_allow_html=True)

# Material properties
MATERIAL_DENSITIES = {
    '14K Gold': 0.0131,
    '18K Gold': 0.0154,
    '22K Gold': 0.0174,
    '24K Gold': 0.0193,
    'Silver (925)': 0.0104,
    'Platinum (950)': 0.0214,
    'Platinum (900)': 0.0204,
    'Palladium': 0.0120,
    'White Gold (18K)': 0.0147,
    'Rose Gold (18K)': 0.0150,
}

MATERIAL_COLORS = {
    '14K Gold': '#DAA520',
    '18K Gold': '#FFD700',
    '22K Gold': '#FFA500',
    '24K Gold': '#FFD700',
    'Silver (925)': '#C0C0C0',
    'Platinum (950)': '#E5E4E2',
    'Platinum (900)': '#E5E4E2',
    'Palladium': '#CED0DD',
    'White Gold (18K)': '#F5F5F5',
    'Rose Gold (18K)': '#B76E79',
}

MATERIAL_INFO = {
    '14K Gold': '58.3% pure - Common for everyday jewelry',
    '18K Gold': '75.0% pure - Premium jewelry standard',
    '22K Gold': '91.7% pure - High-end, investment grade',
    '24K Gold': '99.9% pure - Pure gold, very soft',
    'Silver (925)': '92.5% pure - Sterling silver standard',
    'Platinum (950)': '95.0% pure - Luxury jewelry material',
    'Platinum (900)': '90.0% pure - Alternative platinum alloy',
    'Palladium': '95.0% pure - Lighter platinum alternative',
    'White Gold (18K)': '75.0% pure - Gold with white metals',
    'Rose Gold (18K)': '75.0% pure - Gold with copper',
}

# Core functions
def calculate_stl_volume(stl_mesh):
    """Calculate volume using signed tetrahedra method."""
    volume = 0.0
    for triangle in stl_mesh.vectors:
        A, B, C = triangle[0], triangle[1], triangle[2]
        volume += np.dot(A, np.cross(B, C))
    return abs(volume) / 6.0

def calculate_weight(volume_mm3, material_name):
    """Calculate weight from volume and material."""
    return volume_mm3 * MATERIAL_DENSITIES[material_name]

def get_mesh_statistics(stl_mesh):
    """Get comprehensive mesh statistics."""
    all_points = stl_mesh.vectors.reshape(-1, 3)
    return {
        'num_triangles': len(stl_mesh.vectors),
        'min_coords': all_points.min(axis=0),
        'max_coords': all_points.max(axis=0),
        'dimensions': all_points.max(axis=0) - all_points.min(axis=0),
        'surface_area': stl_mesh.areas.sum(),
        'center': all_points.mean(axis=0)
    }

def create_3d_viewer(stl_mesh, volume, filename="model.stl", selected_material=None):
    """Create an interactive 3D viewer with weight information."""
    stats = get_mesh_statistics(stl_mesh)
    
    # Prepare mesh data
    vertices = stl_mesh.vectors.reshape(-1, 3)
    n_tri = len(stl_mesh.vectors)
    i = np.arange(0, n_tri * 3, 3)
    j = np.arange(1, n_tri * 3, 3)
    k = np.arange(2, n_tri * 3, 3)
    
    # Create figure
    fig = go.Figure()
    
    # Determine color based on selected material
    mesh_color = MATERIAL_COLORS.get(selected_material, '#FFD700') if selected_material else '#FFD700'
    
    # Add 3D mesh
    fig.add_trace(
        go.Mesh3d(
            x=vertices[:, 0],
            y=vertices[:, 1],
            z=vertices[:, 2],
            i=i, j=j, k=k,
            color=mesh_color,
            opacity=0.95,
            flatshading=False,
            lighting=dict(
                ambient=0.6,
                diffuse=0.9,
                specular=0.8,
                roughness=0.2,
                fresnel=0.5
            ),
            lightposition=dict(x=100, y=100, z=100),
            hovertemplate='<b>Coordinates</b><br>X: %{x:.2f} mm<br>Y: %{y:.2f} mm<br>Z: %{z:.2f} mm<extra></extra>',
            name='3D Model'
        )
    )
    
    # Update scene
    fig.update_scenes(
        xaxis=dict(
            title='X (mm)',
            backgroundcolor='rgb(20, 20, 30)',
            gridcolor='rgba(255, 215, 0, 0.1)',
            showbackground=True,
            zerolinecolor='rgba(255, 215, 0, 0.3)'
        ),
        yaxis=dict(
            title='Y (mm)',
            backgroundcolor='rgb(20, 20, 30)',
            gridcolor='rgba(255, 215, 0, 0.1)',
            showbackground=True,
            zerolinecolor='rgba(255, 215, 0, 0.3)'
        ),
        zaxis=dict(
            title='Z (mm)',
            backgroundcolor='rgb(20, 20, 30)',
            gridcolor='rgba(255, 215, 0, 0.1)',
            showbackground=True,
            zerolinecolor='rgba(255, 215, 0, 0.3)'
        ),
        camera=dict(
            eye=dict(x=1.5, y=1.5, z=1.3),
            center=dict(x=0, y=0, z=0),
            up=dict(x=0, y=0, z=1)
        ),
        aspectmode='data',
        bgcolor='rgb(15, 15, 25)'
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': f"<b>{filename}</b>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#f0e6d2', 'family': 'Cormorant Garamond'}
        },
        showlegend=False,
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=50, b=0),
        font=dict(family='Space Mono', color='#c0c0c0')
    )
    
    return fig, stats

def create_comparison_chart(volume):
    """Create a bar chart comparing weights across materials."""
    materials = list(MATERIAL_DENSITIES.keys())
    weights = [calculate_weight(volume, m) for m in materials]
    colors = [MATERIAL_COLORS[m] for m in materials]
    
    fig = go.Figure(data=[
        go.Bar(
            x=materials,
            y=weights,
            marker=dict(
                color=colors,
                line=dict(color='#1a1a2e', width=2)
            ),
            text=[f"{w:.3f}g" for w in weights],
            textposition='outside',
            textfont=dict(size=12, color='#f0e6d2', family='Space Mono'),
            hovertemplate='<b>%{x}</b><br>Weight: %{y:.4f}g<br>Troy oz: %{customdata:.4f}<extra></extra>',
            customdata=[w / 31.1035 for w in weights]
        )
    ])
    
    fig.update_layout(
        title={
            'text': f"<b>Material Weight Comparison</b><br><sub>Volume: {volume:.2f} mm³</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#f0e6d2', 'family': 'Cormorant Garamond'}
        },
        xaxis_title="<b>Material</b>",
        yaxis_title="<b>Weight (grams)</b>",
        height=500,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Space Mono', color='#c0c0c0', size=11),
        xaxis=dict(
            tickangle=-45,
            gridcolor='rgba(255, 215, 0, 0.1)'
        ),
        yaxis=dict(
            gridcolor='rgba(255, 215, 0, 0.1)'
        )
    )
    
    return fig

# Main app
def main():
    # Header
    st.markdown("""
        <h1 style='text-align: center; margin-bottom: 0;'>💎 STL Weight Calculator</h1>
        <p style='text-align: center; color: #c0c0c0; font-family: "Space Mono", monospace; font-size: 1.1rem;'>
            Professional 3D Viewer for Precious Metal Weight Analysis
        </p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Material selection
        selected_material = st.selectbox(
            "Primary Material",
            options=list(MATERIAL_DENSITIES.keys()),
            index=1,  # Default to 18K Gold
            help="Select the primary material for weight calculation"
        )
        
        st.info(f"**{selected_material}**\n\n{MATERIAL_INFO[selected_material]}")
        
        # Unit system
        st.markdown("### 📏 Unit System")
        unit_system = st.radio(
            "Display units",
            ["Metric (g)", "Troy (oz)", "Both"],
            index=2
        )
        
        # Additional options
        st.markdown("### 🎨 Display Options")
        show_wireframe = st.checkbox("Show mesh wireframe", value=False)
        show_comparison = st.checkbox("Show material comparison", value=True)
        
        # Information
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        Upload an STL file to calculate its weight in various precious metals.
        
        **Formula:**
        ```
        Weight = Volume × Density
        ```
        
        **Requirements:**
        - STL file in millimeters
        - Watertight mesh (no holes)
        - Binary or ASCII format
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload
        st.markdown("### 📤 Upload STL File")
        uploaded_file = st.file_uploader(
            "Choose an STL file",
            type=['stl'],
            help="Upload your 3D model in STL format",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.stl') as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_path = tmp_file.name
            
            try:
                # Load mesh
                with st.spinner('Loading 3D model...'):
                    stl_mesh = mesh.Mesh.from_file(tmp_path)
                
                # Calculate volume
                with st.spinner('Calculating volume...'):
                    volume = calculate_stl_volume(stl_mesh)
                
                # Create viewer
                fig_3d, stats = create_3d_viewer(
                    stl_mesh, 
                    volume, 
                    uploaded_file.name,
                    selected_material
                )
                
                # Display 3D viewer
                st.plotly_chart(fig_3d, use_container_width=True)
                
                # Model statistics
                with st.expander("📊 Model Statistics", expanded=True):
                    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                    
                    with stat_col1:
                        st.metric("Triangles", f"{stats['num_triangles']:,}")
                    
                    with stat_col2:
                        st.metric("Volume", f"{volume:.2f} mm³")
                    
                    with stat_col3:
                        st.metric("Surface Area", f"{stats['surface_area']:.2f} mm²")
                    
                    with stat_col4:
                        dimensions = stats['dimensions']
                        st.metric("Dimensions", 
                                 f"{dimensions[0]:.1f}×{dimensions[1]:.1f}×{dimensions[2]:.1f} mm")
                
                # Weight calculations
                st.markdown("---")
                st.markdown("### ⚖️ Weight Analysis")
                
                # Tabs for different views
                tab1, tab2, tab3 = st.tabs(["📋 Detailed Table", "📊 Comparison Chart", "🧮 Calculator"])
                
                with tab1:
                    # Create detailed weight table
                    weight_data = []
                    for material, density in MATERIAL_DENSITIES.items():
                        weight_g = calculate_weight(volume, material)
                        troy_oz = weight_g / 31.1035
                        dwt = weight_g / 1.55517
                        
                        weight_data.append({
                            'Material': material,
                            'Density (g/mm³)': f"{density:.4f}",
                            'Weight (g)': f"{weight_g:.4f}",
                            'Troy oz': f"{troy_oz:.4f}",
                            'Pennyweight': f"{dwt:.4f}",
                            'Info': MATERIAL_INFO[material]
                        })
                    
                    import pandas as pd
                    df = pd.DataFrame(weight_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                
                with tab2:
                    if show_comparison:
                        fig_comparison = create_comparison_chart(volume)
                        st.plotly_chart(fig_comparison, use_container_width=True)
                
                with tab3:
                    st.markdown("#### Quick Weight Calculator")
                    calc_material = st.selectbox(
                        "Material",
                        options=list(MATERIAL_DENSITIES.keys()),
                        index=list(MATERIAL_DENSITIES.keys()).index(selected_material),
                        key="calc_material"
                    )
                    
                    calc_volume = st.number_input(
                        "Volume (mm³)",
                        min_value=0.0,
                        value=float(volume),
                        step=0.1,
                        format="%.2f"
                    )
                    
                    calc_weight = calculate_weight(calc_volume, calc_material)
                    calc_troy = calc_weight / 31.1035
                    calc_dwt = calc_weight / 1.55517
                    
                    result_col1, result_col2, result_col3 = st.columns(3)
                    with result_col1:
                        st.metric("Grams", f"{calc_weight:.4f}")
                    with result_col2:
                        st.metric("Troy Ounces", f"{calc_troy:.4f}")
                    with result_col3:
                        st.metric("Pennyweight", f"{calc_dwt:.4f}")
                
                # Cleanup
                os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"Error processing STL file: {str(e)}")
                os.unlink(tmp_path)
        
        else:
            # Show sample information
            st.info("👆 Upload an STL file to begin analysis")
            
            st.markdown("""
            ### 🎯 What This Tool Does
            
            This professional calculator analyzes your 3D models and calculates their weight in various precious metals:
            
            - **Accurate Volume Calculation** using signed tetrahedra method
            - **Multiple Material Support** including gold, silver, platinum, and palladium
            - **Interactive 3D Visualization** with real-time rotation and zoom
            - **Comprehensive Weight Analysis** in multiple unit systems
            - **Professional Grade** calculations for jewelry and precious metal industry
            
            ### 🚀 Getting Started
            
            1. Upload your STL file (must be in millimeters)
            2. Select your primary material from the sidebar
            3. View your 3D model and weight calculations
            4. Compare weights across different materials
            
            ### 💡 Pro Tips
            
            - Ensure your STL mesh is watertight (closed, no holes)
            - Use millimeters as your unit in the 3D modeling software
            - Higher triangle count = more accurate volume calculation
            - Check the model statistics to verify dimensions
            """)
    
    with col2:
        # Material reference card
        st.markdown("### 💎 Material Reference")
        
        for material in ['18K Gold', 'Silver (925)', 'Platinum (950)']:
            with st.container():
                st.markdown(f"""
                <div style='background: rgba(255, 215, 0, 0.05); 
                            border-left: 4px solid {MATERIAL_COLORS[material]}; 
                            padding: 15px; 
                            margin-bottom: 15px;
                            border-radius: 8px;'>
                    <h4 style='margin: 0; color: {MATERIAL_COLORS[material]};'>{material}</h4>
                    <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>{MATERIAL_INFO[material]}</p>
                    <p style='margin: 5px 0; color: #ffd700; font-family: "Space Mono"; font-weight: 700;'>
                        {MATERIAL_DENSITIES[material]:.4f} g/mm³
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        # Quick reference
        st.markdown("### 📏 Unit Conversions")
        st.markdown("""
        - **1 troy oz** = 31.1035 grams
        - **1 pennyweight** = 1.55517 grams
        - **1 gram** = 0.643 pennyweight
        - **1 cm³** = 1000 mm³
        """)
        
        # Formula reference
        st.markdown("### 🧮 Calculation Method")
        st.latex(r"\text{Weight} = \text{Volume} \times \text{Density}")
        st.latex(r"V_{total} = \sum_{i=1}^{n} \frac{1}{6} (\mathbf{A}_i \cdot (\mathbf{B}_i \times \mathbf{C}_i))")
        
        st.markdown("""
        <p style='font-size: 0.85rem; color: #c0c0c0; font-style: italic;'>
        Volume is calculated using the signed tetrahedra method for maximum accuracy.
        </p>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
