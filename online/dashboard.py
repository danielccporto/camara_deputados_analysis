"""
Dashboard - Análise Legislativa da Câmara dos Deputados
========================================================

Exercício 6: Dashboard com Chain-of-Thoughts Prompting

Técnica utilizada: Chain-of-Thoughts (CoT)
- Etapa 1: Definição da arquitetura geral
- Etapa 2: Estruturação detalhada das abas
- Etapa 3: Geração do código Streamlit completo

Este dashboard foi desenvolvido através de 3 prompts encadeados para o Gemini,
refletindo a metodologia de decomposição de problemas complexos em etapas menores.

Versão: 1.0 (Overview completa)
Próximas: Exercício 7 (Despesas e Proposições com Batch-prompting)
"""

import streamlit as st
import pandas as pd
import json
import yaml
from PIL import Image
from pathlib import Path
import plotly.express as px

try:
    from assistant import render_assistant_tab
except Exception:
    render_assistant_tab = None


# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Câmara dos Deputados Analysis",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILOS PERSONALIZADOS
# ============================================================================
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .insight-box {
        background-color: #e8f4f8;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.3rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES AUXILIARES COM CACHE
# ============================================================================
@st.cache_data
def carregar_config():
    """Carrega configurações do arquivo config.yaml"""
    try:
        with open("data/config.yaml", "r", encoding="utf-8") as f:
            # tentamos ler como UTF-8 normal e como UTF-8-SIG (remove BOM)
            text = f.read()
        try:
            config = yaml.safe_load(text)
        except Exception:
            # tentar com BOM-friendly
            try:
                config = yaml.safe_load(text.encode('utf-8').decode('utf-8-sig'))
            except Exception:
                # fallback resiliente: extrai overview_summary manualmente
                if "overview_summary:" in text:
                    resumo = text.split("overview_summary:", 1)[1]
                    resumo = resumo.lstrip().lstrip("|").strip()
                    return {"overview_summary": resumo}
                return {}
        return config or {}
    except FileNotFoundError:
        st.info("ℹ️ Arquivo config.yaml não encontrado em data/ — use data/config.yaml para configurar a visão geral.")
        return {}
    except Exception as e:
        st.error("❌ Erro ao carregar data/config.yaml — verifique permissões e codificação.")
        return {}


@st.cache_data
def carregar_insights_deputados():
    """Carrega insights sobre distribuição de deputados"""
    try:
        with open("data/insights_distribuicao_deputados.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados
    except FileNotFoundError:
        st.warning("⚠️ Arquivo de insights não encontrado")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar insights: {e}")
        return None


@st.cache_data
def carregar_gráfico():
    """Carrega a imagem do gráfico de distribuição"""
    try:
        img = Image.open("docs/distribuicao_deputados.png")
        return img
    except FileNotFoundError:
        st.warning("⚠️ Arquivo de gráfico não encontrado")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar gráfico: {e}")
        return None


# ============================================================================
# FUNÇÕES AUXILIARES - ABA DESPESAS
# ============================================================================
@st.cache_data
def carregar_despesas():
    """Carrega dados de despesas dos deputados."""
    try:
        caminho_detalhado = Path("data/despesas_deputados_detalhadas.parquet")
        caminho_agregado = Path("data/serie_despesas_diarias_deputados.parquet")

        if caminho_detalhado.exists():
            df = pd.read_parquet(caminho_detalhado)
        else:
            df = pd.read_parquet(caminho_agregado)

        if 'dataDocumento' in df.columns:
            df['dataDocumento'] = pd.to_datetime(df['dataDocumento'], errors='coerce')
        return df
    except FileNotFoundError:
        st.warning("Arquivo de despesas não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar despesas: {e}")
        return None


@st.cache_data
def carregar_insights_despesas():
    """Carrega insights sobre despesas dos deputados."""
    try:
        with open("data/insights_despesas_deputados.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("insights", [])
    except FileNotFoundError:
        st.warning("Arquivo de insights não encontrado.")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar insights: {e}")
        return []


# ============================================================================
# FUNÇÕES AUXILIARES - ABA PROPOSIÇÕES
# ============================================================================
@st.cache_data
def carregar_proposicoes():
    """Carrega dados de proposições legislativas."""
    try:
        df = pd.read_parquet("data/proposicoes_deputados.parquet")
        # Nem sempre a coluna de data vem com o nome esperado; fazer verificação
        if 'dataApresentacao' in df.columns:
            df['dataApresentacao'] = pd.to_datetime(df['dataApresentacao'], errors='coerce')
        else:
            # tentar alternativas comuns
            for alt in ('data_apresentacao', 'dataApresentacao_iso', 'data'):
                if alt in df.columns:
                    df['dataApresentacao'] = pd.to_datetime(df[alt], errors='coerce')
                    break
        return df
    except FileNotFoundError:
        st.warning("Arquivo de proposições não encontrado.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar proposições: {e}")
        return None


@st.cache_data
def carregar_sumarizacoes():
    """Carrega sumarizações de proposições."""
    try:
        with open("data/sumarizacao_proposicoes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("resumos", [])
    except FileNotFoundError:
        st.warning("Arquivo de sumarizações não encontrado.")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar sumarizações: {e}")
        return []


# ============================================================================
# NAVEGAÇÃO COM ABAS
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "💰 Despesas", "📜 Proposições", "🤖 Assistente"])

# ============================================================================
# ABA 1: OVERVIEW
# ============================================================================
with tab1:
    st.title("🏛️ Câmara dos Deputados Analysis")
    st.divider()
    
    # Carregar dados
    config = carregar_config()
    insights = carregar_insights_deputados()
    grafico = carregar_gráfico()
    
    if config:
        # Descrição do projeto
        st.subheader("📋 Sobre o Projeto")
        descricao = config.get("overview_summary", "Descrição não disponível")
        st.write(descricao)
        
        st.divider()
        
        # Layout em colunas: gráfico e insights
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📈 Distribuição de Deputados por Partido")
            if grafico:
                st.image(grafico, use_column_width=True)
            else:
                st.info("Gráfico não disponível no momento")
        
        with col2:
            st.subheader("💡 Insights Gerados")
            if insights and "insights" in insights:
                insights_list = insights["insights"]
                
                if isinstance(insights_list, list):
                    for i, insight in enumerate(insights_list, 1):
                        st.markdown(f"""
                        <div class="insight-box">
                        <strong>Insight {i}:</strong><br>
                        {insight}
                        </div>
                        """, unsafe_allow_html=True)
                elif isinstance(insights_list, str):
                    # Se for string única
                    linhas = insights_list.split('\n')
                    for i, linha in enumerate(linhas, 1):
                        if linha.strip():
                            st.markdown(f"""
                            <div class="insight-box">
                            {linha}
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Insights não disponíveis ainda. Execute o pipeline de dados.")
        
        st.divider()
        
        # Informações técnicas
        st.subheader("🔧 Informações Técnicas")
        col_info1, col_info2, col_info3 = st.columns(3)
        
        with col_info1:
            st.metric("Fonte de Dados", "API Câmara")
        with col_info2:
            st.metric("Tecnologia", "Streamlit + Gemini")
        with col_info3:
            st.metric("Período", "Atual")


# ============================================================================
# ABA 2: DESPESAS (Placeholder para Exercício 7)
# ============================================================================
with tab2:
    st.title("💰 Análise de Despesas dos Deputados")
    
    # Carregar dados
    df_despesas = carregar_despesas()
    insights = carregar_insights_despesas()
    
    # Exibir insights
    if insights:
        st.subheader("💡 Insights Principais")
        if isinstance(insights, list):
            # Se for lista, exibir em colunas
            num_insights = min(len(insights), 3)
            cols = st.columns(num_insights)
            for idx, insight in enumerate(insights[:3]):
                with cols[idx % num_insights]:
                    st.info(insight)
        else:
            # Se for string
            st.info(str(insights))
        
        st.divider()
    
    if df_despesas is not None:
        if 'total_despesas' in df_despesas.columns and not df_despesas['total_despesas'].empty:
            total_geral = float(df_despesas['total_despesas'].sum())
            tipo_top = "N/A"
            if 'tipoDespesa' in df_despesas.columns:
                por_tipo = df_despesas.groupby('tipoDespesa', dropna=False)['total_despesas'].sum().sort_values(ascending=False)
                if not por_tipo.empty:
                    tipo_top = str(por_tipo.index[0])

            periodo = "N/A"
            if 'dataDocumento' in df_despesas.columns:
                datas_validas = df_despesas['dataDocumento'].dropna()
                if not datas_validas.empty:
                    periodo = f"{datas_validas.min().date()} ate {datas_validas.max().date()}"

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Geral (R$)", f"{total_geral:,.2f}")
            m2.metric("Tipo Mais Relevante", tipo_top)
            m3.metric("Periodo", periodo)
            st.divider()

        colunas_nome = ['nomeDeputado', 'nomeParlamentar', 'nome', 'deputado']
        coluna_deputado = next((col for col in colunas_nome if col in df_despesas.columns), None)

        if coluna_deputado is None:
            st.info("Base agregada detectada: exibindo analise geral de despesas.")

            if {'dataDocumento', 'total_despesas'}.issubset(df_despesas.columns):
                serie_tempo = (
                    df_despesas.groupby('dataDocumento', dropna=False)['total_despesas']
                    .sum()
                    .reset_index()
                    .sort_values('dataDocumento')
                )
                fig_tempo = px.line(
                    serie_tempo,
                    x='dataDocumento',
                    y='total_despesas',
                    title='Evolucao temporal das despesas agregadas',
                    labels={'dataDocumento': 'Data', 'total_despesas': 'Total de Despesas (R$)'},
                    markers=True,
                )
                st.plotly_chart(fig_tempo, use_container_width=True)

            if {'tipoDespesa', 'total_despesas'}.issubset(df_despesas.columns):
                st.subheader("📊 Top tipos de despesa")
                top_tipos = (
                    df_despesas.groupby('tipoDespesa', dropna=False)['total_despesas']
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                    .reset_index()
                )
                fig_tipos = px.bar(
                    top_tipos,
                    x='tipoDespesa',
                    y='total_despesas',
                    title='Top 10 tipos de despesa (valor total)',
                    labels={'tipoDespesa': 'Tipo de Despesa', 'total_despesas': 'Total de Despesas (R$)'},
                )
                st.plotly_chart(fig_tipos, use_container_width=True)
        else:
            deputados = sorted(df_despesas[coluna_deputado].dropna().astype(str).unique().tolist())
            deputado_selecionado = st.selectbox(
                "Selecione um deputado:",
                deputados if deputados else ["Sem dados"],
                key="despesas_deputado"
            )

            df_deputado = df_despesas[df_despesas[coluna_deputado].astype(str) == str(deputado_selecionado)].copy()

            if df_deputado.empty:
                st.warning(f"Sem dados de despesas para {deputado_selecionado}")
            else:
                if {'dataDocumento', 'tipoDespesa', 'total_despesas'}.issubset(df_deputado.columns):
                    df_serie = (
                        df_deputado.sort_values('dataDocumento')
                        .groupby(['dataDocumento', 'tipoDespesa'], dropna=False)['total_despesas']
                        .sum()
                        .reset_index()
                    )

                    fig = px.line(
                        df_serie,
                        x='dataDocumento',
                        y='total_despesas',
                        color='tipoDespesa',
                        title=f"Serie temporal de despesas - {deputado_selecionado}",
                        labels={'dataDocumento': 'Data', 'total_despesas': 'Total de Despesas (R$)', 'tipoDespesa': 'Tipo de Despesa'},
                        markers=True
                    )
                    fig.update_layout(hovermode='x unified', height=500)
                    st.plotly_chart(fig, use_container_width=True)

                st.subheader("📊 Resumo por tipo de despesa")
                if {'tipoDespesa', 'total_despesas'}.issubset(df_deputado.columns):
                    resumo = df_deputado.groupby('tipoDespesa', dropna=False)['total_despesas'].agg(['sum', 'mean']).round(2)
                    resumo.columns = ['Total (R$)', 'Media (R$)']
                    st.dataframe(resumo, use_container_width=True)
    else:
        st.error("Não foi possível carregar os dados de despesas.")


# ============================================================================
# ABA 3: PROPOSIÇÕES (Placeholder para Exercício 7)
# ============================================================================
with tab3:
    st.title("📜 Proposições Legislativas")
    
    # Carregar dados
    df_proposicoes = carregar_proposicoes()
    sumarizacoes = carregar_sumarizacoes()
    
    if df_proposicoes is not None:
        # Filtro por tema (opcional)
        temas_disponiveis = sorted(df_proposicoes['tema'].unique()) if 'tema' in df_proposicoes.columns else []
        temas_selecionados = st.multiselect(
            "🏷️ Filtrar por tema:",
            temas_disponiveis,
            key="proposicoes_tema"
        )
        
        # Aplicar filtro
        if temas_selecionados:
            df_filtrado = df_proposicoes[df_proposicoes['tema'].isin(temas_selecionados)]
        else:
            df_filtrado = df_proposicoes
        
        # Exibir tabela
        st.subheader("📋 Proposições")
        colunas_exibir = ['id', 'ementa', 'tema', 'dataApresentacao']
        colunas_exibir = [col for col in colunas_exibir if col in df_filtrado.columns]
        
        st.dataframe(
            df_filtrado[colunas_exibir].sort_values('dataApresentacao', ascending=False) if 'dataApresentacao' in df_filtrado.columns else df_filtrado,
            use_container_width=True,
            height=400
        )
        
        # Sumarizações
        if sumarizacoes:
            st.subheader("💡 Resumos e Insights")
            for idx, sumarizacao in enumerate(sumarizacoes, 1):
                with st.container():
                    st.markdown(f"**#{idx}** {sumarizacao}")
        else:
            st.info("ℹ️ Nenhuma sumarização disponível")
        
        st.divider()
        
        # Estatísticas
        st.subheader("📊 Estatísticas")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Proposições", len(df_filtrado))
        with col2:
            if 'tema' in df_filtrado.columns:
                st.metric("Temas Únicos", df_filtrado['tema'].nunique())
            else:
                st.metric("Temas Únicos", 0)
        with col3:
            if 'dataApresentacao' in df_filtrado.columns:
                dias_range = (df_filtrado['dataApresentacao'].max() - df_filtrado['dataApresentacao'].min()).days
                st.metric("Período (dias)", dias_range)

        st.divider()
        st.subheader("🤖 Chat especialista em Câmara dos Deputados")
        if render_assistant_tab is None:
            st.error("Não foi possível carregar o assistente.")
        else:
            render_assistant_tab(show_title=False, key_prefix="proposicoes")
    else:
        st.error("Não foi possível carregar as proposições.")


# ============================================================================
# ABA 4: ASSISTENTE
# ============================================================================
with tab4:
    if render_assistant_tab is None:
        st.error("Não foi possível carregar o assistente.")
    else:
        render_assistant_tab(key_prefix="assistente_tab")


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.title("ℹ️ Informações")
    
    st.markdown("""
    ### Projeto: Análise Legislativa
    
    **Objetivo:**
    Análise completa de dados da Câmara dos Deputados com:
    - Distribuição de deputados por partido
    - Análise de despesas públicas
    - Processamento de proposições legislativas
    
    **Técnicas Utilizadas:**
    - 🔗 Prompt-chaining (Exercício 4)
    - 🧠 Generated Knowledge (Exercício 4)
    - 🎯 Chain-of-Thoughts (Exercício 6)
    - 📦 Batch-prompting (Exercício 7)
    - 🤖 Self-Ask + FAISS (Exercício 8)
    
    **Fonte de Dados:**
    [Dados Abertos Câmara](https://dadosabertos.camara.leg.br/api/v2)
    """)
    
    st.divider()
    
    # Info técnica
    st.subheader("📊 Status do Pipeline")
    try:
        if Path("data/deputados.parquet").exists():
            st.success("✅ Deputados")
        if Path("data/serie_despesas_diarias_deputados.parquet").exists():
            st.success("✅ Despesas")
        if Path("data/proposicoes_deputados.parquet").exists():
            st.success("✅ Proposições")
    except:
        pass
    
    st.divider()
    st.caption("Versão 1.0 - Exercício 6: Chain-of-Thoughts")


if __name__ == "__main__":
    pass
