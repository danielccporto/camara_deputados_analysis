# Projeto: Análise e Visualização de Dados Legislativos

Este projeto é uma aplicação completa para coleta, análise, sumarização e visualização de dados legislativos da Câmara dos Deputados. Ele utiliza Python, APIs públicas, e modelos de linguagem (LLMs) para gerar insights e sumarizações interativas.

## Funcionalidades Principais

### 1. **Coleta de Dados**
- **Deputados Atuais**: Coleta informações dos deputados atuais da Câmara dos Deputados.
- **Despesas dos Deputados**: Agrupa despesas diárias por tipo e fornecedor.
- **Proposições Legislativas**: Coleta proposições tramitadas no período de referência com base em temas específicos (Economia, Educação, Ciência e Tecnologia).

### 2. **Análise de Dados**
- **Evolução Temporal**: Analisa a evolução temporal das despesas por tipo de despesa.
- **Ranking de Fornecedores**: Identifica os fornecedores mais frequentes e os valores associados.
- **Despesas Médias Diárias**: Calcula a média de despesas diárias por tipo de despesa.

### 3. **Modelos de Linguagem (LLMs)**
- Gera insights a partir das análises de dados utilizando o modelo Gemini.
- Sumariza proposições legislativas em chunks para facilitar a compreensão.

### 4. **Visualização e Dashboard**
- Painel interativo com abas:
  - **Overview**: Apresentação do projeto e insights gerais.
  - **Despesas**: Exibição de gráficos de distribuição e evolução de despesas.
  - **Proposições**: Mostra as sumarizações geradas para proposições legislativas.

## Estrutura do Projeto

```
├── data/                # Diretório para arquivos Parquet e JSON gerados
├── docs/                # Gráficos e arquivos de documentação visual
├── offline/             # Scripts para coleta e processamento de dados
│   ├── dataprep.py      # Coleta, processamento e integração de dados
├── online/              # Interface do dashboard
│   ├── dashboard.py     # Script principal para o painel interativo
├── requirements.txt     # Dependências do projeto
├── .env                 # Arquivo para variáveis de ambiente (chaves de API)
└── README.md            # Documentação do projeto
```

## Configuração do Ambiente

### 1. Clone o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd <NOME_DO_REPOSITORIO>
```

### 2. Crie e ative um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com a seguinte estrutura:
```
GOOGLE_API_KEY=<SUA_CHAVE_GEMINI>
```

## Execução

### 1. Coleta e Processamento de Dados
Execute o script `dataprep.py` para coletar e processar os dados:
```bash
python offline/dataprep.py
```

### 2. Inicialização do Dashboard
Inicie o painel interativo:
```bash
streamlit run online/dashboard.py
```

## Contribuições
Sugestões, melhorias e pull requests são bem-vindos. Certifique-se de seguir as diretrizes do projeto para contribuições.

## Licença
Este projeto está licenciado sob a [MIT License](LICENSE).

---
Desenvolvido com Python e paixão por dados.

