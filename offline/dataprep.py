import requests
import pandas as pd
import matplotlib.pyplot as plt
import google.generativeai as genai 
from dotenv import load_dotenv
import os
import json 


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
    #df = pd.read_parquet("data/serie_despesas_diarias_deputados.parquet")
    #print(df.columns.to_list())
    #print(df.dtypes)

def gerar_analise_gemini():
    """
    Chama o modelo Gemini para gerar um código Python que analise os dados
    das despesas diárias dos deputados com base no prompt fornecido.
    """
    genai.configure(api_key=api_key)

    #Prompt para geração de análises 
    prompt_start = ("""
        "Você é um especialista em análise de dados. Tenho um arquivo Parquet com informações das despesas "
        "dos deputados, contendo as colunas:\n"
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
    )
    response3 = model.generate_content(prompt3)
    codigo_final = str(response3.candidates[0].content)
    inicio = codigo_final.find("```python") + len("```python")
    fim = codigo_final.rfind("```")
    codigo_puro = codigo_final[inicio:fim].strip()
    #.replace("\\n", "\n")
    #codigo_puro_edit = codigo_puro.replace('\"', '"')
    #codigo_puro_final = codigo_puro_edit.replace("\'", "'")
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



if __name__ == "__main__":
    
    #coletar_deputados()
    #distribuicao = gerar_grafico_distribuicao()
    #gerar_insights_gemini(distribuicao)
    #coletar_despesas_deputados()
    gerar_analise_gemini()