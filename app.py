# -*- coding: utf-8 -*-
"""
Created on Mon Sep 22 12:14:25 2025

@author: geoti
"""

from folium.plugins import Fullscreen
import streamlit as st
import geopandas as gpd
import folium
import pandas as pd
from streamlit_folium import folium_static
import plotly.express as px
from datetime import datetime
from folium.plugins import MarkerCluster

st.set_page_config(layout='wide', initial_sidebar_state='expanded')
img_logo = "geotig_logo.PNG"
img_icon = "geotig_icon.png"
st.logo(img_logo, icon_image=img_icon)

tab1, tab2 = st.tabs(["Datos", "Informacion Fundos"])

@st.cache_data
def cargar_ncr():
    ncr = gpd.read_file("MB_V_L_FUNDO_NCR.geojson")
    return ncr

# Diccionario de colores según categoría
lyr_ncr = {
    "Muy Alto": "red",
    "Alto": "orange",
    "Medio": "yellow",
    "Bajo": "yellowgreen",
    "Muy Bajo": "green"
}

@st.cache_data
def cargar_barrios():
    barrios = gpd.read_file("Area_Barrios.geojson")
    return barrios

@st.cache_data
def cargar_datos():
    df = pd.read_csv("FUNDOS_COMPLEJIDADyRIESGO.csv", sep=";")
    return df

@st.cache_data
def cargar_pts():
    pts = gpd.read_file("consolidado_pts.geojson")
    pts["D_FECHA"] = pd.to_datetime(pts["D_FECHA"], errors="coerce")
    return pts

df = cargar_datos()
ncr = cargar_ncr()
barrios = cargar_barrios()
incidentes = cargar_pts()

ncr_df = ncr.merge(df, how="left", left_on="COD_FUNDO", right_on="COD_FUNDO")
lista_fundos = pd.Series(df['COD_FUNDO'].drop_duplicates()).sort_values(ascending=True).tolist()
lista_barrios = df['Barrio'].drop_duplicates().sort_values(ascending=True).tolist()
lista_comunas = df['NOM_COMUNA'].drop_duplicates().sort_values(ascending=True).tolist()
lista_ncr = df['NCR'].drop_duplicates().sort_values(ascending=True).tolist()
lista_incidentes = incidentes['TIPO'].drop_duplicates().sort_values(ascending=True).tolist()

# ======= FORMULARIO DE FILTROS =======
with st.sidebar:
    with st.form("filtros_form"):
        st.markdown("### 🔍 Filtros")
        
        with st.expander("Filtros generales", expanded=True):
            barrio_select = st.multiselect(
                'Seleccionar barrio:',
                options=lista_barrios,
                default=[],
                help="Selecciona un barrio"
            )

            comuna_select = st.multiselect(
                'Seleccionar comuna:',
                options=lista_comunas,
                default=[],
                help="Selecciona una comuna"
            )

            ncr_select = st.multiselect(
                'Seleccionar por NCR:',
                options=lista_ncr,
                default=[],
                help="Selecciona una categoría"
            )

        with st.expander("Filtrar fundos", expanded=False):
            fundo = st.multiselect(
                'Seleccionar fundo:',
                options=lista_fundos,
                default=[],
                help="Selecciona un fundo"
            )
            
        with st.expander("Filtrar incidentes", expanded=False):
            # Fechas base
            fecha_min = datetime(2022, 1, 1)
            fecha_hoy = datetime.today().replace(day=1)
            fecha_7m = (fecha_hoy - pd.DateOffset(months=7)).to_pydatetime()
            
            # Lista de meses en formato YYYY-MM
            meses = pd.date_range(start=fecha_min, end=fecha_hoy, freq="MS").strftime("%Y-%m").tolist()
            
            # Selector de rango de meses
            mes_ini, mes_fin = st.select_slider(
                "Selecciona rango de meses:",
                options=meses,
                value=(fecha_7m.strftime("%Y-%m"), fecha_hoy.strftime("%Y-%m"))
            )
            
            # Selección múltiple de tipos de incidentes
            lista_incidentes_sorted = sorted(incidentes["TIPO"].dropna().unique().tolist())
            selection = st.pills(
                "Tipo de incidente",
                lista_incidentes_sorted,
                selection_mode="multi",
                default=lista_incidentes_sorted
            )
        
        # Botones fuera de los expanders
        st.markdown("---")
        submitted = st.form_submit_button(
            "🔍 Aplicar Filtros", 
            type="primary",
            use_container_width=True
        )
        
        clear_filters = st.form_submit_button(
            "🗑️ Limpiar Filtros", 
            use_container_width=True
        )

