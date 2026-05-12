# Exercício 6: Dashboard com Chain-of-Thoughts Prompting

## 📌 Resumo Executivo

Este exercício implementa a **Aba Overview** do dashboard utilizando a técnica **Chain-of-Thoughts (CoT)** prompting, onde o código foi desenvolvido através de **3 prompts encadeados** ao modelo Gemini.

---

## 🎯 Objetivo da Técnica Chain-of-Thoughts

A técnica CoT decomposição um problema complexo em **múltiplas etapas de raciocínio**:

1. **Primeiro prompt**: Pensa sobre a arquitetura geral
2. **Segundo prompt**: Estrutura os detalhes específicos
3. **Terceiro prompt**: Gera o código final refinado

**Vantagem**: O modelo entende melhor o contexto completo, gerando código mais estruturado, modular e com melhor tratamento de erros.

---

## 📊 Estrutura de Prompts

### **ETAPA 1: Arquitetura Geral**

#### Objetivo do Prompt:
Definir a estrutura global, fluxo de dados e componentes principais do dashboard.

#### Conteúdo do Prompt:
```
Você é um especialista em desenvolvimento de dashboards com Streamlit.

OBJETIVO: Descrever a arquitetura geral de um dashboard para análise de dados legislativos
da Câmara dos Deputados.

O dashboard deve ter:
- 3 abas principais: Overview, Despesas e Proposições
- Tema visual profissional e consistente
- Navegação intuitiva
- Componentes reutilizáveis

TAREFA:
1. Estruture a arquitetura geral em camadas (UI, dados, processamento)
2. Descreva o fluxo de dados do arquivo Parquet até a visualização
3. Defina como as abas devem se comunicar
4. Sugira componentes principais (sidebar, headers, footers)
```

#### Resposta Esperada:
- Descrição de arquitetura em camadas
- Fluxo de dados
- Padrões de design
- Componentes principais

#### Por que esta etapa é importante?
Estabelece a **visão geral** que guiará as etapas seguintes. Sem arquitetura clara, o código fica desorganizado.

---

### **ETAPA 2: Estrutura Detalhada das Abas**

#### Objetivo do Prompt:
Especificar cada componente Streamlit da aba Overview com layout e tratamento de erros.

#### Conteúdo do Prompt:
```
Com base na arquitetura anterior:
[arquitetura_respondida]

AGORA, detalhe a estrutura de cada aba:

**ABA 1 - OVERVIEW:**
- Título: "Análise Legislativa da Câmara dos Deputados"
- Descrição: Carregada de 'config.yaml'
- Exibir gráfico de pizza: 'docs/distribuicao_deputados.png'
- Mostrar insights: 'data/insights_distribuicao_deputados.json'
- Layout: descrição em colunas, depois gráfico à esquerda, insights à direita

**ABA 2 e 3:**
- Placeholder com st.info("Em desenvolvimento...")

TAREFA:
1. Detalhe os componentes de cada aba
2. Especifique tipos de componentes Streamlit (st.image, st.write, st.json, etc)
3. Descreva o layout e posicionamento
4. Defina tratamento de erros
```

#### Resposta Esperada:
- Especificação de cada componente
- Tipos de dados e fontes
- Layout com colunas/containers
- Estratégia de erro

#### Por que esta etapa é importante?
Converte a **visão geral** em **especificações técnicas** que podem ser implementadas.

---

### **ETAPA 3: Código Completo**

#### Objetivo do Prompt:
Gerar o código Python final do Streamlit, pronto para produção.

#### Conteúdo do Prompt:
```
Com base na arquitetura e estrutura anteriores:
[arquitetura_respondida]
[estrutura_respondida]

TAREFA: Gere o código completo em Streamlit para o dashboard.

REQUISITOS:
1. Arquivo: online/dashboard.py
2. Imports: streamlit, pandas, PIL, json, yaml
3. Config: wide layout, página_icon 🏛️
4. Aba Overview com:
   - Carregamento de config.yaml
   - Exibição de imagem
   - Exibição de insights formatados
   - Tratamento de erro se arquivo não existir
5. Função de cache com @st.cache_data
6. Abas 2 e 3: Placeholders

IMPORTANTE:
- Use caminhos relativos
- Código pronto para produção
- Retorne APENAS código Python
```

#### Resposta Esperada:
- Código completo e funcional
- Sem bugs ou erros de sintaxe
- Pronto para executar: `streamlit run online/dashboard.py`

#### Por que esta etapa é importante?
Gera o **código final refinado**, que já incorpora o conhecimento das 2 etapas anteriores.

---

## 💻 Código Gerado

### Localização:
`online/dashboard.py`

### Componentes Principais:

