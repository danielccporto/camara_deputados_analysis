# Análise de Pontos Faltantes - Atividade de Pipeline de Dados

## 📋 Resumo Executivo

O projeto possui uma base sólida com **Exercícios 3, 4 e 5** implementados. **Faltam 3 componentes principais**: Dashboard (Ex 6-7), Assistente com IA (Ex 8) e Geração de Imagens (Ex 9).

---

## ✅ IMPLEMENTADO

### Exercício 3: Processamento de Deputados
- ✅ `coletar_deputados()` - Coleta via API e salva em `data/deputados.parquet`
- ✅ `gerar_grafico_distribuicao()` - Gráfico pizza em `docs/distribuicao_deputados.png`
- ✅ `gerar_insights_gemini()` - Insights em `data/insights_distribuicao_deputados.json`
- ✅ Usa Gemini com persona de analista político

### Exercício 4: Processamento de Despesas
- ✅ `coletar_despesas_deputados()` - Coleta despesas e agrupa por data + tipo
- ✅ Salva em `data/serie_despesas_diarias_deputados.parquet`
- ✅ `gerar_analise_gemini()` - **Prompt-chaining** em 3 etapas:
  1. Sugere 3 análises úteis
  2. Estrutura código modular
  3. Gera código completo com tratamento de erros
- ✅ `gerar_insights_despesas()` - **Generated Knowledge** usando resultados das análises
- ✅ Salva em `data/insights_despesas_deputados.json`

### Exercício 5: Processamento de Proposições
- ✅ `coletar_proposicoes()` - Coleta proposições dos temas: Economia(40), Educação(46), Ciência & Tecnologia(62)
- ✅ Coleta 10 proposições por tema
- ✅ Salva em `data/proposicoes_deputados.parquet`
- ✅ `sumarizar_proposicoes()` - **Sumarização por chunks**:
  - Itera por proposição
  - Resume em até 3 frases
  - Rate limiting (1s entre chamadas)
  - Salva em `data/sumarizacao_proposicoes.json`

---

## ❌ FALTANDO

### Exercício 6: Dashboard com Chain-of-Thoughts
**Status**: NÃO INICIADO
**Arquivo**: `online/dashboard.py` (não existe)

#### Requisitos:
1. Criar arquivo `online/dashboard.py`
2. Usar **3 etapas de Chain-of-Thought prompting** para gerar o código:
   - **Prompt 1**: Arquitetura geral do dashboard
   - **Prompt 2**: Estrutura das abas e componentes
   - **Prompt 3**: Código completo do Streamlit

3. **Aba "Overview"**:
   - ✅ Título e descrição
   - ✅ Exibir texto de `config.yaml` (já existe em config.yaml)
   - ✅ Exibir gráfico `docs/distribuicao_deputados.png`
   - ✅ Exibir insights de `data/insights_distribuicao_deputados.json`

4. **Aba "Despesas"**: Preparada para Exercício 7
5. **Aba "Proposições"**: Preparada para Exercício 7

#### Pontos de Avaliação:
- [ ] Função/código gerado em cada etapa do Chain-of-Thought
- [ ] Objetivo de cada prompt explicado
- [ ] Dashboard executa sem erros
- [ ] Overview exibe todos os elementos corretamente

---

### Exercício 7: Dashboard com Batch-prompting
**Status**: NÃO INICIADO
**Modifica**: `online/dashboard.py`

#### Requisitos:
1. **Aba "Despesas"** deve ter:
   - [ ] Exibir insights de `data/insights_despesas_deputados.json`
   - [ ] `st.selectbox` para seleção de deputado
   - [ ] Gráfico de série temporal (line chart) de despesas do deputado
   - [ ] Gráfico com dados de `data/serie_despesas_diarias_deputados.parquet`

2. **Aba "Proposições"** deve ter:
   - [ ] Tabela com dados de `data/proposicoes_deputados.parquet` (`st.dataframe`)
   - [ ] Exibir resumos de `data/sumarizacao_proposicoes.json`

3. **Técnica Batch-prompting**:
   - [ ] Um único prompt descreve detalhadamente AMBAS as abas
   - [ ] LLM gera código completo em uma única resposta
   - [ ] Menos back-and-forth que Chain-of-Thoughts

#### Pontos de Avaliação:
- [ ] Prompt único descreve ambas abas com detalhes
- [ ] Código gerado funciona sem erros
- [ ] Comparação entre Chain-of-Thoughts (Ex 6) vs Batch-prompting (Ex 7):
  - Qualidade do código gerado
  - Tempo de iteração
  - Modularidade
  - Clareza da resposta

---

### Exercício 8: Assistente Online com Base Vetorial
**Status**: NÃO INICIADO
**Arquivo**: Adicionar em `online/dashboard.py` ou novo arquivo

