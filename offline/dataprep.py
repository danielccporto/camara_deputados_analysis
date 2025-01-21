import requests
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai 
from dotenv import load_dotenv
import os
import json 
import sys
import time 


# Adiciona o diretório raiz ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")


# Define a URL base da API
URL_BASE = 'https://dadosabertos.camara.leg.br/api/v2'

def coletar_deputados():
    """
    Coleta os dados dos deputados atuais da Câmara dos Deputados e salva em formato Parquet.
    """
    url = f"{URL_BASE}/deputados"
    response = requests.get(url)
    
    if response.status_code == 200:
        deputados = response.json()['dados']
        df_deputados = pd.DataFrame(deputados)
        
        # Criação do diretório para armazenar o arquivo Parquet
        #os.makedirs("data", exist_ok=True)
        df_deputados.to_parquet("data/deputados.parquet", index=False)
        print("Dados dos deputados salvos em data/deputados.parquet")
    else:
        print(f"Erro ao acessar a API: {response.status_code}")

def gerar_grafico_distribuicao():
    """
    Gera um gráfico de pizza com a distribuição de deputados por partido.
    """
    # Lê o arquivo Parquet com os dados dos deputados
    df_deputados = pd.read_parquet("data/deputados.parquet")
    
    # Calcula a distribuição por partido
    distribuicao = df_deputados['siglaPartido'].value_counts()
    partidos = distribuicao.index
    valores = distribuicao.values
    
    # Criação do gráfico
    plt.figure(figsize=(10, 8))
    plt.pie(valores, labels=partidos, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
    plt.title("Distribuição de Deputados por Partido")
    
    # Salvar o gráfico
    os.makedirs("docs", exist_ok=True)
    plt.savefig("docs/distribuicao_deputados.png")
    plt.close()
    print("Gráfico salvo em docs/distribuicao_deputados.png")

    return distribuicao

def gerar_insights_gemini(distribuicao):
    """
    Gera insights utilizando o modelo Gemini com base na distribuição de deputados por partido.
    """
    # Configurar o cliente da API Gemini
    genai.configure(api_key=api_key)

    # Formatar os dados para o prompt
    distribuicao_dados = {
        "partidos": distribuicao.index.tolist(),
        "quantidade": distribuicao.values.tolist(),
        "percentual": (distribuicao / distribuicao.sum() * 100).round(2).tolist()
    }

    # Criar o prompt como string simples
    prompt = (
        "Você é um analista político experiente com profundo conhecimento sobre o sistema legislativo brasileiro.\n\n"
        f"A distribuição de deputados por partido é a seguinte: {distribuicao_dados}.\n\n"
        "Forneça insights sobre como a composição dos partidos influencia o funcionamento da Câmara dos Deputados."
    )

    # Enviar o prompt ao modelo usando generate_content
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    insights = response.text.split("\n")
    
    # Salvar os insights
    salvar_insights(insights)


def salvar_insights(insights):
    with open("data/insights_distribuicao_deputados.json", "w", encoding="utf-8") as f:
        json.dump({"insights": insights}, f, indent=4, ensure_ascii=False)
    print("Insights salvos em data/insights_distribuicao_deputados.json")

def coletar_despesas_deputados():
    """
    Coleta as informações de despesas dos deputados atuais e salva em formato Parquet.
    Agrupa por dia, deputado e tipo de despesa.
    """

    df_deputados = pd.read_parquet("data/deputados.parquet")
    ids_deputados = df_deputados["id"].tolist()
    despesas = []

    # Iterar sobre os IDs dos deputados
    for id_deputado in ids_deputados:
        url = f"{URL_BASE}/deputados/{id_deputado}/despesas"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Adicionar os dados ao dataframe
            despesas.extend(response.json().get("dados", []))
        else:
            print(f"Erro ao acessar as despesas do deputado {id_deputado}: {response.status_code}")

    # Criar DataFrame com os dados coletados
    df_despesas = pd.DataFrame(despesas)

    # Verificar se o DataFrame não está vazio
    if df_despesas.empty:
        print("Nenhuma despesa foi coletada.")
        return

    #Columns Check
    #print("Colunas disponíveis no DataFrame de despesas:", df_despesas.columns.tolist())


    # Selecionar colunas relevantes
    colunas_relevantes = ["dataDocumento", "nomeFornecedor", "tipoDespesa", "valorLiquido"]
    df_despesas = df_despesas[colunas_relevantes]

    # Converter data para formato datetime
    df_despesas["dataDocumento"] = pd.to_datetime(df_despesas["dataDocumento"])

    # Agrupar os dados por dia, deputado e tipo de despesa
    df_agrupado = df_despesas.groupby(
        ["dataDocumento", "tipoDespesa"]
    ).agg(
        total_despesas=("valorLiquido", "sum"),
        fornecedores=("nomeFornecedor", lambda x: list(set(x)))
    ).reset_index()

    # Salvar os dados no formato Parquet
    os.makedirs("data", exist_ok=True)
    df_agrupado.to_parquet("data/serie_despesas_diarias_deputados.parquet", index=False)
    print("Dados de despesas salvos em data/serie_despesas_diarias_deputados.parquet")

    #Visualização arquivo 
    df = pd.read_parquet("data/serie_despesas_diarias_deputados.parquet")
    print(df.columns.to_list())
    print(df.dtypes)

def gerar_analise_gemini():
    """
    Chama o modelo Gemini para gerar um código Python que analise os dados
    das despesas diárias dos deputados com base no prompt fornecido.
    """
    genai.configure(api_key=api_key)

    #Prompt para geração de análises 
    prompt_start = ("""
        "Você é um especialista em análise de dados. Tenho um arquivo Parquet no caminho: "data/serie_despesas_diarias_deputados.parquet"
        "com informações das despesas dos deputados, contendo as colunas:\n"
        "- `dataDocumento` (datetime): Data da despesa.\n"
        "- `tipoDespesa` (string): Categoria da despesa.\n"
        "- `total_despesas` (float): Soma das despesas em uma data para um tipo específico.\n"
        "- `fornecedores` (list[string]): Lista de fornecedores associados às despesas.\n\n"
        "Sugira apenas 3 análises úteis que podem ser feitas com esses dados."
    """
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response_1 = model.generate_content(prompt_start)
    sugestoes = response_1.candidates[0].content
    print("Sugestões de análises:", sugestoes)

    prompt2 = (
        f"A partir das seguintes análises sugeridas:\n\n{sugestoes}\n\n"
        "Estruture um código Python em uma função modular, documentada, que gere gráficos usando `pandas`, "
        "`matplotlib`, ou `seaborn`."
    )

    response2 = model.generate_content(prompt2)
    estrutura_codigo = response2.candidates[0].content
    print("Estrutura do código gerada:", estrutura_codigo)

    prompt3 = (
        f"Com base na estrutura e análises detalhadas anteriormente, gere o código Python completo:\n\n{estrutura_codigo}\n\n"
        "Inclua tratamento de erros para arquivos ausentes ou vazios, modularidade com funções dedicadas para "
        "cada análise, e gráficos claros para os resultados."
        "Inclua também retornos para as funções das 3 análises do arquivo parquet a fim dos resultados poderem ser utilizados posteriormente"
    )
    response3 = model.generate_content(prompt3)
    codigo_final = str(response3.candidates[0].content)
    inicio = codigo_final.find("```python") + len("```python")
    fim = codigo_final.rfind("```")
    codigo_puro = codigo_final[inicio:fim].strip()
    codigo_tratado = (
    codigo_puro.replace("\\n", "\n")  # Corrigir quebras de linha escapadas
              .replace('\\"\\"\\"', '"""')  # Corrigir docstrings escapadas
              .replace('\\"', '"')
              .replace("\\'", "'")
              
)

    # Salvar o código em um arquivo Python
    os.makedirs("data", exist_ok=True)
    with open("data/generated_analysis.py", "w", encoding="utf-8") as f:
        f.write(codigo_tratado)

    print("Código Python gerado e salvo em 'generated_analysis.py'.")


def gerar_insights_despesas():
    """
    Gera insights utilizando os resultados das análises de despesas realizadas 
    no arquivo Parquet `data/serie_despesas_diarias_deputados.parquet`.
    Salva os insights gerados em `data/insights_despesas_deputados.json`.
    """
    from data.generated_analysis import analisar_despesas_deputados

    try:
        # Configurar a API do LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)

        # Caminho do arquivo Parquet
        caminho_parquet = "data/serie_despesas_diarias_deputados.parquet"

        # Executar as análises (retorna figuras, não DataFrames)
        fig_tempo, fig_fornecedor, fig_medias = analisar_despesas_deputados(caminho_parquet)

        if fig_tempo is None or fig_fornecedor is None or fig_medias is None:
            print("Erro: Não foi possível obter resultados das análises.")
            return

        # Criar o prompt com os resultados das análises
        prompt = f"""
        Você é um especialista em finanças públicas e análise de dados. Com base nas análises realizadas sobre os dados de despesas de deputados, seguem as observações:

        1. **Evolução Temporal das Despesas**:
           - Gráfico da evolução temporal gerado.

        2. **Ranking de Fornecedores**:
           - Gráfico do ranking de fornecedores gerado.

        3. **Despesas Médias Diárias por Tipo**:
           - Gráfico das médias diárias por tipo de despesa gerado.

        Com base nesses resultados, forneça insights sobre os padrões de gastos, possíveis irregularidades e recomendações para uma gestão financeira mais eficiente.
        """

        # Enviar o prompt ao modelo LLM
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Verificar a resposta e processar os insights
        if response.candidates and len(response.candidates) > 0:
            parts = response.candidates[0].content.parts
            insights = "".join([part.text for part in parts])
        else:
            insights = "Erro ao gerar insights."

        # Salvar os insights em um arquivo JSON
        output_path = "data/insights_despesas_deputados.json"
        os.makedirs("data", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"insights": insights}, f, indent=4, ensure_ascii=False)

        print(f"Insights salvos em '{output_path}'.")

    except Exception as e:
        print(f"Erro ao gerar insights: {e}")


def coletar_proposicoes(data_inicio, data_fim):
    """
    Coleta informações de proposições que tramitam no período especificado e pertencem aos temas:
    'Economia', 'Educação' e 'Ciência, Tecnologia e Inovação'.
    Salva os dados coletados em um arquivo Parquet.

    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'.
        data_fim (str): Data de fim no formato 'YYYY-MM-DD'.

    Returns:
        None. Salva os dados em 'data/proposicoes_deputados.parquet'.
    """
    # URL base da API
    URL_BASE = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

    # Temas e seus códigos
    temas = {
        "Economia": 40,
        "Educação": 46,
        "Ciência, Tecnologia e Inovação": 62
    }

    # Armazenar os resultados
    proposicoes_totais = []

    # Coleta de proposições por tema
    for tema, cod_tema in temas.items():
        params = {
            "dataInicio": data_inicio,
            "dataFim": data_fim,
            "codTema": cod_tema,
            "itens": 10  # Limitar a 10 proposições por tema
        }

        # Fazer a solicitação GET à API
        response = requests.get(URL_BASE, params=params)
        if response.status_code == 200:
            dados = response.json().get('dados', [])
            for proposicao in dados:
                proposicao['tema'] = tema  # Adicionar o tema aos dados
                proposicoes_totais.append(proposicao)
        else:
            print(f"Erro ao acessar API para o tema {tema}: {response.status_code}")

    # Transformar os dados em um DataFrame
    if proposicoes_totais:
        df_proposicoes = pd.DataFrame(proposicoes_totais)

        # Criar o diretório data se não existir
        os.makedirs("data", exist_ok=True)

        # Salvar os dados em formato Parquet
        df_proposicoes.to_parquet("data/proposicoes_deputados.parquet", index=False)
        print("Proposições salvas em 'data/proposicoes_deputados.parquet'.")
    else:
        print("Nenhuma proposição foi coletada.")


def sumarizar_proposicoes():
    """
    Realiza a sumarização por chunks das proposições tramitadas no período de referência.
    Salva o resumo gerado em 'data/sumarizacao_proposicoes.json'.
    """
    try:
        # Configurar a API do LLM
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Carregar as proposições do arquivo Parquet
        caminho_proposicoes = "data/proposicoes_deputados.parquet"
        df_proposicoes = pd.read_parquet(caminho_proposicoes)

        # Verificar se o DataFrame está vazio
        if df_proposicoes.empty:
            print("Nenhuma proposição encontrada para sumarização.")
            return

        # Criar chunks para sumarização
        chunks = []
        for _, row in df_proposicoes.iterrows():
            ementa = row.get("ementa", "Sem ementa disponível.")
            tema = row.get("tema", "Sem tema disponível.")
            chunks.append(f"Tema: {tema}\nEmenta: {ementa}\n")

        # Inicializar resumos existentes (se houver)
        output_path = "data/sumarizacao_proposicoes.json"
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                summaries = json.load(f)["resumos"]
        else:
            summaries = []

        # Processar cada chunk com rate limiting
        for chunk in chunks[len(summaries):]:  # Evitar reprocessar já sumarizados
            prompt = f"""
            Aqui está uma proposição da Câmara dos Deputados:
            {chunk}

            Por favor, resuma o tema e os pontos principais em até 3 frases.
            """
            model = genai.GenerativeModel("gemini-1.5-flash")

            try:
                response = model.generate_content(prompt)
                if response.candidates and len(response.candidates) > 0:
                    parts = response.candidates[0].content.parts
                    resumo = "".join([part.text for part in parts])
                    summaries.append(resumo.strip())
                else:
                    summaries.append("Erro ao gerar resumo para o chunk.")
            except Exception as e:
                print(f"Erro na chamada à API: {e}")
                break  # Parar em caso de erro de quota

            time.sleep(1)  # Aguardar para evitar excesso de chamadas

        # Salvar os resumos em um arquivo JSON
        os.makedirs("data", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"resumos": summaries}, f, indent=4, ensure_ascii=False)

        print(f"Sumarizações salvas em '{output_path}'.")

    except Exception as e:
        print(f"Erro ao sumarizar proposições: {e}")





if __name__ == "__main__":
    
    coletar_deputados()
    distribuicao = gerar_grafico_distribuicao()
    gerar_insights_gemini(distribuicao)
    coletar_despesas_deputados()
    gerar_analise_gemini()
    gerar_insights_despesas()
    coletar_proposicoes(data_inicio="2024-08-01", data_fim="2024-08-30")
    sumarizar_proposicoes() 