# Si se presiona limpiar filtros, resetear todo
if clear_filters:
    barrio_select = []
    comuna_select = []
    ncr_select = []
    fundo = []
    selection = lista_incidentes_sorted
    mes_ini = fecha_7m.strftime("%Y-%m")
    mes_fin = fecha_hoy.strftime("%Y-%m")

# Si no se han aplicado filtros aún, usar valores por defecto
if not submitted and not clear_filters:
    # Valores por defecto para la primera carga
    barrio_select = []
    comuna_select = []
    ncr_select = []
    fundo = []
    selection = lista_incidentes_sorted
    mes_ini = fecha_7m.strftime("%Y-%m")
    mes_fin = fecha_hoy.strftime("%Y-%m")

# Mostrar estado actual de filtros
with st.sidebar:
    if submitted:
        # Mostrar resumen de filtros activos
        filtros_activos = []
        if barrio_select:
            filtros_activos.append(f"Barrios: {len(barrio_select)}")
        if comuna_select:
            filtros_activos.append(f"Comunas: {len(comuna_select)}")
        if ncr_select:
            filtros_activos.append(f"NCR: {len(ncr_select)}")
        if fundo:
            filtros_activos.append(f"Fundos: {len(fundo)}")
        if selection != lista_incidentes_sorted:
            filtros_activos.append(f"Incidentes: {len(selection)}")
            
        if filtros_activos:
            st.info("**Filtros activos:**\n" + "\n".join([f"• {filtro}" for filtro in filtros_activos]))
    
    st.markdown("---")
    st.image(img_logo, caption="Geotig SpA")

# ======= PROCESAMIENTO DE DATOS CON FILTROS =======

# Convertir fechas y preparar datos
ini = pd.to_datetime(mes_ini, format="%Y-%m")
fin = pd.to_datetime(mes_fin, format="%Y-%m")
rango_meses = pd.date_range(ini, fin, freq="MS").strftime("%Y-%m").tolist()

incidentes["FECHA"] = incidentes["D_FECHA"].dt.strftime("%Y-%m").astype(str)
pts_folium = incidentes.drop("D_FECHA", axis=1)

# Aplicar filtros a incidentes
pts_lyr = pts_folium.copy()
pts_lyr = pts_lyr[pts_lyr["FECHA"].isin(rango_meses)]
if selection:
    pts_lyr = pts_lyr[pts_lyr["TIPO"].isin(selection)]
if barrio_select:
    pts_lyr = pts_lyr[pts_lyr["NOM_BARRIO"].isin(barrio_select)]

def create_map():
    bounds = ncr_df.total_bounds
    m = folium.Map()

    Fullscreen(
        position='topleft',
        title='Pantalla completa',
        title_cancel='Salir pantalla completa',
        force_separate_button=True
    ).add_to(m)

    # Filtro para zoom
    selected = ncr_df.copy()
    if len(fundo) > 0 or len(barrio_select) > 0 or len(comuna_select) > 0 or len(ncr_select) > 0:
        selected = selected[
            (selected["COD_FUNDO"].isin(fundo)) |
            (selected["Barrio"].isin(barrio_select)) |
            (selected["NOM_COMUNA"].isin(comuna_select)) |
            (selected["NCR"].isin(ncr_select))
        ]

    if not selected.empty:
        selected_bounds = selected.total_bounds
        m.fit_bounds([[selected_bounds[1], selected_bounds[0]],
                      [selected_bounds[3], selected_bounds[2]]])
    else:
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Agregar barrios
    folium.GeoJson(
        barrios,
        name="Barrios",
        style_function=lambda feature: {
            "color": "grey",
            "weight": 1,
            "fillOpacity": 0.5,
        },
        popup=folium.GeoJsonPopup(
            fields=["NOM_AREA", "NOM_BARRIO"],
            aliases=["Area:", "Barrio:"],
            localize=True
        )
    ).add_to(m)

    # Estilo condicional de fundos
    def style_function(feature):
        fundo_name = feature["properties"]["COD_FUNDO"]
        barrio_name = feature["properties"].get("Barrio", "")
        comuna_name = feature["properties"].get("NOM_COMUNA", "")
        ncr_name = feature["properties"].get("NCR", "")

        selected_fundo = str(fundo_name) in [str(f) for f in fundo] if fundo else False
        selected_barrio = str(barrio_name) in [str(b) for b in barrio_select] if barrio_select else False
        selected_comuna = str(comuna_name) in [str(c) for c in comuna_select] if comuna_select else False
        selected_ncr = str(ncr_name) in [str(n) for n in ncr_select] if ncr_select else False

        if len(fundo) == 0 and len(barrio_select) == 0 and len(comuna_select) == 0 and len(ncr_select) == 0:
            # Sin filtros → colores NCR normales
            return {
                "fillColor": lyr_ncr.get(feature["properties"]["NCR"], "gray"),
                "color": "black",
                "weight": 0.3,
                "fillOpacity": 1,
                "opacity": 1
            }
        elif selected_fundo or selected_barrio or selected_comuna or selected_ncr:
            # Selección → resaltado
            return {
                "fillColor": lyr_ncr.get(feature["properties"]["NCR"], "gray"),
                "color": "red",
                "weight": 1.5,
                "fillOpacity": 1,
                "opacity": 1
            }
        else:
            # No seleccionado → atenuado
            return {
                "fillColor": "gray",
                "color": "black",
                "weight": 0.3,
                "fillOpacity": 0.3,
                "opacity": 0.3
            }

    # Agregar fundos
    folium.GeoJson(
        ncr_df,
        name="Fundos FORMIN",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["COD_FUNDO", "NOM_FUNDO", "Area", "Barrio", "NCR", "NOM_COMUNA"],
            aliases=["COD FUNDO:", "NOM FUNDO:", "Area:", "Barrio:", "NCR:", "Comuna:"],
            localize=True
        )
    ).add_to(m)
    
    # agregar puntos
    mc = MarkerCluster(name="Incidentes").add_to(m)
    
    for _, row in pts_lyr.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=4,
            color="blue",
            fill=True,
            fillOpacity=0.8,
            popup=folium.Popup(
                f"""
                <b>Categoría:</b> {row.get('TIPO', '')}<br>
                <b>Fecha:</b> {row.get('FECHA', '')}<br>
                <b>Empresa:</b> {row.get('INTERNO', '')}
                """,
                max_width=300
            )
        ).add_to(mc)
    
    # Añadir el grupo al mapa
    mc.add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)

    return m

