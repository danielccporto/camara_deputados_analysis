# Exercício 7: Dashboard - Abas Despesas e Proposições com Batch-prompting

## 📌 Resumo Executivo

Este exercício implementa as **abas Despesas e Proposições** usando a técnica **Batch-prompting**, onde um **único prompt detalhado** descreve todas as funcionalidades de ambas as abas, e o Gemini gera o código completo em uma única resposta.

---

## 🎯 Objetivo da Técnica Batch-prompting

Batch-prompting é uma abordagem onde você:
- **Descreve TUDO em um único prompt**: Todos os requisitos, componentes e regras
- **Fornece contexto completo**: Dados, arquivos, estrutura
- **Pede código completo**: Em uma única resposta

**Diferença de Chain-of-Thoughts**:
- **CoT (Ex 6)**: 3 prompts pequenos, encadeados progressivamente → Melhor para estruturação
- **Batch (Ex 7)**: 1 prompt grande, com tudo detalhado → Melhor para geração rápida

---

## 📊 Estrutura do Prompt Batch

### **PROMPT ÚNICO: Abas Despesas e Proposições**

#### Objetivo do Prompt:
Gerar código Streamlit **completo e funcional** para AMBAS as abas em uma única resposta.

#### Conteúdo do Prompt (Detalhado):

```
Você é um especialista em desenvolvimento de dashboards com Streamlit para análise de dados legislativos.

CONTEXTO:
- Projeto: Câmara dos Deputados Analysis
- Arquivo base: online/dashboard.py (código Overview já existe)
- Plataforma: Streamlit
- Dados disponíveis:
  * data/serie_despesas_diarias_deputados.parquet
  * data/insights_despesas_deputados.json
  * data/proposicoes_deputados.parquet
  * data/sumarizacao_proposicoes.json

==============================================================================
ABA 2 - DESPESAS (REQUISITOS DETALHADOS)
==============================================================================

1. TÍTULO E DESCRIÇÃO:
   - st.title("💰 Análise de Despesas dos Deputados")
   - st.markdown("Análise detalhada das despesas declaradas pelos deputados...")

2. INSIGHTS SOBRE DESPESAS:
   - Carregar insights_despesas_deputados.json
   - Exibir cada insight em container formatado
   - Usar cores e emojis para destacar

3. SELEÇÃO DE DEPUTADO (st.selectbox):
   - Extrair lista única de deputados de serie_despesas_diarias_deputados.parquet
   - Componente: st.selectbox("Selecione um deputado:", deputados)
   - Valor padrão: primeiro deputado da lista

4. GRÁFICO DE SÉRIE TEMPORAL (Line Chart):
   - Filtrar dados do parquet para deputado selecionado
   - Eixo X: data (dataDocumento)
   - Eixo Y: total_despesas
   - Agrupar por: tipoDespesa (cores diferentes para cada tipo)
   - Usar st.line_chart() OU plotly/matplotlib
   - Título: "Série Temporal de Despesas - [Nome Deputado]"
   - Incluir legenda

5. TABELA ADICIONAL (opcional):
   - Mostrar resumo de despesas por tipo para deputado selecionado
   - st.dataframe() com colunas: tipo, total, média

6. TRATAMENTO DE ERROS:
   - Se arquivo não existir → st.error()
   - Se deputado não tiver dados → st.warning()
   - Use try/except em carregamentos

==============================================================================
ABA 3 - PROPOSIÇÕES (REQUISITOS DETALHADOS)
==============================================================================

1. TÍTULO E DESCRIÇÃO:
   - st.title("📜 Proposições Legislativas")
   - st.markdown("Proposições tramitadas na câmara com resumos gerados por IA...")

2. TABELA DE PROPOSIÇÕES:
   - Carregar proposicoes_deputados.parquet
   - Exibir com st.dataframe()
   - Colunas principais: id, ementa, tema, dataApresentacao
   - Altura: 400px
   - Usar-column=True para ocupar toda a largura

3. RESUMOS DAS PROPOSIÇÕES:
   - Carregar sumarizacao_proposicoes.json
   - Exibir de forma organizada:
     * Um resumo por proposição
     * Numerado (Proposição 1, 2, 3, ...)
     * Em containers com background colorido
     * Relacionar resumo com proposição

4. FILTRO POR TEMA (Bônus):
   - st.multiselect("Filtrar por tema:", temas únicos)
   - Atualizar tabela dinamicamente

5. TRATAMENTO DE ERROS:
   - Se arquivo não existir → st.error()
   - Se vazio → st.warning()
   - Use try/except

==============================================================================
REQUISITOS TÉCNICOS GERAIS
==============================================================================

1. IMPORTAÇÕES:
   - streamlit, pandas, json, yaml, pathlib
   - Plotly (se usar gráficos avançados)

2. CACHE:
   - @st.cache_data em todas funções de carregamento
   - Reduzir I/O de arquivos

3. LAYOUT:
   - Usar st.columns() para organização
   - Manter consistência com aba Overview
   - Espaçamento com st.divider()

4. CODIFICAÇÃO:
   - Arquivo: utf-8
   - Comentários em português
   - Docstrings em todas as funções

5. ESTILOS:
   - Usar emojis para organização
   - Cores consistentes
   - Fontes legíveis

==============================================================================
CÓDIGO A RETORNAR
==============================================================================

Retorne APENAS O CÓDIGO completo das duas abas (Despesas e Proposições).
NÃO INCLUA a aba Overview (já existe).
NÃO inclua configuração de página (já existe).

O código deve ser um "block" pronto para inserir no arquivo dashboard.py.

FORMATO:
- Use este padrão para inserir no dashboard.py:

with tab2:  # Despesas
    [seu código aqui]

with tab3:  # Proposições
    [seu código aqui]

E defina as funções auxiliares FORA das abas (no escopo global).
```