#### Requisitos Técnicos:
1. **Vetorização de Dados**:
   - [ ] Modelo: `neuralmind/bert-base-portuguese-cased`
   - [ ] Vetorizar:
     - Nomes dos deputados
     - Tipos de despesas
     - Ementas das proposições
     - Resumos das proposições
   - [ ] Armazenar em **FAISS** (base vetorial)

2. **Interface de Chat**:
   - [ ] Adicionar em aba "Proposições" ou nova aba "Assistente"
   - [ ] Input do usuário → Busca em FAISS → Resposta com Gemini

3. **Prompt do Sistema com Self-Ask**:
   - [ ] Explicar técnica de Self-Ask:
     - Decomposição de pergunta em sub-questões
     - Responder cada sub-questão
     - Integrar respostas na resposta final
   - [ ] Sistema instrui LLM a usar Self-Ask antes de responder

#### Testes Obrigatórios:
- [ ] Qual é o partido político com mais deputados?
- [ ] Qual é o deputado com mais despesas?
- [ ] Qual é o tipo de despesa mais declarada?
- [ ] Quais são as informações mais relevantes sobre proposições de "Economia"?
- [ ] Quais são as informações mais relevantes sobre "Ciência, Tecnologia e Inovação"?

#### Pontos de Avaliação:
- [ ] Implementação de Self-Ask explicada
- [ ] Respostas às 5 perguntas analisadas
- [ ] Qualidade da vetorização
- [ ] Acurácia da busca em FAISS

---

### Exercício 9: Geração de Imagens com Prompts
**Status**: NÃO INICIADO
**Plataforma**: Google Colab
**Modelo**: CompVis/stable-diffusion-v1-4

#### Requisitos:
1. **Análise Teórica** (documentar):
   - [ ] Arquitetura do Stable Diffusion
   - [ ] Limitações e vantagens
   - [ ] Comparar com DALL-e (teórico)
   - [ ] Comparar com MidJourney (teórico)

2. **Geração de Imagens** (2 proposições):
   - [ ] Extrair 2 proposições de `data/proposicoes_deputados.parquet`
   - [ ] Usar `data/sumarizacao_proposicoes.json` para gerar prompts
   - [ ] Gerar **3 versões** por proposição com técnicas:
     - [ ] Versão 1: "Estilo Visual" (ex: artístico, fotorealista)
     - [ ] Versão 2: "Composição" diferente (ex: zoom in, wide angle)
     - [ ] Versão 3: Com **Negative Prompting** (ex: "sem pessoas, sem texto")

3. **Comparação**:
   - [ ] Avaliar diferenças entre resultados
   - [ ] Analisar impacto do negative prompting
   - [ ] Documento comparativo das 6 imagens (3 x 2 proposições)

#### Pontos de Avaliação:
- [ ] Descrição das arquiteturas de imagem
- [ ] 6 imagens geradas (3 por proposição)
- [ ] Análise qualitativa das diferenças
- [ ] Importância do negative prompting evidenciada

---

## 📊 Matriz de Completude

| Exercício | Status | Prioridade | Dependências |
|-----------|--------|-----------|--------------|
| 3 | ✅ 100% | - | - |
| 4 | ✅ 100% | - | Ex 3 |
| 5 | ✅ 100% | - | - |
| 6 | ❌ 0% | 🔴 Alta | Ex 3-5 |
| 7 | ❌ 0% | 🔴 Alta | Ex 6 |
| 8 | ❌ 0% | 🟠 Média | Ex 5, Ex 7 |
| 9 | ❌ 0% | 🟠 Média | Colab externo |

---

## 🎯 Próximos Passos (Sugerido)

### Fase 1: Dashboard (Ex 6-7)
1. Implementar `online/dashboard.py` com Chain-of-Thoughts
2. Adicionar abas com Batch-prompting
3. Validar toda visualização

### Fase 2: Assistente (Ex 8)
1. Configurar modelo BERT português
2. Implementar FAISS
3. Integrar chat no dashboard
4. Testar com 5 perguntas

### Fase 3: Imagens (Ex 9)
1. Preparar notebooks Colab
2. Gerar 6 imagens
3. Documentar análise comparativa

---

## 📝 Arquivos Necessários

```
Criar:
├── online/
│   ├── __init__.py
│   └── dashboard.py          ← Exercícios 6-7

Modificar:
├── requirements.txt          ← Adicionar streamlit, faiss, transformers
└── .env                       ← Pode precisar mais chaves

Documentar:
├── docs/
│   ├── analise_sd.md         ← Stable Diffusion análise
│   └── imagens/
│       ├── proporcao_1_v1-3.png
│       └── proporcao_2_v1-3.png
```

---

## 🚀 Recomendação

**Começar pelo Exercício 6 (Dashboard)** pois:
- ✅ Todos os dados já existem
- ✅ Demonstra a solução completa
- ✅ Base para o Assistente (Ex 8)

