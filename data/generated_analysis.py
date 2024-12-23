
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def ler_parquet(parquet_file):
    """Lê um arquivo Parquet e retorna um DataFrame Pandas.  Trata erros de arquivo não encontrado ou vazio."""
    try:
        df = pd.read_parquet(parquet_file)
        if df.empty:
            raise pd.errors.EmptyDataError("Arquivo Parquet está vazio.")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo Parquet '{parquet_file}' não encontrado.")
    except pd.errors.EmptyDataError as e:
        raise pd.errors.EmptyDataError(f"Erro: {e}")
    except Exception as e:
        raise Exception(f"Erro inesperado ao ler o arquivo Parquet: {e}")


def plotar_evolucao_temporal(df):
    """Gera um gráfico de linha mostrando a evolução temporal das despesas por tipo."""
    df['dataDocumento'] = pd.to_datetime(df['dataDocumento'])
    df_temp = df.groupby([pd.Grouper(key='dataDocumento', freq='M'), 'tipoDespesa'])['total_despesas'].sum().reset_index()
    plt.figure(figsize=(15, 6))
    sns.lineplot(data=df_temp, x='dataDocumento', y='total_despesas', hue='tipoDespesa')
    plt.title('Evolução Temporal das Despesas por Tipo')
    plt.xlabel('Data')
    plt.ylabel('Total de Despesas')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plotar_ranking_fornecedores(df, delimitador=';'):
    """Gera um gráfico de barras mostrando o ranking dos fornecedores com maiores gastos."""
    try:
        df['fornecedores'] = df['fornecedores'].str.split(delimitador)
        df_explodido = df.explode('fornecedores')
        df_fornecedores = df_explodido.groupby('fornecedores')['total_despesas'].sum().reset_index().sort_values(by='total_despesas', ascending=False)

        plt.figure(figsize=(12, 6))
        sns.barplot(data=df_fornecedores.head(10), x='fornecedores', y='total_despesas')
        plt.title('Top 10 Fornecedores com Maiores Gastos')
        plt.xlabel('Fornecedor')
        plt.ylabel('Total de Despesas')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
        print("Top 10 Fornecedores (Tabela):\
", df_fornecedores.head(10))
    except KeyError as e:
        raise KeyError(f"Coluna '{e.args[0]}' não encontrada no DataFrame.")
    except Exception as e:
        raise Exception(f"Erro inesperado ao processar dados de fornecedores: {e}")


def plotar_distribuicao_despesas(df):
    """Gera um boxplot mostrando a distribuição das despesas por tipo e outliers."""
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='tipoDespesa', y='total_despesas', data=df)
    plt.title('Distribuição das Despesas por Tipo e Outliers')
    plt.xlabel('Tipo de Despesa')
    plt.ylabel('Total de Despesas')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()


def analisar_despesas(parquet_file, delimitador_fornecedores=';'):
    """Analisa um arquivo Parquet contendo dados de despesas e gera gráficos."""
    try:
        df = ler_parquet(parquet_file)
        plotar_evolucao_temporal(df)
        plotar_ranking_fornecedores(df, delimitador_fornecedores)
        plotar_distribuicao_despesas(df)
    except (FileNotFoundError, pd.errors.EmptyDataError, KeyError, Exception) as e:
        print(f"Erro: {e}")


# Exemplo de uso:
# Substitua 'seu_arquivo.parquet' pelo caminho do seu arquivo.  
# Ajuste o delimitador se necessário.
analisar_despesas('data/serie_despesas_diarias_deputados.parquet', delimitador_fornecedores=',') #Exemplo usando vírgula como delimitador.