#### Resposta Esperada:
- Código das 2 abas completo
- Funções auxiliares com cache
- Tratamento de erros integrado
- Pronto para copiar-colar no dashboard.py

---

## ✨ Vantagens do Batch-prompting

| Aspecto | Chain-of-Thoughts | Batch-prompting |
|--------|------------------|-----------------|
| **Número de prompts** | 3-5 | 1 |
| **Tempo de iteração** | Mais longo | Mais rápido |
| **Estruturação** | Melhor | Boa |
| **Detalhes no prompt** | Menos | Mais |
| **Qualidade do código** | Muito boa | Muito boa |
| **Uso de tokens** | Mais (3x) | Menos |
| **Adequado para** | Projetos complexos | Tarefas bem definidas |

---

## 📝 Comparação Final

### Chain-of-Thoughts (Exercício 6):
```
Prompt 1: "Qual é a arquitetura?"
         ↓ (incorpora resposta)
Prompt 2: "Como estruturar as abas?"
         ↓ (incorpora resposta)
Prompt 3: "Gere o código"
         ↓
Resultado: Código muito estruturado
```

### Batch-prompting (Exercício 7):
```
Prompt Único: "Aqui estão TODOS os requisitos das 2 abas,
              todas as colunas de dados, todos os tratamentos
              de erro, todos os estilos... Gere o código!"
         ↓
Resultado: Código muito detalhado e específico
```

---

## 🔍 Análise Qualitativa

Após implementar ambas técnicas, é possível avaliar:

**Aspecto 1: Modularidade do Código**
- **CoT**: Código mais "pensado", com separações lógicas claras
- **Batch**: Código mais "rápido", direto ao ponto

**Aspecto 2: Tratamento de Erros**
- **CoT**: Inclui mais camadas de validação
- **Batch**: Valida o que foi pedido no prompt

**Aspecto 3: Eficiência de Tokens**
- **CoT**: ~3x mais tokens (3 prompts)
- **Batch**: ~1x tokens (1 prompt grande)

**Aspecto 4: Tempo de Desenvolvimento**
- **CoT**: Mais interações, mais tempo
- **Batch**: Uma resposta, menos tempo

**Aspecto 5: Qualidade Final**
- **CoT**: Excelente para código crítico
- **Batch**: Excelente para funcionalidades bem definidas

---

## 🚀 Próximos Passos

Após a implementação:

1. ✅ **Validar funcionamento** do dashboard completo
2. ✅ **Comparar visualmente** as abas geradas
3. ✅ **Documentar diferenças** de qualidade
4. ✅ **Fazer benchmark** de tempo e tokens
5. ✅ **Decidir qual técnica** usar em projetos futuros

---

## 📊 Conclusão

**Batch-prompting é efetivo quando**:
- Os requisitos estão **bem definidos**
- As estruturas de dados são **conhecidas**
- A tarefa é **bem circumscrita**
- Quer-se **rapidez** na geração

**Chain-of-Thoughts é melhor quando**:
- O problema é **complexo e multifacetado**
- Quer-se **máxima qualidade** e estruturação
- Os requisitos **evoluem durante o desenvolvimento**
- A **manutenibilidade** é crítica

---

## 📋 Checklist de Implementação

- [ ] Gerar código das abas com Batch-prompting
- [ ] Validar sintaxe Python
- [ ] Testar carregamento de dados
- [ ] Testar selectbox e filtros
- [ ] Comparar com código do Exercício 6
- [ ] Documentar diferenças observadas
- [ ] Atualizar dashboard.py com novo código