#### 1️⃣ **Configuração da Página**
```python
st.set_page_config(
    page_title="Câmara dos Deputados Analysis",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)
```
- Layout **wide** para aproveitar tela inteira
- Ícone 🏛️ para tema legislativo
- Sidebar expandida por padrão

#### 2️⃣ **Funções com Cache**
```python
@st.cache_data
def carregar_config():
    with open("data/config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
```
- Cache reduz leitura de arquivos
- Melhora performance
- Tratamento de erro integrado

#### 3️⃣ **Abas Tabuladas**
```python
tab1, tab2, tab3 = st.tabs(["📊 Overview", "💰 Despesas", "📜 Proposições"])

with tab1:
    # Conteúdo da aba Overview
```
- Interface intuitiva com abas
- Emojis para identificação rápida

#### 4️⃣ **Aba Overview**
```python
# Título e descrição
st.title("🏛️ Câmara dos Deputados Analysis")
descricao = config.get("overview_summary")
st.write(descricao)

# Layout em 2 colunas
col1, col2 = st.columns([1, 1])

with col1:
    st.image(grafico, use_column_width=True)

with col2:
    for insight in insights["insights"]:
        st.markdown(f"<div class='insight-box'>{insight}</div>")
```
- Descrição do projeto
- Gráfico de distribuição
- Insights formatados

#### 5️⃣ **Sidebar com Informações**
```python
with st.sidebar:
    st.title("ℹ️ Informações")
    st.markdown("### Projeto: Análise Legislativa...")
    # Status do pipeline
    if Path("data/deputados.parquet").exists():
        st.success("✅ Deputados")
```
- Metadados sobre o projeto
- Status dos dados disponíveis

---

## ✅ Validação

### Arquivos Criados:
- ✅ `online/dashboard.py` - Código Streamlit completo
- ✅ `online/__init__.py` - Módulo Python

### Funcionalidades Implementadas:

| Requisito | Status | Descrição |
|-----------|--------|-----------|
| Aba Overview | ✅ | Exibe título, descrição, gráfico e insights |
| Carregamento config.yaml | ✅ | Carrega summary_overview |
| Gráfico distribuição | ✅ | Exibe PNG em coluna |
| Insights Gemini | ✅ | Exibe insights formatados |
| Abas Despesas/Proposições | ✅ | Placeholders para Exercício 7 |
| Cache de dados | ✅ | @st.cache_data em todas as funções |
| Tratamento de erros | ✅ | Try/except para cada carregamento |
| Sidebar | ✅ | Info projeto + status pipeline |
| Estilos personalizados | ✅ | CSS customizado para boxes |

---

## 🔍 Comparação: Chain-of-Thoughts vs Prompt Único

### ❌ Se tivéssemos usado um ÚNICO prompt:
```
"Gere um dashboard Streamlit com 3 abas..."
```

**Resultado esperado:**
- Código genérico, sem estrutura clara
- Menos tratamento de erros
- Abas incompletas
- Sem consideração de cache e performance
- Código menos profissional

### ✅ Com Chain-of-Thoughts (3 prompts):
- Arquitetura **clara e bem definida**
- Código **modular e reutilizável**
- **Tratamento robusto** de erros
- Cache de **performance otimizada**
- **Profissional** e pronto para produção

---

## 🧪 Como Executar

### Pré-requisitos:
```bash
pip install streamlit pyyaml pillow pandas
```

### Execução:
```bash
streamlit run online/dashboard.py
```

### Resultado:
- Dashboard abre em `http://localhost:8501`
- Aba Overview com gráfico e insights
- Abas Despesas e Proposições com placeholders

---

## 📝 Próximos Passos

### Exercício 7: Batch-prompting
- Implementar aba **Despesas** completa
- Implementar aba **Proposições** completa
- Um único prompt descreve ambas abas
- Comparar qualidade com Chain-of-Thoughts

### Exercício 8: Assistente com FAISS
- Adicionar interface de chat
- Vetorização com BERT português
- Base vetorial FAISS
- Self-Ask prompting

### Exercício 9: Geração de Imagens
- Google Colab
- Stable Diffusion
- Gerar 6 imagens (3x2 proposições)

---

## 📊 Conclusão

**Chain-of-Thoughts Prompting** foi efetivo para gerar código de dashboard porque:

1. **Decomposição**: Quebrou o problema em 3 etapas claras
2. **Raciocínio**: Cada etapa refinou a próxima
3. **Qualidade**: Código final foi estruturado e profissional
4. **Manutenibilidade**: Fácil entender e modificar
5. **Reutilização**: Componentes modulares

**Próximo exercício** testará **Batch-prompting**, que tenta fazer o mesmo em um único prompt mais detalhado.
