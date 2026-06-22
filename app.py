%%writefile app.py

import base64
import re
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
st.set_page_config(
    page_title="Busca de Novos Pacientes Oncológicos - Operações",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#0f3d6e"      # cabeçalhos cards/tabelas
SIDEBAR = "#173b51"      # barra lateral
ACCENT = "#2f80ed"       # azul destaque
LIGHT_BG = "#ffffff"     # fundo painel
HEADER_BG = "#dce5eb"    # barra superior clara
BORDER = "#d7e2ef"
TEXT = "#000000"         # textos pretos, sem formatação especial

ROOT = Path(__file__).parent
ASSETS = ROOT / "assets"

# Nomes esperados na pasta assets:
# logo_kora, Filtro, Atualizar, Casa, Seta Direita, Seta Esquerda
def find_asset(stem: str) -> Path | None:
    for ext in [".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG", ".webp", ".WEBP", ".svg", ".SVG"]:
        p = ASSETS / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def img_to_base64(path: Path | None) -> str:
    if not path or not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def asset_data_uri(stem: str) -> str:
    path = find_asset(stem)
    if not path:
        return ""
    ext = path.suffix.lower().replace(".", "")
    mime = "svg+xml" if ext == "svg" else ext
    return f"data:image/{mime};base64,{img_to_base64(path)}"


LOGO_URI = asset_data_uri("logo_kora")
FILTRO_URI = asset_data_uri("Filtro")
ATUALIZAR_URI = asset_data_uri("Atualizar")
CASA_URI = asset_data_uri("Casa")
SETA_DIREITA_URI = asset_data_uri("Seta Direita")
SETA_ESQUERDA_URI = asset_data_uri("Seta Esquerda")

# ============================================================
# ESTADOS
# ============================================================
if "page" not in st.session_state:
    st.session_state.page = "Busca de Pacientes"

if "filters_open" not in st.session_state:
    st.session_state.filters_open = False

SIDEBAR_WIDTH = "320px" if st.session_state.filters_open else "78px"

# Ícone de navegação: na primeira aba aparece seta direita; na segunda, seta esquerda.
NAV_ICON_URI = SETA_DIREITA_URI if st.session_state.page == "Busca de Pacientes" else SETA_ESQUERDA_URI

# ============================================================
# CSS GLOBAL
# ============================================================
st.markdown(
    f"""
    <style>
    .stApp {{
        background: {LIGHT_BG};
        color: #000000 !important;
    }}

    html, body, [class*="css"] {{
        color: #000000 !important;
    }}

    div[data-testid="stToolbar"],
    header[data-testid="stHeader"] {{
        display: none;
    }}

    /* Impede que a barra lateral nativa do Streamlit seja recolhida/suma */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    button[data-testid="stSidebarCollapseButton"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"] {{
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }}

    .block-container {{
        padding-top: 0.85rem;
        padding-left: 1.2rem;
        padding-right: 1.2rem;
        padding-bottom: 5rem;
        max-width: 100%;
    }}

    /* ========================================================
       SIDEBAR / BARRA LATERAL
       ======================================================== */
    [data-testid="stSidebar"] {{
        background: {SIDEBAR};
        width: {SIDEBAR_WIDTH} !important;
        min-width: {SIDEBAR_WIDTH} !important;
        max-width: {SIDEBAR_WIDTH} !important;
        border-right: 1px solid rgba(255,255,255,.20);
        overflow-x: hidden;
        overflow-y: auto;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        width: {SIDEBAR_WIDTH} !important;
        min-width: {SIDEBAR_WIDTH} !important;
        max-width: {SIDEBAR_WIDTH} !important;
        padding: 0.35rem 0rem !important;
        overflow-x: hidden;
        overflow-y: auto;
    }}

    [data-testid="stSidebar"] * {{
        color: #ffffff !important;
    }}

    [data-testid="stSidebar"] hr {{
        margin: 14px 0;
        border-color: rgba(255,255,255,.15);
    }}

    [data-testid="stSidebar"]::-webkit-scrollbar,
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar {{
        width: 7px;
    }}

    [data-testid="stSidebar"]::-webkit-scrollbar-thumb,
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {{
        background: rgba(255,255,255,.32);
        border-radius: 8px;
    }}

    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stDateInput input {{
        background-color: rgba(255,255,255,.08) !important;
        border: 1px solid rgba(255,255,255,.38) !important;
        border-radius: 2px !important;
        min-height: 34px !important;
    }}

    .date-range-row {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        margin-top: 4px;
        margin-bottom: 8px;
    }}

    .date-box {{
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.38);
        color: #ffffff !important;
        height: 28px;
        min-height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        box-sizing: border-box;
    }}

    .date-slider {{
        position: relative;
        height: 22px;
        margin: 2px 0 12px 0;
        border-top: 2px solid rgba(255,255,255,.78);
    }}

    .date-dot {{
        position: absolute;
        top: -7px;
        width: 13px;
        height: 13px;
        background: #ffffff;
        border-radius: 50%;
    }}

    .date-dot.left {{
        left: 0%;
    }}

    .date-dot.right {{
        left: 28%;
    }}

    /* Botões normais da gaveta aberta */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        height: 36px;
        min-height: 36px;
        border-radius: 3px !important;
        border: 1px solid rgba(255,255,255,.28) !important;
        background: {ACCENT} !important;
        color: #ffffff !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        margin: 8px 0 !important;
    }}

    /* Barra fina com botões de imagem nativos do Streamlit.
       Largura aumentada e centralização forçada para evitar PNG cortado. */
    .rail {{
        width: 100%;
        min-width: 70px;
        max-width: 70px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding-top: 6px;
        margin: 0 auto;
        overflow: visible !important;
    }}

    .rail-logo-wrap {{
        width: 54px;
        height: 42px;
        margin: 0 auto 8px auto;
        padding: 0 0 7px 0;
        border-bottom: 1px solid rgba(255,255,255,.32);
        display: flex;
        align-items: center;
        justify-content: center;
        box-sizing: content-box;
        overflow: visible !important;
    }}

    .rail-logo {{
        width: 31px;
        height: 31px;
        object-fit: contain;
        display: block;
        transform: translateX(0px);
        transform-origin: center center;
    }}

    .rail-fallback {{
        width: 46px;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff !important;
        font-size: 24px;
        margin: 0 auto 8px auto;
        padding-bottom: 7px;
        border-bottom: 1px solid rgba(255,255,255,.32);
    }}

    .st-key-btn_open_filters,
    .st-key-btn_refresh,
    .st-key-btn_home,
    .st-key-btn_nav_page {{
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }}

    .st-key-btn_open_filters button,
    .st-key-btn_refresh button,
    .st-key-btn_home button,
    .st-key-btn_nav_page button {{
        width: 54px !important;
        min-width: 54px !important;
        max-width: 54px !important;
        height: 42px !important;
        min-height: 42px !important;
        padding: 0 !important;
        margin: 0 auto 8px auto !important;
        border-radius: 0 !important;
        border: none !important;
        border-bottom: 1px solid rgba(255,255,255,.32) !important;
        background-color: transparent !important;
        background-repeat: no-repeat !important;
        background-position: center center !important;
        background-size: 28px 28px !important;
        box-shadow: none !important;
        overflow: visible !important;
        color: transparent !important;
        font-size: 0 !important;
        line-height: 0 !important;
        text-indent: -9999px !important;
        transform: none !important;
    }}

    .st-key-btn_open_filters button p,
    .st-key-btn_refresh button p,
    .st-key-btn_home button p,
    .st-key-btn_nav_page button p,
    .st-key-btn_open_filters button div,
    .st-key-btn_refresh button div,
    .st-key-btn_home button div,
    .st-key-btn_nav_page button div,
    .st-key-btn_open_filters button span,
    .st-key-btn_refresh button span,
    .st-key-btn_home button span,
    .st-key-btn_nav_page button span {{
        display: none !important;
        visibility: hidden !important;
        color: transparent !important;
        font-size: 0 !important;
        line-height: 0 !important;
        width: 0 !important;
        height: 0 !important;
    }}

    .st-key-btn_open_filters button:hover,
    .st-key-btn_refresh button:hover,
    .st-key-btn_home button:hover,
    .st-key-btn_nav_page button:hover {{
        background-color: rgba(255,255,255,.08) !important;
    }}

    .st-key-btn_open_filters button {{
        background-image: url("{FILTRO_URI}") !important;
    }}

    .st-key-btn_refresh button {{
        background-image: url("{ATUALIZAR_URI}") !important;
    }}

    .st-key-btn_home button {{
        background-image: url("{CASA_URI}") !important;
    }}

    .st-key-btn_nav_page button {{
        background-image: url("{NAV_ICON_URI}") !important;
    }}

    /* Ajuste fino: casa estava menor que os demais ícones. */
    .st-key-btn_home button {{
        background-size: 30px 30px !important;
    }}

    .sidebar-logo-wrap {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 8px 4px 16px 4px;
    }}

    .sidebar-logo {{
        width: 35px;
        height: 35px;
        object-fit: contain;
    }}

    .sidebar-title {{
        font-weight: 800;
        font-size: 15px;
        color: #fff;
        line-height: 16px;
    }}

    .sidebar-subtitle {{
        font-size: 10px;
        color: #dce5eb !important;
        margin-top: 2px;
    }}

    .filter-label {{
        font-size: 10px;
        font-weight: 800;
        color: #ffffff !important;
        margin: 12px 0 4px;
        text-transform: uppercase;
    }}

    /* ========================================================
       CABEÇALHO SUPERIOR
       ======================================================== */
    .topbar {{
        background: {HEADER_BG};
        color: #000000 !important;
        border-radius: 0;
        padding: 2px 12px;
        margin: -0.85rem -1.2rem 10px -1.2rem;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        box-shadow: none;
        border-bottom: 1px solid #c5d2dc;
        min-height: 28px;
    }}

    .topbar .date-ref {{
        grid-column: 2;
        justify-self: center;
        align-self: center;
        color: {PRIMARY} !important;
        font-size: 14px;
        line-height: 16px;
        font-weight: 800;
        text-align: center;
        white-space: nowrap;
    }}

    .topbar .title-ref {{
        grid-column: 3;
        justify-self: end;
        align-self: center;
    }}

    .topbar h1 {{
        font-size: 13px;
        margin: 0;
        color: {PRIMARY} !important;
        font-weight: 700;
        letter-spacing: .2px;
        text-transform: uppercase;
        text-align: right;
        white-space: nowrap;
    }}

    /* ========================================================
       COMPONENTES DO DASHBOARD
       ======================================================== */
    .section-title {{
        color: #000000 !important;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: .2px;
        text-transform: uppercase;
        margin: 12px 0 8px 0;
        padding-left: 8px;
        border-left: 4px solid {ACCENT};
    }}

    .metric-card {{
        background: #fff;
        border: 1px solid {BORDER};
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(15,61,110,.10);
        min-height: 72px;
    }}

    .metric-card .metric-head {{
        background: {PRIMARY};
        color: #fff !important;
        padding: 6px 8px;
        font-size: 9px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        text-align: center;
    }}

    .metric-card .metric-body {{
        padding: 8px 10px;
        background: #fff;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 44px;
    }}

    .metric-card .metric-value {{
        color: #000000 !important;
        font-size: 22px;
        line-height: 25px;
        font-weight: 600;
        text-align: center;
        width: 100%;
    }}

    .metric-card .metric-sub {{
        color: #000000 !important;
        font-size: 10px;
        margin-top: 3px;
        text-align: center;
        width: 100%;
    }}

    .acomp-top-row {{
        margin-bottom: 16px;
    }}

    .acomp-top-row .metric-card {{
        min-height: 90px;
    }}

    .acomp-top-row .metric-card .metric-body {{
        min-height: 58px;
    }}

    .acomp-pillar-row {{
        margin-top: 4px;
        margin-bottom: 16px;
    }}

    .acomp-time-row {{
        margin-top: 4px;
        margin-bottom: 18px;
    }}

    .acomp-time-row .metric-card {{
        min-height: 72px;
    }}

    .acomp-time-row .metric-card .metric-body {{
        min-height: 44px;
    }}

    .table-card .scroll-table {{
        max-height: 320px;
    }}

    .mini-box {{
        background: #fff;
        border: 1px solid {BORDER};
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(15,61,110,.08);
    }}

    .mini-box-title {{
        background: {PRIMARY};
        color: #fff !important;
        padding: 8px 12px;
        font-weight: 700;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .2px;
        text-align: center;
    }}

    .mini-metrics {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0;
        background: #fff;
    }}

    .mini-metric {{
        padding: 12px;
        border-right: 1px solid {BORDER};
        text-align: center;
    }}

    .mini-metric:last-child {{
        border-right: none;
    }}

    .mini-label {{
        color: #000000 !important;
        font-size: 10px;
    }}

    .mini-value {{
        color: #000000 !important;
        font-size: 18px;
        font-weight: 600;
        margin-top: 4px;
    }}

    .viz-card {{
        background: #fff;
        border: 1px solid {BORDER};
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(15,61,110,.09);
        margin-bottom: 18px;
    }}

    .viz-title {{
        background: {PRIMARY};
        color: #fff !important;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .2px;
        text-align: center;
    }}

    .viz-scroll-shell {{
        background: #fff;
        border: 1px solid #d7e2ef;
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(15,61,110,.09);
        margin-bottom: 18px;
    }}

    .viz-scroll-title {{
        background: #0f3d6e;
        color: #fff !important;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .2px;
        text-align: center;
    }}

    .table-card {{
        background: #fff;
        border: 1px solid {BORDER};
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(15,61,110,.09);
        margin-bottom: 28px;
    }}

    .table-title {{
        background: {PRIMARY};
        color: #fff !important;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .2px;
        text-align: center;
    }}

    table.mock-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
        color: #000000 !important;
    }}

    table.mock-table thead th {{
        background: #e7eef7;
        color: #000000 !important;
        text-align: left;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .2px;
        padding: 7px 8px;
        border-bottom: 1px solid {BORDER};
        white-space: nowrap;
        position: sticky;
        top: 0;
        z-index: 5;
    }}

    table.mock-table tbody td {{
        padding: 7px 8px;
        border-bottom: 1px solid #e6edf5;
        white-space: nowrap;
        color: #000000 !important;
        font-weight: 400;
        vertical-align: top;
    }}

    table.mock-table tbody td.laudo-cell {{
        white-space: normal !important;
        min-width: 560px;
        max-width: 720px;
        line-height: 1.35;
        overflow: visible !important;
        text-overflow: clip !important;
    }}

    table.mock-table tbody tr:nth-child(even) {{
        background: #f7fafd;
    }}

    .scroll-table {{
        max-height: 360px;
        overflow: auto;
        position: relative;
    }}

    .plain-status {{
        color: #000000 !important;
        background: transparent !important;
        padding: 0;
        border-radius: 0;
        font-size: inherit;
        font-weight: 400;
    }}

    .bottom-nav {{
        position: fixed;
        left: {SIDEBAR_WIDTH};
        right: 0;
        bottom: 0;
        height: 50px;
        background: #f5f8fc;
        border-top: 1px solid {BORDER};
        display: flex;
        align-items: center;
        gap: 8px;
        padding-left: 16px;
        z-index: 99;
    }}

    .tab-card {{
        padding: 10px 20px;
        border-radius: 3px 3px 0 0;
        border: 1px solid {BORDER};
        color: #000000 !important;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: .2px;
        background: #fff;
    }}

    .tab-card-active {{
        background: {ACCENT};
        border-color: {ACCENT};
        color: #ffffff !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# DADOS SIMULADOS
# ============================================================

def money(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def pct(v: float) -> str:
    return f"{v:.1f}%".replace(".", ",")


@st.cache_data
def load_mock_data():
    pacientes = [
        "Mariana Alves Ferreira", "Carlos Eduardo Menezes", "Ana Paula Rodrigues", "Roberto Martins Costa",
        "Juliana Farias Lima", "Fernando Henrique Duarte", "Patrícia Gomes Vieira", "Ricardo Almeida Nunes",
        "Luciana Teixeira Barros", "Bruno Carvalho Santos", "Helena Batista Moreira", "Marcelo Augusto Ribeiro",
        "Camila Lopes Azevedo", "Sérgio Henrique Pinto", "Renata Cristina Moura", "Eduardo Lima Vasconcelos",
        "Tatiane Rocha Campos", "João Pedro Fernandes"
    ]
    medicos = [
        "Dr. Ricardo Almeida", "Dra. Paula Ferreira", "Dr. Carlos Mendes", "Dra. Ana Souza",
        "Dr. Marcos Lima", "Dra. Juliana Costa", "Dr. Felipe Andrade", "Dra. Fernanda Rocha",
        "Dr. Henrique Tavares", "Dra. Marina Albuquerque"
    ]
    contatos = [
        "(27) 99812-3481", "(27) 99731-8842", "(27) 99200-5588", "(27) 98877-1234",
        "(27) 99556-4321", "(27) 99983-2215", "(27) 99654-7810", "(27) 99472-0093",
        "(27) 99123-5309", "(27) 99875-6612"
    ]
    setores = ["Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação"]
    especialidades = ["Oncologia", "Hematologia"]

    laudo_patologia_base = (
        "Cortes histológicos de blocos de parafina rotulados após desparafinização e tratamento para recuperação "
        "de antígenos foram incubados com anticorpos monoclonais/policlonais, juntamente com controles pertinentes. "
        "Em seguida utilizou-se sistema de detecção baseado em polímero em plataforma Dako-Agilent. Perfil "
        "imunoistoquímico: Proteína p53 com padrão selvagem; PMS2 e MSH6 com expressão preservada; Cerb-B2 escore 0; "
        "Ki-67 com expressão aumentada em componente neoplásico. CONCLUSÃO: achados morfológicos e imunoistoquímicos "
        "compatíveis com adenocarcinoma intramucoso/neoplasia maligna, recomendando correlação clínica e seguimento oncológico."
    )
    patologia_df = pd.DataFrame({
        "DATA IDENTIFICAÇÃO": pd.date_range("2025-06-01", periods=10, freq="D").strftime("%d/%m/%Y"),
        "DIAS DESDE A IDENTIFICAÇÃO": list(range(1, 11)),
        "SETOR SOLICITANTE": [setores[i % len(setores)] for i in range(10)],
        "PACIENTE": pacientes[:10],
        "CD. ATENDIMENTO": [str(1328642 + i * 37) for i in range(10)],
        "CD. PACIENTE": [str(40239 + i * 19) for i in range(10)],
        "EXAME PATOLÓGICO": [
            "EXAME ANATOMOPATOLÓGICO", "EXAME IMUNOISTOQUÍMICO", "BIÓPSIA GUIADA POR IMAGEM",
            "ANATOMOPATOLÓGICO DE PEÇA CIRÚRGICA", "PAINEL IMUNOISTOQUÍMICO ONCOLÓGICO",
            "EXAME CITOPATOLÓGICO", "REVISÃO DE LÂMINAS", "EXAME HISTOPATOLÓGICO",
            "IMUNOISTOQUÍMICA COMPLEMENTAR", "ANATOMOPATOLÓGICO DE BIÓPSIA"
        ],
        "LAUDO": [
            laudo_patologia_base,
            laudo_patologia_base.replace("adenocarcinoma intramucoso/neoplasia maligna", "carcinoma invasivo de padrão glandular"),
            laudo_patologia_base.replace("Cerb-B2 escore 0", "HER2 escore 0 e Ki-67 elevado"),
            laudo_patologia_base.replace("padrão selvagem", "padrão alterado em área tumoral"),
            laudo_patologia_base.replace("seguimento oncológico", "avaliação por oncologia clínica"),
            laudo_patologia_base.replace("adenocarcinoma intramucoso/neoplasia maligna", "linfoma de alto grau em amostra analisada"),
            laudo_patologia_base.replace("componente neoplásico", "componente tumoral epitelial"),
            laudo_patologia_base.replace("PMS2 e MSH6", "MLH1, PMS2, MSH2 e MSH6"),
            laudo_patologia_base.replace("correlação clínica", "correlação clínica e radiológica"),
            laudo_patologia_base.replace("plataforma Dako-Agilent", "plataforma automatizada validada")
        ],
        "MALIGNIDADE": ["SIM"] * 10,
        "MÉD. SOLICITANTE": [medicos[i % len(medicos)] for i in range(10)],
        "CONTATO MÉD. SOLICITANTE": [contatos[i % len(contatos)] for i in range(10)],
    })

    laudo_radio_base = (
        "INDICAÇÃO CLÍNICA: tosse e dor torácica. METODOLOGIA: realizados cortes axiais volumétricos, seguidos de "
        "reconstruções multiplanares, sem contraste endovenoso. ANÁLISE: opacidades nodulares consolidativas na periferia "
        "do lobo inferior direito, podendo estar relacionadas a processo inflamatório/infeccioso, porém recomenda-se controle "
        "tomográfico evolutivo. Ausência de derrame pleural. Sem linfonodomegalias mediastinais significativas. OPINIÃO: "
        "achado nodular pulmonar de atenção, sugerindo seguimento clínico."
    )
    radiologia_exames = [
        "TC - CRÂNIO",
        "RX - TÓRAX - 2 INCIDÊNCIAS",
        "TC - ANGIO TÓRAX C/C",
        "US - ECOGRAFIA TRANSVAGINAL",
        "TC - ABDOMEN TOTAL S/C",
        "RX - SEIOS DA FACE",
        "RM - ENCÉFALO C/C",
        "TC - TÓRAX S/C",
        "MAMOGRAFIA BILATERAL",
        "RM - PELVE C/C",
        "TC - ABDOMEN SUPERIOR C/C",
        "RM - MAMAS C/C",
        "US - ABDOMEN TOTAL",
        "TC - PESCOÇO C/C",
        "RX - TÓRAX PA E PERFIL",
        "TC - TÓRAX C/C",
        "RM - COLUNA LOMBAR",
        "US - TIREOIDE",
    ]

    radiologia_laudos = [
        laudo_radio_base,
        laudo_radio_base.replace("lobo inferior direito", "lobo superior esquerdo"),
        laudo_radio_base.replace("Sem linfonodomegalias", "Presença de linfonodomegalias"),
        laudo_radio_base.replace("achado nodular pulmonar", "lesão expansiva anexial"),
        laudo_radio_base.replace("pulmonar", "hepático hipodenso"),
        laudo_radio_base.replace("opacidades nodulares consolidativas", "espessamento mucoso irregular"),
        laudo_radio_base.replace("controle tomográfico evolutivo", "complementação com ressonância magnética"),
        laudo_radio_base.replace("processo inflamatório/infeccioso", "lesão nodular suspeita"),
        laudo_radio_base.replace("dor torácica", "nódulo palpável em mama direita"),
        laudo_radio_base.replace("lobo inferior direito", "região pélvica profunda"),
        laudo_radio_base.replace("tosse e dor torácica", "perda ponderal e dor abdominal").replace("opacidades nodulares consolidativas", "lesão nodular hepática hipovascular"),
        laudo_radio_base.replace("tosse e dor torácica", "rastreamento mamário alterado").replace("achado nodular pulmonar", "realce nodular irregular em mama esquerda"),
        laudo_radio_base.replace("torácica", "abdominal").replace("lobo inferior direito", "retroperitônio").replace("Sem linfonodomegalias", "Linfonodos retroperitoneais aumentados"),
        laudo_radio_base.replace("lobo inferior direito", "cadeia cervical direita").replace("opacidades nodulares consolidativas", "adenomegalias de aspecto suspeito"),
        laudo_radio_base.replace("opacidades nodulares consolidativas", "opacidade persistente em ápice pulmonar direito"),
        laudo_radio_base.replace("sem contraste endovenoso", "com contraste endovenoso").replace("achado nodular pulmonar", "massa pulmonar espiculada"),
        laudo_radio_base.replace("lobo inferior direito", "corpo vertebral L3").replace("opacidades nodulares consolidativas", "lesão óssea lítica expansiva"),
        laudo_radio_base.replace("lobo inferior direito", "lobo tireoidiano esquerdo").replace("opacidades nodulares consolidativas", "nódulo sólido hipoecoico com microcalcificações"),
    ]

    radiologia_df = pd.DataFrame({
        "DATA IDENTIFICAÇÃO": pd.date_range("2025-06-02", periods=18, freq="D").strftime("%d/%m/%Y"),
        "DIAS DESDE A IDENTIFICAÇÃO": list(range(2, 20)),
        "SETOR SOLICITANTE": [setores[(i + 1) % len(setores)] for i in range(18)],
        "PACIENTE": [pacientes[(i + 3) % len(pacientes)] for i in range(18)],
        "CD. ATENDIMENTO": [str(1425010 + i * 43) for i in range(18)],
        "CD. PACIENTE": [str(51280 + i * 23) for i in range(18)],
        "EXAME IMAGEM": radiologia_exames,
        "LAUDO": radiologia_laudos,
        "AVALIAÇÃO IA": [
            "Crítico",
            "Risco Moderado",
            "92%",
            "",
            "88%",
            "Crítico",
            "",
            "Risco Moderado",
            "95%",
            "Crítico",
            "84%",
            "",
            "Risco Moderado",
            "90%",
            "",
            "97%",
            "Crítico",
            "86%",
        ],
        "AVALIAÇÃO PALAVRAS-CHAVE": [
            "nódulo; controle evolutivo",
            "",
            "linfonodomegalia; carcinoma",
            "expansiva; massa anexial",
            "",
            "destruições erosivas",
            "realce anômalo; expansões",
            "",
            "BIRADS 5; carcinoma",
            "massa; invasão local",
            "",
            "lesão irregular; realce nodular",
            "adenomegalia; retroperitônio",
            "",
            "opacidade persistente; ápice pulmonar",
            "massa espiculada; carcinoma",
            "",
            "nódulo sólido; microcalcificações",
        ],
        "MÉD. SOLICITANTE": [medicos[(i + 2) % len(medicos)] for i in range(18)],
        "CONTATO MÉD. SOLICITANTE": [contatos[(i + 2) % len(contatos)] for i in range(18)],
    })

    lab_exames = [
        "HEMOGLOBINA - HEMOGRAMA", "LEUCÓCITOS - HEMOGRAMA", "PLAQUETAS - HEMOGRAMA",
        "BLASTOS CIRCULANTES - HEMOGRAMA", "LINFÓCITOS ATÍPICOS - HEMOGRAMA",
        "CREATININA", "DHL", "CÁLCIO TOTAL", "BETA 2 MICROGLOBULINA",
        "ELETROFORESE DE PROTEINAS", "CADEIA LEVE LIVRE - KAPPA/LAMBDA", "PSA TOTAL E LIVRE"
    ]
    lab_resultados = [
        "8,6 g/dL", "24.800/mm³", "82.000/mm³", "Presente - 6%", "Presente - 4%",
        "2,4 mg/dL", "780 U/L", "11,2 mg/dL", "3,1 mg/L",
        "Proteína monoclonal detectada", "Relação Kappa/Lambda 2,43", "6,8 ng/mL"
    ]
    laboratorio_df = pd.DataFrame({
        "DATA IDENTIFICAÇÃO": pd.date_range("2025-06-03", periods=12, freq="D").strftime("%d/%m/%Y"),
        "DIAS DESDE A IDENTIFICAÇÃO": list(range(3, 15)),
        "SETOR SOLICITANTE": [setores[(i + 2) % len(setores)] for i in range(12)],
        "PACIENTE": pacientes[6:18],
        "CD. ATENDIMENTO": [str(1527001 + i * 31) for i in range(12)],
        "CD. PACIENTE": [str(61840 + i * 17) for i in range(12)],
        "EXAME LABORATORIAL": lab_exames,
        "RESULTADO": lab_resultados,
        "MÉD. SOLICITANTE": [medicos[(i + 4) % len(medicos)] for i in range(12)],
        "CONTATO MÉD. SOLICITANTE": [contatos[(i + 4) % len(contatos)] for i in range(12)],
    })

    naveg = pd.DataFrame({
        "DATA IDENTIFICAÇÃO": [
            "01/06/2025", "02/06/2025", "03/06/2025", "04/06/2025", "05/06/2025",
            "06/06/2025", "07/06/2025", "08/06/2025", "09/06/2025", "10/06/2025",
            "11/06/2025", "12/06/2025", "13/06/2025", "14/06/2025", "15/06/2025",
            "16/06/2025", "17/06/2025", "18/06/2025", "19/06/2025", "20/06/2025"
        ],
        "DATA CONSULTA/TRATAMENTO": [
            "10/06/2025", "16/06/2025", "21/06/2025", "28/06/2025", "18/06/2025",
            "03/07/2025", "19/06/2025", "06/07/2025", "24/06/2025", "10/07/2025",
            "26/06/2025", "14/07/2025", "01/07/2025", "19/07/2025", "04/07/2025",
            "22/07/2025", "08/07/2025", "25/07/2025", "11/07/2025", "29/07/2025"
        ],
        "HOSPITAL": ["HA", "HA", "HFSB", "HA", "HA", "HFSB", "HA", "HA", "HA", "HFSB"] * 2,
        "SETOR SOLICITANTE": [
            "Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação",
            "Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação",
            "Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação",
            "Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação"
        ],
        "ÁREA": [
            "Patologia", "Radiologia", "Laboratório", "Patologia", "Radiologia",
            "Laboratório", "Radiologia", "Patologia", "Laboratório", "Radiologia",
            "Patologia", "Laboratório", "Radiologia", "Patologia", "Laboratório",
            "Radiologia", "Patologia", "Laboratório", "Radiologia", "Patologia"
        ],
        "PACIENTE": [
            "Mariana Alves Ferreira", "Carlos Eduardo Menezes", "Ana Paula Rodrigues", "Roberto Martins Costa",
            "Juliana Farias Lima", "Fernando Henrique Duarte", "Patrícia Gomes Vieira", "Ricardo Almeida Nunes",
            "Luciana Teixeira Barros", "Bruno Carvalho Santos", "Helena Batista Moreira", "Marcelo Augusto Ribeiro",
            "Camila Lopes Azevedo", "Sérgio Henrique Pinto", "Renata Cristina Moura", "Eduardo Lima Vasconcelos",
            "Tatiane Rocha Campos", "João Pedro Fernandes", "Mariana Alves Ferreira", "Carlos Eduardo Menezes"
        ],
        "TIPO ATEND.": ["1ª Consulta", "1º Tratamento"] * 10,
        "CD ATEND.": [
            "1328642", "1328679", "1328716", "1328753", "1328790",
            "1328827", "1425268", "1425311", "1527063", "1425354",
            "1425397", "1527094", "1425440", "1527125", "1425483",
            "1527156", "1328864", "1527187", "1425526", "1328901"
        ],
        "CD PACIENTE": [
            "40239", "40258", "40277", "40296", "40315",
            "40334", "51418", "51441", "61874", "51464",
            "51487", "61891", "51510", "61908", "51533",
            "61925", "40353", "61942", "51556", "40372"
        ],
        "CONVÊNIO": [
            "Bradesco Saúde", "Unimed", "SulAmérica", "Amil", "Notre Dame",
            "Particular", "Vale/PASA", "CASSI", "Saúde Caixa", "Best Senior",
            "Bradesco Saúde", "Unimed", "SulAmérica", "Amil", "Vale/PASA",
            "CASSI", "Saúde Caixa", "Best Senior", "Unimed", "Bradesco Saúde"
        ],
        "MÉD. SOLICITANTE": [
            "Dr. Ricardo Almeida", "Dra. Paula Ferreira", "Dr. Carlos Mendes", "Dra. Ana Souza",
            "Dr. Marcos Lima", "Dra. Juliana Costa", "Dr. Felipe Andrade", "Dra. Fernanda Rocha",
            "Dr. Henrique Tavares", "Dra. Marina Albuquerque", "Dr. Gustavo Pereira", "Dra. Beatriz Nogueira",
            "Dr. Lucas Barbosa", "Dra. Renata Moura", "Dr. Ricardo Almeida", "Dra. Paula Ferreira",
            "Dr. Carlos Mendes", "Dra. Ana Souza", "Dr. Marcos Lima", "Dra. Juliana Costa"
        ],
        "CONTATO MÉD. SOLICITANTE": [
            "(27) 99812-3481", "(27) 99731-8842", "(27) 99200-5588", "(27) 98877-1234",
            "(27) 99556-4321", "(27) 99983-2215", "(27) 99654-7810", "(27) 99472-0093",
            "(27) 99123-5309", "(27) 99875-6612", "(27) 99812-3481", "(27) 99731-8842",
            "(27) 99200-5588", "(27) 98877-1234", "(27) 99556-4321", "(27) 99983-2215",
            "(27) 99654-7810", "(27) 99472-0093", "(27) 99123-5309", "(27) 99875-6612"
        ],
        "ESPECIALIDADE": ["Oncologia", "Hematologia", "Oncologia", "Oncologia", "Hematologia"] * 4,
        "RECEITA": [115.36, 12450, 8730, 95.35, 307.14, 15680, 9870, 425.11, 23450, 567.22, 18500, 22100, 9900, 13200, 17650, 24800, 3100, 6400, 15400, 11900],
    })
    nao_nav = pd.DataFrame({
        "DATA IDENTIFICAÇÃO": ["01/06/2025", "02/06/2025", "03/06/2025", "04/06/2025", "05/06/2025", "06/06/2025", "07/06/2025", "08/06/2025", "09/06/2025", "10/06/2025", "11/06/2025", "12/06/2025"],
        "DATA REGISTRO NÃO NAVEGAÇÃO": ["03/06/2025", "05/06/2025", "05/06/2025", "09/06/2025", "07/06/2025", "11/06/2025", "10/06/2025", "12/06/2025", "13/06/2025", "15/06/2025", "13/06/2025", "17/06/2025"],
        "HOSPITAL": ["HA", "HA", "HFSB", "HA", "HA", "HFSB", "HA", "HA", "HA", "HFSB", "HA", "HA"],
        "SETOR SOLICITANTE": ["Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação", "Urgência", "Eletivo", "Ambulatório", "Centro Cirúrgico", "Internação", "Radiologia", "Laboratório"],
        "ÁREA": ["Patologia", "Radiologia", "Laboratório", "Patologia", "Radiologia", "Laboratório", "Radiologia", "Patologia", "Laboratório", "Radiologia", "Patologia", "Laboratório"],
        "PACIENTE": ["Mariana Alves Ferreira", "Carlos Eduardo Menezes", "Ana Paula Rodrigues", "Roberto Martins Costa", "Juliana Farias Lima", "Fernando Henrique Duarte", "Patrícia Gomes Vieira", "Ricardo Almeida Nunes", "Luciana Teixeira Barros", "Bruno Carvalho Santos", "Helena Batista Moreira", "Marcelo Augusto Ribeiro"],
        "STATUS": ["NÃO NAVEGADO"] * 12,
        "MOTIVO": [
            "Sem cobertura de Convênio",
            "Médico não quis encaminhar",
            "Paciente já em acompanhamento oncológico externo",
            "Tratamento já iniciado fora da rede",
            "Dados cadastrais incompletos no atendimento",
            "Sem cobertura de Convênio",
            "Médico não quis encaminhar",
            "Critério clínico descartado após revisão",
            "Sem agenda disponível no prazo recomendado",
            "Tratamento já iniciado fora da rede",
            "Pendência documental para autorização",
            "Dados cadastrais incompletos no atendimento"
        ],
        "CD ATEND": ["1328642", "1328679", "1328716", "1328753", "1328790", "1328827", "1425268", "1425311", "1527063", "1425354", "1425397", "1527094"],
        "CD PACIENTE": ["40239", "40258", "40277", "40296", "40315", "40334", "51418", "51441", "61874", "51464", "51487", "61891"],
        "CONVÊNIO": ["Bradesco Saúde", "Unimed", "SulAmérica", "Amil", "Notre Dame", "Particular", "Vale/PASA", "CASSI", "Saúde Caixa", "Best Senior", "Bradesco Saúde", "Unimed"],
        "MÉD. SOLICITANTE": ["Dr. Ricardo Almeida", "Dra. Paula Ferreira", "Dr. Carlos Mendes", "Dra. Ana Souza", "Dr. Marcos Lima", "Dra. Juliana Costa", "Dr. Felipe Andrade", "Dra. Fernanda Rocha", "Dr. Henrique Tavares", "Dra. Marina Albuquerque", "Dr. Ricardo Almeida", "Dra. Paula Ferreira"],
        "CONTATO MÉD. SOLICITANTE": ["(27) 99812-3481", "(27) 99731-8842", "(27) 99200-5588", "(27) 98877-1234", "(27) 99556-4321", "(27) 99983-2215", "(27) 99654-7810", "(27) 99472-0093", "(27) 99123-5309", "(27) 99875-6612", "(27) 99812-3481", "(27) 99731-8842"],
    })
    receita_med = pd.DataFrame({
        "MÉDICO": [
            "Dr. Ricardo Almeida", "Dra. Paula Ferreira", "Dr. Carlos Mendes", "Dra. Ana Souza",
            "Dr. Marcos Lima", "Dra. Juliana Costa", "Dr. Felipe Andrade", "Dra. Fernanda Rocha",
            "Dr. Henrique Tavares", "Dra. Marina Albuquerque", "Dr. Gustavo Pereira",
            "Dra. Beatriz Nogueira", "Dr. Lucas Barbosa", "Dra. Renata Moura"
        ],
        "ESPECIALIDADE": ["Oncologia", "Hematologia", "Oncologia", "Oncologia", "Hematologia", "Oncologia", "Hematologia", "Oncologia", "Oncologia", "Hematologia", "Oncologia", "Hematologia", "Oncologia", "Hematologia"],
        "REC. TOTAL": [612400, 548900, 487300, 421700, 386500, 354200, 329800, 298400, 276900, 251700, 229600, 207300, 185900, 162400],
        "% Receita": [16.7, 14.9, 13.3, 11.5, 10.5, 9.6, 9.0, 8.1, 7.5, 6.8, 6.2, 5.6, 5.1, 4.4],
        "Nº PAC.": [126, 112, 98, 87, 79, 73, 68, 61, 58, 52, 48, 44, 39, 34],
        "Nº ATEND.": [184, 166, 143, 128, 116, 104, 98, 89, 84, 76, 69, 61, 55, 49],
    })
    receita_med["TICKET MÉD."] = receita_med["REC. TOTAL"] / receita_med["Nº ATEND."]
    receita_conv = pd.DataFrame({
        "CONVÊNIO": [
            "Bradesco Saúde", "Unimed", "SulAmérica", "Amil", "Vale/PASA", "CASSI",
            "Saúde Caixa", "Best Senior", "Notre Dame", "Particular", "CST", "ISSEC",
            "MedSênior", "Geap Saúde", "Petrobras Saúde", "Postal Saúde"
        ],
        "REC. TOTAL": [845230, 734600, 612450, 498700, 398700, 356800, 322400, 288900, 241200, 198600, 154600, 128900, 112300, 98400, 86200, 72100],
        "% Receita": [18.8, 16.3, 13.6, 11.1, 8.9, 7.9, 7.2, 6.4, 5.4, 4.4, 3.4, 2.9, 2.5, 2.2, 1.9, 1.6],
        "Nº PAC.": [241, 211, 178, 144, 114, 103, 96, 84, 71, 58, 45, 38, 34, 29, 25, 21],
        "Nº ATEND.": [352, 318, 251, 212, 163, 149, 137, 119, 103, 82, 64, 56, 49, 43, 37, 31],
    })
    receita_conv["TICKET MÉD."] = receita_conv["REC. TOTAL"] / receita_conv["Nº ATEND."]
    receita_cid = pd.DataFrame({
        "CID": [
            "C50 – Neoplasia maligna da mama",
            "C34 – Neoplasia maligna de brônquios/pulmão",
            "C18 – Neoplasia maligna do cólon",
            "C61 – Neoplasia maligna da próstata",
            "C91 – Leucemia linfoide",
            "C83 – Linfoma não-Hodgkin difuso",
            "C92 – Leucemia mieloide",
            "C16 – Neoplasia maligna do estômago",
            "C20 – Neoplasia maligna do reto",
            "C56 – Neoplasia maligna do ovário",
            "C64 – Neoplasia maligna do rim",
            "C22 – Neoplasia maligna do fígado",
            "C73 – Neoplasia maligna da tireoide",
            "C81 – Doença de Hodgkin",
            "C90 – Mieloma múltiplo",
            "C71 – Neoplasia maligna do encéfalo"
        ],
        "REC. TOTAL": [635400, 587260, 512560, 447000, 398400, 354420, 321100, 289600, 251900, 229800, 201420, 178900, 151700, 132400, 118600, 96400],
        "% Receita": [15.6, 14.4, 12.6, 11.0, 9.8, 8.7, 7.9, 7.1, 6.2, 5.6, 4.9, 4.4, 3.7, 3.2, 2.9, 2.4],
        "Nº PAC.": [187, 164, 142, 129, 113, 101, 94, 82, 74, 66, 58, 51, 44, 38, 34, 29],
        "Nº ATEND.": [264, 238, 201, 186, 161, 148, 137, 119, 106, 96, 84, 73, 64, 56, 49, 41],
    })
    receita_cid["TICKET MÉD."] = receita_cid["REC. TOTAL"] / receita_cid["Nº ATEND."]
    return patologia_df, radiologia_df, laboratorio_df, naveg, nao_nav, receita_med, receita_conv, receita_cid


patologia_df, radiologia_df, laboratorio_df, naveg_df, nao_nav_df, receita_med_df, receita_conv_df, receita_cid_df = load_mock_data()

# ============================================================
# ENRIQUECIMENTO MOCK - STATUS, SQUAD MÉDICA E FINANCEIRO
# ============================================================

STATUS_IDENTIFICADO = "Identificado e não 1ª Consulta"
STATUS_CONSULTA = "1ª Consulta e não 1º Tratamento"
STATUS_ORDER = [STATUS_IDENTIFICADO, STATUS_CONSULTA]

squad_acompanhamento = [
    "Dra. Beatriz Nogueira",
    "Dr. Lucas Barbosa",
    "Dra. Renata Moura",
    "Dr. Gustavo Pereira",
    "Dra. Marina Albuquerque",
    "Dr. Henrique Tavares",
    "",
    "Dra. Fernanda Rocha",
    "Dr. Felipe Andrade",
    "",
    "Dra. Juliana Costa",
    "Dr. Marcos Lima",
]

squad_sem_vazio = [m for m in squad_acompanhamento if m]

def add_status_and_med_resp(df: pd.DataFrame, offset: int = 0) -> pd.DataFrame:
    df = df.copy()

    statuses = [STATUS_ORDER[(i + offset) % 2] for i in range(len(df))]
    med_resp = []
    for i, status in enumerate(statuses):
        candidate = squad_acompanhamento[(i + offset) % len(squad_acompanhamento)]
        # Regra de negócio do mock: pacientes sem médico responsável devem estar apenas no status
        # "Identificado e não 1ª Consulta".
        if status == STATUS_CONSULTA and candidate == "":
            candidate = squad_sem_vazio[(i + offset) % len(squad_sem_vazio)]
        med_resp.append(candidate)

    if "STATUS" not in df.columns:
        pos = df.columns.get_loc("PACIENTE") + 1 if "PACIENTE" in df.columns else len(df.columns)
        df.insert(pos, "STATUS", statuses)
    else:
        df["STATUS"] = statuses

    if "MÉD. RESP. ACOMP." not in df.columns:
        if "MÉD. SOLICITANTE" in df.columns:
            pos = df.columns.get_loc("MÉD. SOLICITANTE") + 1
        else:
            pos = len(df.columns)
        df.insert(pos, "MÉD. RESP. ACOMP.", med_resp)
    else:
        df["MÉD. RESP. ACOMP."] = med_resp

    return df

patologia_df = add_status_and_med_resp(patologia_df, offset=0)
radiologia_df = add_status_and_med_resp(radiologia_df, offset=1)
laboratorio_df = add_status_and_med_resp(laboratorio_df, offset=2)

# Ajustes financeiros no analítico de pacientes navegados.
# Novas colunas financeiras solicitadas:
# TOTAL - PRODUZIDO, TOTAL - ENVIADO, TOTAL - PENDENTE DE ENVIO,
# TOTAL - RECEBIDO, TOTAL - VALOR A VENCER e TOTAL - VENCIDO.
if "RECEITA" in naveg_df.columns:
    naveg_df = naveg_df.rename(columns={"RECEITA": "TOTAL - PRODUZIDO"})

# Remove nomes financeiros antigos, caso existam em alguma versão anterior.
naveg_df = naveg_df.drop(
    columns=["RECEITA - PRODUZIDA", "RECEITA - ENVIADA", "RECEITA - RECEBIDA", "TOTAL GLOSADO"],
    errors="ignore",
)

total_enviado = [
    0, 11200, 8730, None, 307.14, 15000, 0, 425.11, 22000, None,
    18500, 21000, 0, 12500, 17650, 24000, None, 6400, 15400, 11000
]
total_recebido = [
    0, 9800, None, None, 0, 13750, 8500, None, 20200, None,
    17000, 19800, None, 10900, 16000, 22000, None, 5800, None, 9800
]
total_vencido = [
    None, 850, None, None, 120.00, 760, 420, None, 950, None,
    620, 530, None, 870, 740, 1100, None, 260, None, 390
]

produzido_num = pd.to_numeric(naveg_df["TOTAL - PRODUZIDO"], errors="coerce").fillna(0)

enviado_series = pd.Series(total_enviado[:len(naveg_df)], dtype="float")
recebido_series = pd.Series(total_recebido[:len(naveg_df)], dtype="float")
vencido_series = pd.Series(total_vencido[:len(naveg_df)], dtype="float")

pendente_envio_series = produzido_num.reset_index(drop=True) - enviado_series.fillna(0)
pendente_envio_series = pendente_envio_series.where(pendente_envio_series > 0, None)

valor_a_vencer_series = enviado_series.fillna(0) - recebido_series.fillna(0) - vencido_series.fillna(0)
valor_a_vencer_series = valor_a_vencer_series.where(valor_a_vencer_series > 0, None)

finance_cols = [
    ("TOTAL - ENVIADO", total_enviado),
    ("TOTAL - PENDENTE DE ENVIO", pendente_envio_series.tolist()),
    ("TOTAL - RECEBIDO", total_recebido),
    ("TOTAL - VALOR A VENCER", valor_a_vencer_series.tolist()),
    ("TOTAL - VENCIDO", total_vencido),
]

for col, values in finance_cols:
    if col not in naveg_df.columns:
        pos = naveg_df.columns.get_loc("TOTAL - PRODUZIDO") + 1
        if col == "TOTAL - PENDENTE DE ENVIO" and "TOTAL - ENVIADO" in naveg_df.columns:
            pos = naveg_df.columns.get_loc("TOTAL - ENVIADO") + 1
        if col == "TOTAL - RECEBIDO" and "TOTAL - PENDENTE DE ENVIO" in naveg_df.columns:
            pos = naveg_df.columns.get_loc("TOTAL - PENDENTE DE ENVIO") + 1
        if col == "TOTAL - VALOR A VENCER" and "TOTAL - RECEBIDO" in naveg_df.columns:
            pos = naveg_df.columns.get_loc("TOTAL - RECEBIDO") + 1
        if col == "TOTAL - VENCIDO" and "TOTAL - VALOR A VENCER" in naveg_df.columns:
            pos = naveg_df.columns.get_loc("TOTAL - VALOR A VENCER") + 1
        naveg_df.insert(pos, col, values[:len(naveg_df)])
    else:
        naveg_df[col] = values[:len(naveg_df)]

# Hospital nas tabelas da aba Busca de Pacientes
def add_hospital_column(df: pd.DataFrame, offset: int = 0) -> pd.DataFrame:
    df = df.copy()
    hospitais = ["HA", "HFSB"]
    values = [hospitais[(i + offset) % 2] for i in range(len(df))]
    if "HOSPITAL" not in df.columns:
        pos = df.columns.get_loc("DIAS DESDE A IDENTIFICAÇÃO") + 1 if "DIAS DESDE A IDENTIFICAÇÃO" in df.columns else 1
        df.insert(pos, "HOSPITAL", values)
    else:
        df["HOSPITAL"] = values
    return df

patologia_df = add_hospital_column(patologia_df, offset=0)
radiologia_df = add_hospital_column(radiologia_df, offset=1)
laboratorio_df = add_hospital_column(laboratorio_df, offset=0)

# Médicos responsáveis também nos analíticos de navegação/não navegação.
med_resp_naveg = [squad_sem_vazio[i % len(squad_sem_vazio)] for i in range(len(naveg_df))]
med_resp_nao_nav = [
    "Dra. Beatriz Nogueira", "Dr. Lucas Barbosa", "Dra. Renata Moura", "Dr. Gustavo Pereira",
    "Dra. Marina Albuquerque", "Dr. Henrique Tavares", "Dra. Fernanda Rocha", "Dr. Felipe Andrade",
    "Dra. Juliana Costa", "Dr. Marcos Lima", "Dra. Paula Ferreira", "Dr. Ricardo Almeida"
]

if "MÉD. RESP. ACOMP." not in naveg_df.columns:
    pos = naveg_df.columns.get_loc("MÉD. SOLICITANTE") + 1 if "MÉD. SOLICITANTE" in naveg_df.columns else len(naveg_df.columns)
    naveg_df.insert(pos, "MÉD. RESP. ACOMP.", med_resp_naveg[:len(naveg_df)])
else:
    naveg_df["MÉD. RESP. ACOMP."] = med_resp_naveg[:len(naveg_df)]

if "MÉD. RESP. ACOMP." not in nao_nav_df.columns:
    pos = nao_nav_df.columns.get_loc("MÉD. SOLICITANTE") + 1 if "MÉD. SOLICITANTE" in nao_nav_df.columns else len(nao_nav_df.columns)
    nao_nav_df.insert(pos, "MÉD. RESP. ACOMP.", med_resp_nao_nav[:len(nao_nav_df)])
else:
    nao_nav_df["MÉD. RESP. ACOMP."] = med_resp_nao_nav[:len(nao_nav_df)]

# Troca de motivo para algo mais aderente à navegação oncológica.
nao_nav_df["MOTIVO"] = nao_nav_df["MOTIVO"].replace({
    "Dados cadastrais incompletos no atendimento": "Sem elegibilidade operacional para navegação"
})

def money_card(v: float) -> str:
    if v >= 1_000_000:
        return "R$ " + f"{v/1_000_000:.2f}".replace(".", ",") + " Mi"
    if v >= 1_000:
        return "R$ " + f"{v/1_000:.1f}".replace(".", ",") + " Mil"
    return money(v)

def sum_finance_col(df: pd.DataFrame, col: str) -> float:
    if col not in df.columns:
        return 0.0
    return pd.to_numeric(df[col], errors="coerce").fillna(0).sum()

def busca_base_df() -> pd.DataFrame:
    frames = []
    for area, df in [
        ("Patologia", patologia_df),
        ("Radiologia", radiologia_df),
        ("Laboratório", laboratorio_df),
    ]:
        temp = df.copy()
        temp["ÁREA"] = area
        frames.append(temp)
    return pd.concat(frames, ignore_index=True, sort=False)

if "busca_status_filter" not in st.session_state:
    st.session_state.busca_status_filter = None

if "busca_med_resp_filter" not in st.session_state:
    st.session_state.busca_med_resp_filter = None

if "nao_nav_motivo_filter" not in st.session_state:
    st.session_state.nao_nav_motivo_filter = None

if "nao_nav_med_resp_filter" not in st.session_state:
    st.session_state.nao_nav_med_resp_filter = None

if "naveg_hospital_filter" not in st.session_state:
    st.session_state.naveg_hospital_filter = None

if "naveg_convenio_filter" not in st.session_state:
    st.session_state.naveg_convenio_filter = None

def apply_naveg_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    hospital_filter = st.session_state.get("naveg_hospital_filter")
    convenio_filter = st.session_state.get("naveg_convenio_filter")

    if hospital_filter:
        filtered = filtered[filtered["HOSPITAL"] == hospital_filter]

    if convenio_filter:
        filtered = filtered[filtered["CONVÊNIO"] == convenio_filter]

    return filtered

def enviado_recebido_hospital_df(df: pd.DataFrame) -> pd.DataFrame:
    finance_cols = [
        "TOTAL - PRODUZIDO",
        "TOTAL - PENDENTE DE ENVIO",
        "TOTAL - ENVIADO",
        "TOTAL - RECEBIDO",
        "TOTAL - VALOR A VENCER",
        "TOTAL - VENCIDO",
    ]
    temp = df.copy()
    for col in finance_cols:
        temp[col] = pd.to_numeric(temp[col], errors="coerce").fillna(0)

    rows = []
    for hospital, hdf in temp.groupby("HOSPITAL", sort=True):
        hrow = {"Hospital": hospital, "Convênio": "TOTAL DO HOSPITAL"}
        for col in finance_cols:
            hrow[col.replace("TOTAL - ", "").title()] = hdf[col].sum()
        rows.append(hrow)

        conv_group = (
            hdf.groupby("CONVÊNIO")[finance_cols]
            .sum()
            .reset_index()
            .sort_values("TOTAL - PRODUZIDO", ascending=False)
        )
        for _, r in conv_group.iterrows():
            crow = {"Hospital": hospital, "Convênio": r["CONVÊNIO"]}
            for col in finance_cols:
                crow[col.replace("TOTAL - ", "").title()] = r[col]
            rows.append(crow)

    return pd.DataFrame(rows)

def format_enviado_recebido_for_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["Produzido", "Pendente De Envio", "Enviado", "Recebido", "Valor A Vencer", "Vencido"]:
        if col in out.columns:
            out[col] = out[col].apply(lambda x: money(float(x)) if pd.notna(x) else "")
    out = out.rename(columns={
        "Pendente De Envio": "Pendente de Envio",
        "Valor A Vencer": "Valor a Vencer",
    })
    return out

def update_naveg_hospital_table_event(event, raw_df: pd.DataFrame):
    try:
        rows = event.selection.rows
    except Exception:
        rows = []

    if rows:
        selected = raw_df.iloc[rows[0]]
        hospital = selected["Hospital"]
        convenio = selected["Convênio"]

        st.session_state.naveg_hospital_filter = hospital
        st.session_state.naveg_convenio_filter = None if convenio == "TOTAL DO HOSPITAL" else convenio
        st.rerun()

def matrix_money(value) -> str:
    try:
        return money(float(value))
    except Exception:
        return ""

def set_naveg_filter(hospital: str | None = None, convenio: str | None = None):
    st.session_state.naveg_hospital_filter = hospital
    st.session_state.naveg_convenio_filter = convenio
    st.rerun()

def render_enviado_recebido_matrix(df: pd.DataFrame):
    raw = enviado_recebido_hospital_df(df)

    value_cols = [
        "Produzido",
        "Pendente De Envio",
        "Enviado",
        "Recebido",
        "Valor A Vencer",
        "Vencido",
    ]

    st.markdown("<div class='table-card'><div class='table-title'>ENVIADO E RECEBIDO POR HOSPITAL</div></div>", unsafe_allow_html=True)

    widths = [1.0, 2.15, 1.15, 1.45, 1.15, 1.15, 1.4, 1.15]
    header = st.columns(widths)
    header[0].markdown("**Hospital**")
    header[1].markdown("**Convênio**")
    header[2].markdown("**Produzido**")
    header[3].markdown("**Pendente Envio**")
    header[4].markdown("**Enviado**")
    header[5].markdown("**Recebido**")
    header[6].markdown("**Vl a Vencer**")
    header[7].markdown("**Vencido**")
    st.markdown("<hr style='margin: 2px 0 6px 0; border: 0; border-top: 1px solid #cfe0f2;'>", unsafe_allow_html=True)

    for hospital in raw["Hospital"].drop_duplicates().tolist():
        hkey = f"matrix_expanded_{hospital}"
        if hkey not in st.session_state:
            st.session_state[hkey] = True

        hrow = raw[(raw["Hospital"] == hospital) & (raw["Convênio"] == "TOTAL DO HOSPITAL")].iloc[0]
        expanded = st.session_state[hkey]
        icon = "▾" if expanded else "▸"

        cols = st.columns(widths)
        with cols[0]:
            if st.button(f"{icon} {hospital}", key=f"matrix_hospital_{hospital}", use_container_width=True):
                st.session_state[hkey] = not st.session_state[hkey]
                st.session_state.naveg_hospital_filter = hospital
                st.session_state.naveg_convenio_filter = None
                st.rerun()
        cols[1].markdown("**TOTAL DO HOSPITAL**")
        for i, col in enumerate(value_cols, start=2):
            cols[i].markdown(f"**{matrix_money(hrow[col])}**")

        if expanded:
            conv_rows = raw[(raw["Hospital"] == hospital) & (raw["Convênio"] != "TOTAL DO HOSPITAL")].copy()
            for _, r in conv_rows.iterrows():
                conv = str(r["Convênio"])
                ccols = st.columns(widths)
                ccols[0].markdown("")
                with ccols[1]:
                    safe_key = re.sub(r"[^A-Za-z0-9_]+", "_", f"{hospital}_{conv}") or f"{hospital}_sem_convenio"
                    if st.button(f"↳ {conv}", key=f"matrix_convenio_{safe_key}", use_container_width=True):
                        st.session_state.naveg_hospital_filter = hospital
                        st.session_state.naveg_convenio_filter = conv
                        st.rerun()
                for i, col in enumerate(value_cols, start=2):
                    ccols[i].markdown(matrix_money(r[col]))

        st.markdown("<hr style='margin: 2px 0 4px 0; border: 0; border-top: 1px solid #eef3f8;'>", unsafe_allow_html=True)

def apply_busca_interactive_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()

    status_filter = st.session_state.get("busca_status_filter")
    med_filter = st.session_state.get("busca_med_resp_filter")

    if status_filter:
        filtered = filtered[filtered["STATUS"] == status_filter]

    if med_filter is not None:
        if med_filter == "SEM MÉDICO RESP.":
            filtered = filtered[filtered["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip() == ""]
        else:
            filtered = filtered[filtered["MÉD. RESP. ACOMP."].fillna("").astype(str) == med_filter]

    return filtered

def apply_nao_nav_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    motivo_filter = st.session_state.get("nao_nav_motivo_filter")
    med_filter = st.session_state.get("nao_nav_med_resp_filter")

    if motivo_filter:
        filtered = filtered[filtered["MOTIVO"] == motivo_filter]

    if med_filter is not None:
        filtered = filtered[filtered["MÉD. RESP. ACOMP."].fillna("").astype(str) == med_filter]

    return filtered

def update_filter_from_status_event(event, status_summary: pd.DataFrame):
    try:
        rows = event.selection.rows
    except Exception:
        rows = []

    if rows:
        selected_status = str(status_summary.iloc[rows[0]]["Status"])
        if st.session_state.busca_status_filter != selected_status or st.session_state.busca_med_resp_filter is not None:
            st.session_state.busca_status_filter = selected_status
            st.session_state.busca_med_resp_filter = None
            st.rerun()
    else:
        if st.session_state.busca_status_filter is not None and st.session_state.busca_med_resp_filter is None:
            st.session_state.busca_status_filter = None
            st.rerun()

def plot_status_by_med_resp(df: pd.DataFrame):
    temp = df.copy()
    temp["MÉD. RESP. ACOMP."] = temp["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip()
    temp.loc[temp["MÉD. RESP. ACOMP."] == "", "MÉD. RESP. ACOMP."] = "SEM MÉDICO RESP."

    # A linha sem médico responsável deve conter apenas pacientes identificados e ainda sem 1ª consulta.
    temp = temp[~((temp["MÉD. RESP. ACOMP."] == "SEM MÉDICO RESP.") & (temp["STATUS"] != STATUS_IDENTIFICADO))]

    order_medicos = ["SEM MÉDICO RESP."] + sorted([m for m in temp["MÉD. RESP. ACOMP."].unique().tolist() if m != "SEM MÉDICO RESP."])
    grouped = (
        temp.groupby(["MÉD. RESP. ACOMP.", "STATUS"])
        .size()
        .reset_index(name="Nº Atend.")
    )

    fig = go.Figure()
    for status in STATUS_ORDER:
        vals = []
        for med in order_medicos:
            value = grouped[
                (grouped["MÉD. RESP. ACOMP."] == med) &
                (grouped["STATUS"] == status)
            ]["Nº Atend."]
            vals.append(int(value.iloc[0]) if not value.empty else 0)

        fig.add_trace(
            go.Bar(
                y=order_medicos,
                x=vals,
                name=status,
                orientation="h",
                text=[str(v) if v > 0 else "" for v in vals],
                textposition="inside",
            )
        )

    fig.update_layout(
        height=max(270, 32 * len(order_medicos) + 90),
        barmode="stack",
        margin=dict(l=180, r=40, t=20, b=35),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        font=dict(color="#000000", size=11),
        xaxis=dict(gridcolor="#e7eef7", tickfont=dict(color="#000000")),
        yaxis=dict(autorange="reversed", tickfont=dict(color="#000000")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig

def update_filter_from_chart_event(event):
    try:
        points = event.selection.points
    except Exception:
        points = []

    if points:
        point = points[0]
        med = point.get("y")
        curve_number = point.get("curve_number", point.get("curveNumber", None))
        status = STATUS_IDENTIFICADO if curve_number == 0 else STATUS_CONSULTA

        if st.session_state.busca_med_resp_filter != med or st.session_state.busca_status_filter != status:
            st.session_state.busca_med_resp_filter = med
            st.session_state.busca_status_filter = status
            st.rerun()
    else:
        if st.session_state.busca_med_resp_filter is not None:
            st.session_state.busca_med_resp_filter = None
            st.session_state.busca_status_filter = None
            st.rerun()

def plot_motivos_nao_nav_bar(df: pd.DataFrame):
    grouped = (
        df.groupby("MOTIVO")
        .size()
        .reset_index(name="Nº Atend.")
        .sort_values("Nº Atend.", ascending=False)
    )
    fig = go.Figure()
    fig.add_bar(
        x=grouped["Nº Atend."].tolist(),
        y=grouped["MOTIVO"].tolist(),
        orientation="h",
        marker_color=ACCENT,
        text=grouped["Nº Atend."].tolist(),
        textposition="inside",
        customdata=grouped["MOTIVO"].tolist(),
    )
    fig.update_layout(
        height=max(300, 34 * len(grouped) + 90),
        margin=dict(l=280, r=40, t=20, b=35),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        clickmode="event+select",
        yaxis=dict(autorange="reversed", tickfont=dict(color="#000000")),
        xaxis=dict(gridcolor="#e7eef7", tickfont=dict(color="#000000")),
        font=dict(color="#000000", size=11),
        showlegend=False,
    )
    return fig


def update_nao_nav_motivo_event(event, base_df: pd.DataFrame | None = None):
    try:
        points = event.selection.points
    except Exception:
        points = []

    if points:
        point = points[0]
        motivo = (
            point.get("customdata")
            or point.get("y")
            or point.get("label")
            or point.get("legendgroup")
        )

        if not motivo and base_df is not None:
            grouped = base_df.groupby("MOTIVO").size().reset_index(name="Nº Atend.").sort_values("Nº Atend.", ascending=False)
            idx = point.get("point_number", point.get("pointNumber", None))
            if idx is not None and int(idx) < len(grouped):
                motivo = str(grouped.iloc[int(idx)]["MOTIVO"])

        if motivo and st.session_state.nao_nav_motivo_filter != motivo:
            st.session_state.nao_nav_motivo_filter = motivo
            st.rerun()
    else:
        if st.session_state.nao_nav_motivo_filter is not None:
            st.session_state.nao_nav_motivo_filter = None
            st.rerun()

def plot_nao_nav_por_med_resp(df: pd.DataFrame):
    temp = df.copy()
    temp["MÉD. RESP. ACOMP."] = temp["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip()
    temp = temp[temp["MÉD. RESP. ACOMP."] != ""]
    grouped = temp.groupby("MÉD. RESP. ACOMP.").size().reset_index(name="Nº Atend.").sort_values("Nº Atend.", ascending=False)

    fig = go.Figure()
    fig.add_bar(
        x=grouped["Nº Atend."].tolist(),
        y=grouped["MÉD. RESP. ACOMP."].tolist(),
        orientation="h",
        marker_color=ACCENT,
        text=grouped["Nº Atend."].tolist(),
        textposition="inside",
    )
    fig.update_layout(
        height=max(275, 35 * len(grouped) + 80),
        margin=dict(l=180, r=40, t=20, b=30),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        yaxis=dict(autorange="reversed", tickfont=dict(color="#000000")),
        xaxis=dict(gridcolor="#e7eef7", tickfont=dict(color="#000000")),
        font=dict(color="#000000", size=11),
    )
    return fig

def update_nao_nav_med_event(event):
    try:
        points = event.selection.points
    except Exception:
        points = []

    if points:
        med = points[0].get("y")
        if st.session_state.nao_nav_med_resp_filter != med:
            st.session_state.nao_nav_med_resp_filter = med
            st.rerun()
    else:
        if st.session_state.nao_nav_med_resp_filter is not None:
            st.session_state.nao_nav_med_resp_filter = None
            st.rerun()

# ============================================================
# COMPONENTES VISUAIS
# ============================================================

def sidebar():
    with st.sidebar:
        # Barra fina: logo + botões com PNG como background.
        # Tudo funciona por st.button, sem trocar de página/URL.
        if not st.session_state.filters_open:
            st.markdown('<div class="rail">', unsafe_allow_html=True)

            if LOGO_URI:
                st.markdown(
                    f'''
                    <div class="rail-logo-wrap">
                        <img class="rail-logo" src="{LOGO_URI}" alt="Kora">
                    </div>
                    ''',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="rail-fallback">◔</div>', unsafe_allow_html=True)

            if st.button(" ", key="btn_open_filters", help="Abrir filtros"):
                st.session_state.filters_open = True
                st.rerun()

            if st.button(" ", key="btn_refresh", help="Atualizar"):
                st.rerun()

            if st.button(" ", key="btn_home", help="Busca de Pacientes"):
                st.session_state.page = "Busca de Pacientes"
                st.rerun()

            if st.session_state.page == "Busca de Pacientes":
                if st.button(" ", key="btn_nav_page", help="Ir para Acomp. Indicadores"):
                    st.session_state.page = "Acomp. Indicadores"
                    st.rerun()
            else:
                if st.button(" ", key="btn_nav_page", help="Voltar para Busca de Pacientes"):
                    st.session_state.page = "Busca de Pacientes"
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Gaveta aberta: mostra filtros na MESMA tela.
        if LOGO_URI:
            st.markdown(
                f"""
                <div class="sidebar-logo-wrap">
                    <img class="sidebar-logo" src="{LOGO_URI}">
                    <div>
                        <div class="sidebar-title">BI Navegação Oncológica</div>
                        <div class="sidebar-subtitle">Navegação • v1.0</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("‹ Voltar", key="btn_close_filters"):
            st.session_state.filters_open = False
            st.rerun()

        st.markdown("---")
        st.markdown("<div style='font-weight:700;color:#ffffff;margin-bottom:8px;'>▾ FILTROS</div>", unsafe_allow_html=True)

        st.markdown("<div class='filter-label'>Data</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="date-range-row">
                <div class="date-box">01/06/2025</div>
                <div class="date-box">15/06/2025</div>
            </div>
            <div class="date-slider">
                <div class="date-dot left"></div>
                <div class="date-dot right"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='filter-label'>Ano</div>", unsafe_allow_html=True)
        ano_filtro = st.selectbox(
            "Ano",
            ["2026", "2027"],
            key="filtro_ano",
            label_visibility="collapsed",
        )

        meses = [
            "Todos",
            f"Jan/{ano_filtro}",
            f"Fev/{ano_filtro}",
            f"Mar/{ano_filtro}",
            f"Abr/{ano_filtro}",
            f"Mai/{ano_filtro}",
            f"Jun/{ano_filtro}",
            f"Jul/{ano_filtro}",
            f"Ago/{ano_filtro}",
            f"Set/{ano_filtro}",
            f"Out/{ano_filtro}",
            f"Nov/{ano_filtro}",
            f"Dez/{ano_filtro}",
        ]
        st.markdown("<div class='filter-label'>Mês Atual</div>", unsafe_allow_html=True)
        st.selectbox(
            "Mês Atual",
            meses,
            key="filtro_mes_atual",
            label_visibility="collapsed",
        )

        st.markdown("<div class='filter-label'>HUB</div>", unsafe_allow_html=True)
        st.selectbox(
            "HUB",
            ["Todos", "HB01", "HB02", "HB03", "HB04"],
            key="filtro_hub",
            label_visibility="collapsed",
        )

        st.markdown("<div class='filter-label'>Convênio</div>", unsafe_allow_html=True)
        st.selectbox(
            "Convênio",
            ["Todos", "UNIMED", "BRADESCO", "VALE/PASA", "CST", "AMIL", "BEST SENIOR"],
            key="filtro_convenio",
            label_visibility="collapsed",
        )

        st.markdown("<div class='filter-label'>Área</div>", unsafe_allow_html=True)
        st.selectbox(
            "Área",
            ["Todos", "Patologia", "Radiologia", "Laboratório"],
            key="filtro_area",
            label_visibility="collapsed",
        )

        st.markdown("<div class='filter-label'>Setor</div>", unsafe_allow_html=True)
        st.selectbox(
            "Setor",
            ["Todos", "Urgência", "Ambulatório", "Centro Cirúrgico", "Laboratório", "IDE"],
            key="filtro_setor",
            label_visibility="collapsed",
        )

        st.markdown("<div class='filter-label'>Especialidade</div>", unsafe_allow_html=True)
        st.selectbox(
            "Especialidade",
            ["Todos", "Oncologia", "Hematologia"],
            key="filtro_especialidade",
            label_visibility="collapsed",
        )

        prestadores_set = set()
        for _df in [patologia_df, radiologia_df, laboratorio_df, naveg_df, nao_nav_df, receita_med_df]:
            for _col in ["MÉD. SOLICITANTE", "MÉDICO"]:
                if _col in _df.columns:
                    prestadores_set.update(_df[_col].dropna().astype(str).tolist())

        prestadores = ["Todos"] + sorted(prestadores_set)

        st.markdown("<div class='filter-label'>Prestador</div>", unsafe_allow_html=True)
        st.selectbox(
            "Prestador",
            prestadores,
            key="filtro_prestador",
            label_visibility="collapsed",
        )

        st.button("APLICAR FILTROS", key="btn_apply_filters")

        # A navegação entre abas fica apenas na seta da barra fina.
        # Por isso, os botões inferiores de "Acomp. Indicadores" e
        # "Busca de Pacientes" foram removidos da gaveta de filtros.


def topbar():
    st.markdown(
        """
        <div class="topbar">
            <div></div>
            <div class="date-ref">01/06/2025 — 15/06/2025</div>
            <div class="title-ref">
                <h1>BUSCA DE NOVOS PACIENTES ONCOLÓGICOS - OPERAÇÕES</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-head">{title}</div>
            <div class="metric-body">
                <div class="metric-value">{value}</div>
                <div class="metric-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mini_origin_block(title: str, atend: str, conv1: str, conv2: str):
    st.markdown(
        f"""
        <div class="mini-box">
            <div class="mini-box-title">{title}</div>
            <div class="mini-metrics">
                <div class="mini-metric"><div class="mini-label">Nº Atend. - Identificados.</div><div class="mini-value">{atend}</div></div>
                <div class="mini-metric"><div class="mini-label">Taxa Conv. - 1ª Consulta.</div><div class="mini-value">{conv1}</div></div>
                <div class="mini-metric"><div class="mini-label">Taxa Conv. - 1º Tratamento.</div><div class="mini-value">{conv2}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def table_html(df: pd.DataFrame, title: str, scroll=False):
    def break_long_text(text: str, width: int = 115) -> str:
        words = str(text).split()
        lines = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= width:
                current = f"{current} {word}".strip()
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return "<br>".join(lines)

    def fmt_cell(col, val):
        if pd.isna(val):
            return ""
        if col == "LAUDO":
            return break_long_text(str(val), width=115)
        if "%" in col and isinstance(val, (int, float)):
            return pct(val)
        if "REC" in col or "TICKET" in col or col == "RECEITA" or col.startswith("TOTAL -"):
            if isinstance(val, (int, float)):
                return money(val)
        if isinstance(val, float):
            return f"{val:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"<span class='plain-status'>{val}</span>"

    rows = []
    for _, r in df.iterrows():
        cells = []
        for c in df.columns:
            css_class = " class='laudo-cell'" if c == "LAUDO" else ""
            cells.append(f"<td{css_class}>{fmt_cell(c, r[c])}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")

    header = "".join([f"<th>{c}</th>" for c in df.columns])
    scroll_class = "scroll-table" if scroll else ""

    st.markdown(
        f"""
        <div class="table-card">
            <div class="table-title">{title}</div>
            <div class="{scroll_class}">
                <table class="mock-table">
                    <thead><tr>{header}</tr></thead>
                    <tbody>{''.join(rows)}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_area_monthly():
    months = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    values = [2050000, 1720000, 2220000, 1880000, 1900000, 1240000]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines+markers+text",
            fill="tozeroy",
            line=dict(width=3, color=ACCENT),
            marker=dict(size=8, color=ACCENT),
            fillcolor="rgba(47,128,237,0.42)",
            text=["R$ 2,05 Mi", "R$ 1,72 Mi", "R$ 2,22 Mi", "R$ 1,88 Mi", "R$ 1,90 Mi", "R$ 1,24 Mi"],
            textposition="top center",
        )
    )
    fig.update_layout(
        height=275,
        margin=dict(l=30, r=20, t=20, b=30),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        yaxis=dict(gridcolor="#e7eef7", tickfont=dict(color="#000000"), tickformat=".2s"),
        xaxis=dict(gridcolor="#fff", tickfont=dict(color="#000000")),
        font=dict(color="#000000", size=11),
    )
    return fig


def plot_total_recebido_monthly(df: pd.DataFrame):
    temp = df.copy()
    date_col = "DATA CONSULTA/TRATAMENTO" if "DATA CONSULTA/TRATAMENTO" in temp.columns else "DATA IDENTIFICAÇÃO"
    temp["_DATA_REF"] = pd.to_datetime(temp[date_col], dayfirst=True, errors="coerce")
    temp["_VALOR_RECEBIDO"] = pd.to_numeric(temp["TOTAL - RECEBIDO"], errors="coerce").fillna(0)
    temp = temp.dropna(subset=["_DATA_REF"])

    month_map = {
        1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
    }

    grouped = (
        temp.groupby(temp["_DATA_REF"].dt.month)["_VALOR_RECEBIDO"]
        .sum()
        .reset_index()
        .rename(columns={"_DATA_REF": "MES_NUM", "_VALOR_RECEBIDO": "TOTAL_RECEBIDO"})
        .sort_values("MES_NUM")
    )

    months = [month_map[int(m)] for m in grouped["MES_NUM"].tolist()]
    values = grouped["TOTAL_RECEBIDO"].tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines+markers+text",
            fill="tozeroy",
            line=dict(width=3, color=ACCENT),
            marker=dict(size=8, color=ACCENT),
            fillcolor="rgba(47,128,237,0.42)",
            text=[money_card(v) for v in values],
            textposition="top center",
        )
    )
    fig.update_layout(
        height=275,
        margin=dict(l=30, r=20, t=20, b=30),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        yaxis=dict(gridcolor="#e7eef7", tickfont=dict(color="#000000"), tickformat=".2s"),
        xaxis=dict(gridcolor="#fff", tickfont=dict(color="#000000")),
        font=dict(color="#000000", size=11),
    )
    return fig


def plot_hbar(labels, values, left_margin: int = 150):
    fig = go.Figure()
    fig.add_bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=ACCENT,
        text=[money(v).replace("R$ ", "R$") for v in values],
        textposition="outside",
    )
    fig.update_layout(
        height=max(275, 35 * len(labels) + 80),
        margin=dict(l=left_margin, r=90, t=15, b=25),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        yaxis=dict(autorange="reversed", gridcolor="#fff", tickfont=dict(color="#000000")),
        xaxis=dict(gridcolor="#e7eef7", tickfont=dict(color="#000000")),
        font=dict(color="#000000", size=11),
    )
    return fig


def plot_donut():
    return plot_donut_nao_nav(nao_nav_df)


def plot_donut_cid_top10():
    labels = [
        "C50 Mama", "C34 Pulmão", "C18 Cólon", "C61 Próstata", "C91 Leucemia",
        "C83 Linfoma", "C92 L. mieloide", "C16 Estômago", "C90 Mieloma", "C56 Ovário"
    ]
    values = [132, 118, 96, 84, 72, 66, 58, 49, 44, 39]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=.55,
                marker=dict(colors=["#2f80ed", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#1d4ed8", "#2563eb", "#1e40af", "#172554", "#0f3d6e"]),
                textinfo="percent+value",
                textfont=dict(color="#000000"),
            )
        ]
    )
    fig.update_layout(
        height=275,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        font=dict(color="#000000", size=11),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=.5, font=dict(color="#000000")),
    )
    return fig



def plot_donut_area_receita():
    labels = ["Patologia", "Radiologia", "Laboratório"]
    values = [945000, 1125000, 760000]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=.55,
                marker=dict(colors=[ACCENT, "#60a5fa", "#bfdbfe"]),
                textinfo="percent+value",
                textfont=dict(color="#000000"),
            )
        ]
    )
    fig.update_layout(
        height=275,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        font=dict(color="#000000", size=11),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=.5, font=dict(color="#000000")),
    )
    return fig


def viz_container_scroll(title: str, fig, height_px: int = 360, width_px: int = 1050):
    fig.update_layout(width=width_px)
    html = fig.to_html(full_html=False, include_plotlyjs=True, config={"displayModeBar": False})
    st.markdown(
        f"<div class='viz-scroll-shell'><div class='viz-scroll-title'>{title}</div></div>",
        unsafe_allow_html=True,
    )

    container_html = """
    <div style="height:{height}px; overflow:auto; background:white; border:1px solid #d7e2ef; border-top:0;">
        <div style="min-width:{width}px;">
            {plot_html}
        </div>
    </div>
    """.format(height=height_px, width=width_px, plot_html=html)

    components.html(
        container_html,
        height=height_px + 20,
        scrolling=False,
    )

def viz_container(title: str, fig):
    st.markdown(f"<div class='viz-card'><div class='viz-title'>{title}</div>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def bottom_nav():
    current = st.session_state.page
    cls1 = "tab-card tab-card-active" if current == "Busca de Pacientes" else "tab-card"
    cls2 = "tab-card tab-card-active" if current == "Acomp. Indicadores" else "tab-card"

    st.markdown(
        f"""
        <div class="bottom-nav">
            <div class="{cls1}">Busca de Pacientes</div>
            <div class="{cls2}">Acomp. Indicadores</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# PÁGINAS
# ============================================================

def page_busca():
    topbar()

    base_all = busca_base_df()
    base_filtered = apply_busca_interactive_filters(base_all)

    total_atend = len(base_filtered)
    total_pac = base_filtered["PACIENTE"].nunique()
    total_pat = len(base_filtered[base_filtered["ÁREA"] == "Patologia"])
    total_rad = len(base_filtered[base_filtered["ÁREA"] == "Radiologia"])
    total_lab = len(base_filtered[base_filtered["ÁREA"] == "Laboratório"])
    tempo_medio = pd.to_numeric(base_filtered["DIAS DESDE A IDENTIFICAÇÃO"], errors="coerce").mean()
    tempo_medio_txt = "-" if pd.isna(tempo_medio) else f"{tempo_medio:.1f} dias".replace(".", ",")

    cols = st.columns(5)
    with cols[0]:
        metric_card("Nº Atend. Identificados - Total", f"{total_atend:,}".replace(",", "."), f"{total_pac} pacientes")
    with cols[1]:
        metric_card("Nº Atend.Identificados - Patologia", f"{total_pat:,}".replace(",", "."), f"{base_filtered[base_filtered['ÁREA'] == 'Patologia']['PACIENTE'].nunique()} pacientes")
    with cols[2]:
        metric_card("Nº Atend. Identificados - Radiologia", f"{total_rad:,}".replace(",", "."), f"{base_filtered[base_filtered['ÁREA'] == 'Radiologia']['PACIENTE'].nunique()} pacientes")
    with cols[3]:
        metric_card("Nº Atend. Identificados - Laboratório", f"{total_lab:,}".replace(",", "."), f"{base_filtered[base_filtered['ÁREA'] == 'Laboratório']['PACIENTE'].nunique()} pacientes")
    with cols[4]:
        metric_card("Tempo médio desde a identificação", tempo_medio_txt, "Média com filtro")

    status_identificados = len(base_filtered[base_filtered["STATUS"] == STATUS_IDENTIFICADO])
    status_consulta = len(base_filtered[base_filtered["STATUS"] == STATUS_CONSULTA])
    sem_medico = len(base_filtered[base_filtered["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip() == ""])

    cols = st.columns([1.3, 1, 1, 1, 1.3])
    with cols[1]:
        metric_card("Nº Atend. - Identificado e não 1ª Consulta", f"{status_identificados:,}".replace(",", "."), "")
    with cols[2]:
        metric_card("Nº Atend. - 1ª Consulta e não 1º Tratamento", f"{status_consulta:,}".replace(",", "."), "")
    with cols[3]:
        metric_card("Nº Atend. - Sem Médico Resp. Acompanhamento", f"{sem_medico:,}".replace(",", "."), "")

    status_summary = (
        base_all.groupby("STATUS")
        .agg(**{"Nº Atend.": ("STATUS", "size"), "Nº Pacientes": ("PACIENTE", "nunique")})
        .reset_index()
        .rename(columns={"STATUS": "Status"})
    )
    status_summary["Status"] = pd.Categorical(status_summary["Status"], STATUS_ORDER, ordered=True)
    status_summary = status_summary.sort_values("Status").reset_index(drop=True)

    col_status, col_chart = st.columns([0.28, 0.72])
    with col_status:
        st.markdown("<div class='table-card'><div class='table-title'>STATUS</div></div>", unsafe_allow_html=True)
        try:
            status_event = st.dataframe(
                status_summary,
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row",
                key=f"status_selector_table_{st.session_state.get('status_selector_reset_counter', 0)}",
            )
            update_filter_from_status_event(status_event, status_summary)
        except TypeError:
            st.dataframe(status_summary, hide_index=True, use_container_width=True)

    with col_chart:
        st.markdown("<div class='viz-card'><div class='viz-title'>Nº ATENDIMENTOS POR STATUS POR MÉDICO RESPONSÁVEL PELO ACOMPANHAMENTO</div>", unsafe_allow_html=True)
        try:
            chart_event = st.plotly_chart(
                plot_status_by_med_resp(base_all),
                use_container_width=True,
                config={"displayModeBar": False},
                on_select="rerun",
                selection_mode="points",
                key=f"chart_status_med_resp_{st.session_state.get('chart_selector_reset_counter', 0)}",
            )
            update_filter_from_chart_event(chart_event)
        except TypeError:
            st.plotly_chart(plot_status_by_med_resp(base_all), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.busca_status_filter or st.session_state.busca_med_resp_filter:
        filtro_status = st.session_state.busca_status_filter or "Todos"
        filtro_med = st.session_state.busca_med_resp_filter or "Todos"
        st.caption(f"Filtro interativo aplicado: Status = {filtro_status} | Médico responsável = {filtro_med}")
        if st.button("Limpar filtro interativo", key="limpar_filtro_interativo_busca"):
            st.session_state.busca_status_filter = None
            st.session_state.busca_med_resp_filter = None
            st.session_state.status_selector_reset_counter = st.session_state.get("status_selector_reset_counter", 0) + 1
            st.session_state.chart_selector_reset_counter = st.session_state.get("chart_selector_reset_counter", 0) + 1
            st.rerun()

    col_motivo, col_med_nao_nav = st.columns([1.0, 1.0])
    nao_nav_base = nao_nav_df.copy()
    nao_nav_filtered = apply_nao_nav_filters(nao_nav_base)

    with col_motivo:
        st.markdown("<div class='viz-card'><div class='viz-title'>Motivos de Não Navegação</div>", unsafe_allow_html=True)
        try:
            motivo_event = st.plotly_chart(
                plot_motivos_nao_nav_bar(nao_nav_base),
                use_container_width=True,
                config={"displayModeBar": False},
                on_select="rerun",
                selection_mode="points",
                key=f"donut_motivo_nao_nav_busca_{st.session_state.get('nao_nav_motivo_reset_counter', 0)}",
            )
            update_nao_nav_motivo_event(motivo_event, nao_nav_base)
        except TypeError:
            st.plotly_chart(plot_motivos_nao_nav_bar(nao_nav_base), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_med_nao_nav:
        st.markdown("<div class='viz-card'><div class='viz-title'>Nº Atendimentos Não Navegados por Médico Resp. Acomp.</div>", unsafe_allow_html=True)
        try:
            med_event = st.plotly_chart(
                plot_nao_nav_por_med_resp(nao_nav_base),
                use_container_width=True,
                config={"displayModeBar": False},
                on_select="rerun",
                selection_mode="points",
                key=f"bar_med_nao_nav_busca_{st.session_state.get('nao_nav_med_reset_counter', 0)}",
            )
            update_nao_nav_med_event(med_event)
        except TypeError:
            st.plotly_chart(plot_nao_nav_por_med_resp(nao_nav_base), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.nao_nav_motivo_filter or st.session_state.nao_nav_med_resp_filter:
        st.caption(
            f"Filtro não navegação aplicado: Motivo = {st.session_state.nao_nav_motivo_filter or 'Todos'} | Médico resp. = {st.session_state.nao_nav_med_resp_filter or 'Todos'}"
        )
        if st.button("Limpar filtros de não navegação", key="limpar_filtros_nao_nav_busca"):
            st.session_state.nao_nav_motivo_filter = None
            st.session_state.nao_nav_med_resp_filter = None
            st.session_state.nao_nav_motivo_reset_counter = st.session_state.get("nao_nav_motivo_reset_counter", 0) + 1
            st.session_state.nao_nav_med_reset_counter = st.session_state.get("nao_nav_med_reset_counter", 0) + 1
            st.rerun()

    st.markdown("<div class='section-title'>Busca de Pacientes</div>", unsafe_allow_html=True)

    patologia_view = patologia_df.copy()
    radiologia_view = radiologia_df.copy()
    laboratorio_view = laboratorio_df.copy()

    if st.session_state.busca_status_filter:
        patologia_view = patologia_view[patologia_view["STATUS"] == st.session_state.busca_status_filter]
        radiologia_view = radiologia_view[radiologia_view["STATUS"] == st.session_state.busca_status_filter]
        laboratorio_view = laboratorio_view[laboratorio_view["STATUS"] == st.session_state.busca_status_filter]

    if st.session_state.busca_med_resp_filter is not None:
        med_filter = st.session_state.busca_med_resp_filter
        if med_filter == "SEM MÉDICO RESP.":
            patologia_view = patologia_view[patologia_view["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip() == ""]
            radiologia_view = radiologia_view[radiologia_view["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip() == ""]
            laboratorio_view = laboratorio_view[laboratorio_view["MÉD. RESP. ACOMP."].fillna("").astype(str).str.strip() == ""]
        else:
            patologia_view = patologia_view[patologia_view["MÉD. RESP. ACOMP."].fillna("").astype(str) == med_filter]
            radiologia_view = radiologia_view[radiologia_view["MÉD. RESP. ACOMP."].fillna("").astype(str) == med_filter]
            laboratorio_view = laboratorio_view[laboratorio_view["MÉD. RESP. ACOMP."].fillna("").astype(str) == med_filter]

    patologia_view = patologia_view.drop(columns=["ESPECIALIDADE", "SETOR SOLICITANTE"], errors="ignore")
    radiologia_view = radiologia_view.drop(columns=["ESPECIALIDADE"], errors="ignore")
    laboratorio_view = laboratorio_view.drop(columns=["ESPECIALIDADE"], errors="ignore")

    st.markdown("<div class='section-title'>Pacientes Não Navegados</div>", unsafe_allow_html=True)
    table_html(nao_nav_filtered, "ANALÍTICO PACIENTES NÃO NAVEGADOS", scroll=True)

    table_html(patologia_view, "PACIENTES IDENTIFICADOS - PATOLOGIA", scroll=True)
    table_html(radiologia_view, "PACIENTES IDENTIFICADOS - RADIOLOGIA", scroll=True)
    table_html(laboratorio_view, "PACIENTES IDENTIFICADOS - LABORATÓRIO", scroll=True)
    table_html(naveg_df, "ANALÍTICO PACIENTES NAVEGADOS", scroll=True)


def page_acomp():
    topbar()

    st.markdown('<div class="acomp-top-row">', unsafe_allow_html=True)
    cols = st.columns(5)
    with cols[0]:
        metric_card("Nº Atend. - Identificados", "1.497", "1.284 pacientes únicos")
    with cols[1]:
        metric_card("Nº Atend. - 1ª Consulta", "932", "847 pacientes únicos")
    with cols[2]:
        metric_card("Nº Atend. - 1º Tratamento", "611", "523 pacientes únicos")
    with cols[3]:
        metric_card("Taxa Conv. - 1ª Consulta", "62,3%", "1ª C. / identificados")
    with cols[4]:
        metric_card("Taxa Conv. - 1º Tratamento", "40,8%", "1º T. / identificados")
    st.markdown('</div>', unsafe_allow_html=True)

    cols = st.columns(6)
    with cols[0]:
        metric_card("Total - Produzido", money_card(sum_finance_col(naveg_df, "TOTAL - PRODUZIDO")), "")
    with cols[1]:
        metric_card("Total - Enviado", money_card(sum_finance_col(naveg_df, "TOTAL - ENVIADO")), "")
    with cols[2]:
        metric_card("Total - Pendente de Envio", money_card(sum_finance_col(naveg_df, "TOTAL - PENDENTE DE ENVIO")), "")
    with cols[3]:
        metric_card("Total - Recebido", money_card(sum_finance_col(naveg_df, "TOTAL - RECEBIDO")), "")
    with cols[4]:
        metric_card("Total - Valor a Vencer", money_card(sum_finance_col(naveg_df, "TOTAL - VALOR A VENCER")), "")
    with cols[5]:
        metric_card("Total - Vencido", money_card(sum_finance_col(naveg_df, "TOTAL - VENCIDO")), "")

    st.markdown('<div class="acomp-time-row">', unsafe_allow_html=True)
    cols = st.columns([1.2, 1, 1, 1.2])
    with cols[1]:
        metric_card("Tempo Médio Identificação - 1ª Consulta", "12,4 dias", "")
    with cols[2]:
        metric_card("Tempo Médio Identificação - 1º Tratamento", "27,8 dias", "")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="acomp-pillar-row">', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        mini_origin_block("Patologia", "378", "62,4%", "42,1%")
    with cols[1]:
        mini_origin_block("Radiologia", "432", "61,6%", "41,0%")
    with cols[2]:
        mini_origin_block("Laboratório", "687", "63,2%", "39,4%")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Enviado e Recebido por Hospital</div>", unsafe_allow_html=True)
    render_enviado_recebido_matrix(naveg_df)

    if st.session_state.naveg_hospital_filter or st.session_state.naveg_convenio_filter:
        st.caption(
            f"Filtro navegação aplicado: Hospital = {st.session_state.naveg_hospital_filter or 'Todos'} | Convênio = {st.session_state.naveg_convenio_filter or 'Todos'}"
        )
        if st.button("Limpar filtro Enviado e Recebido", key="limpar_filtro_enviado_recebido"):
            st.session_state.naveg_hospital_filter = None
            st.session_state.naveg_convenio_filter = None
            st.rerun()

    st.markdown("<div class='section-title'>Gráficos Gerais</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.25, .75])
    with col1:
        viz_container("Total Produzido por Mês", plot_area_monthly())
        viz_container("Total Recebido por Mês", plot_total_recebido_monthly(naveg_df))
    with col2:
        viz_container("Receita por Área", plot_donut_area_receita())

    col1, col2 = st.columns([1.0, 1.0])
    with col1:
        conv_sorted = receita_conv_df.sort_values("REC. TOTAL", ascending=False)
        viz_container_scroll(
            "Receita por Convênio",
            plot_hbar(conv_sorted["CONVÊNIO"].tolist(), conv_sorted["REC. TOTAL"].tolist()),
            height_px=360,
            width_px=980,
        )
    with col2:
        med_sorted = receita_med_df.sort_values("REC. TOTAL", ascending=False)
        viz_container_scroll(
            "Receita por Médico Oncologista/Hematologista",
            plot_hbar(med_sorted["MÉDICO"].tolist(), med_sorted["REC. TOTAL"].tolist()),
            height_px=360,
            width_px=1050,
        )

    col1, col2 = st.columns([1.0, 1.0])
    with col1:
        cid_sorted = receita_cid_df.sort_values("REC. TOTAL", ascending=False)
        viz_container_scroll(
            "Receita por CID",
            plot_hbar(
                cid_sorted["CID"].tolist(),
                cid_sorted["REC. TOTAL"].tolist(),
                left_margin=310,
            ),
            height_px=260,
            width_px=1300,
        )
    with col2:
        viz_container("Top 10 CID - 1º Tratamento", plot_donut_cid_top10())

    st.markdown("<div class='section-title'>Tabelas Gerenciais e Analíticas</div>", unsafe_allow_html=True)

    receita_med_view = receita_med_df.sort_values("% Receita", ascending=False)
    receita_conv_view = receita_conv_df.sort_values("% Receita", ascending=False)
    receita_cid_view = receita_cid_df.sort_values("% Receita", ascending=False)

    c1, c2, c3 = st.columns(3)
    with c1:
        table_html(receita_med_view, "Receita por Médico Oncologista/Hematologista", scroll=True)
    with c2:
        table_html(receita_conv_view, "Receita por Convênio", scroll=True)
    with c3:
        table_html(receita_cid_view, "Receita por CID", scroll=True)

    naveg_analitico_view = apply_naveg_filters(naveg_df)
    table_html(naveg_analitico_view, "Analítico Pacientes Navegados", scroll=True)

# ============================================================
# EXECUÇÃO
# ============================================================
sidebar()

if st.session_state.page == "Busca de Pacientes":
    page_busca()
else:
    page_acomp()

bottom_nav()

