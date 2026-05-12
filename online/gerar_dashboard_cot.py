import streamlit as st
import json
import yaml
from pathlib import Path
from PIL import Image
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"


@st.cache_data
def load_config():
    """Load configuration from YAML file."""
    config_path = DATA_DIR / "config.yaml"
    if not config_path.exists():
        st.error(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        st.error(f"❌ Erro ao carregar configuração: {e}")
        return {}


@st.cache_data
def load_insights():
    """Load insights from JSON file."""
    insights_path = DATA_DIR / "insights_distribuicao_deputados.json"
    if not insights_path.exists():
        st.warning(f"⚠️ Arquivo de insights não encontrado: {insights_path}")
        return []
    
    try:
        with open(insights_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [insight for insight in data.get("insights", []) if insight.strip()]
    except Exception as e:
        st.error(f"❌ Erro ao carregar insights: {e}")
        return []


def load_image(image_name):
    """Load image from docs directory."""
    image_path = DOCS_DIR / image_name
    if not image_path.exists():
        st.warning(f"⚠️ Imagem não encontrada: {image_path}")
        return None
    
    try:
        return Image.open(image_path)
    except Exception as e:
        st.error(f"❌ Erro ao carregar imagem: {e}")
        return None


def render_overview_tab():
    """Render the Overview tab."""
    config = load_config()
    overview_summary = config.get("overview_summary", "Descrição não disponível.")
    
    st.title("📊 Análise Legislativa da Câmara dos Deputados")
    st.divider()
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### Sobre o Projeto")
        st.markdown(overview_summary)
    
    with col2:
        chart_image = load_image("distribuicao_deputados.png")
        if chart_image:
            st.image(chart_image, use_container_width=True, caption="Distribuição de Deputados por Partido")
        else:
            st.info("📈 Imagem do gráfico não disponível")
    
    st.divider()
    
    st.markdown("### 💡 Insights e Análises")
    insights = load_insights()
    
    if insights:
        for idx, insight in enumerate(insights, 1):
            with st.container():
                st.markdown(f"**Insight {idx}:**")
                st.markdown(insight)
    else:
        st.info("ℹ️ Nenhum insight disponível no momento")


def render_despesas_tab():
    """Render the Despesas tab (placeholder)."""
    st.title("💰 Análise de Despesas")
    st.info("🔨 Esta seção está em desenvolvimento. Dados sobre despesas diárias dos deputados e análises de padrões de gastos estarão disponíveis em breve.")
    
    st.markdown("""
    **Previsão de Conteúdo:**
    - Evolução temporal das despesas
    - Distribuição por tipo de despesa
    - Ranking de fornecedores
    - Despesas médias por deputado
    """)


def render_proposicoes_tab():
    """Render the Proposições tab (placeholder)."""
    st.title("📜 Proposições Legislativas")
    st.info("🔨 Esta seção está em desenvolvimento. Análise de proposições legislativas e suas sumarizações estarão disponíveis em breve.")
    
    st.markdown("""
    **Previsão de Conteúdo:**
    - Proposições por tema (Economia, Educação, Ciência e Tecnologia)
    - Sumarizações automáticas de projetos de lei
    - Cronologia de votações
    - Classificação por status
    """)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Câmara dos Deputados Analysis",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.sidebar.title("🏛️ Câmara dos Deputados")
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **Análise de Dados Legislativos**
    
    Este dashboard apresenta análises sobre:
    - Distribuição de deputados por partido
    - Despesas legislativas
    - Proposições em tramitação
    """)
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"*Atualizado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}*")
    
    tab1, tab2, tab3 = st.tabs(["Overview", "Despesas", "Proposições"])
    
    with tab1:
        render_overview_tab()
    
    with tab2:
        render_despesas_tab()
    
    with tab3:
        render_proposicoes_tab()


if __name__ == "__main__":
    main()