def show_map():
    m = create_map()
    folium_static(m, width=1000, height=600)

df_columnas = df[[
    "COD_FUNDO", "NOM_FUNDO", "DSC_SUBGER", "DSC_Z_ADM_", 
    "NOM_REGION", "NOM_PROVIN", "NOM_COMUNA", "Area", 
    "Barrio", "NCR", "JefeSector"
]]

with tab1:
    c1_f1, c2_f1 = st.columns([10, 5])
    
    with c2_f1:
        t1_df, t2_df = st.tabs(["Info. fundos", "Info. incidentes"])
        with t1_df:
            df_resumido = df_columnas.copy()
            if len(fundo) > 0 or len(barrio_select) > 0 or len(comuna_select) > 0 or len(ncr_select) > 0:
                df_resumido = df_resumido[
                    (df_resumido["COD_FUNDO"].isin(fundo)) |
                    (df_resumido["Barrio"].isin(barrio_select)) |
                    (df_resumido["NOM_COMUNA"].isin(comuna_select)) |
                    (df_resumido["NCR"].isin(ncr_select))
                ]
            
            st.dataframe(df_resumido, hide_index=True, use_container_width=True)
        with t2_df:
            df_incidentes = pd.DataFrame(pts_lyr.drop(columns="geometry"))
            st.dataframe(df_incidentes, hide_index=True, use_container_width=True)               
        
        # Cuenta número de fundos por NCR
        counts = df_resumido["NCR"].value_counts().reset_index()
        counts.columns = ["NCR", "Fundos"]
        
        fig = px.pie(
            counts,
            names="NCR",
            values="Fundos",
            color="NCR",
            color_discrete_map={
                "Muy Alto": "red",
                "Alto": "orange",
                "Medio": "yellow",
                "Bajo": "yellowgreen",
                "Muy Bajo": "green"
            }
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(title="Distribución de fundos según NCR")
        
        config = {
            "displayModeBar": False,
            "displaylogo": False
        }
        
        st.plotly_chart(fig, use_container_width=True, config=config)
        
        
    with c1_f1:
        map_container = st.container()
        chart_container = st.container()
        
        with chart_container:
            fig = px.histogram(
                df_incidentes, 
                x="FECHA", 
                color="TIPO",
                nbins=10,
                title="Incidentes por tipo"
            )
            fig.update_layout(bargap=0.3)

            st.plotly_chart(fig, use_container_width=True, config=config)
        
        with map_container:
            st.subheader("Mapa interactivo", help="Puede tardar en cargar", anchor=False, divider="green")
            with st.spinner("Cargando mapa..."):
                show_map()
    
with tab2:
    df_filtrado = df.copy()
    if len(fundo) > 0 or len(barrio_select) > 0 or len(comuna_select) > 0 or len(ncr_select) > 0:
        df_filtrado = df[
            (df["COD_FUNDO"].isin(fundo)) |
            (df["Barrio"].isin(barrio_select)) |
            (df["NOM_COMUNA"].isin(comuna_select)) |
            (df["NCR"].isin(ncr_select))
        ]

    st.markdown("Información del excel entregado:")
    st.dataframe(df_filtrado, hide_index=True)










