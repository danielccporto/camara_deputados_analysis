
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


def _normalizar_coluna_fornecedor(df: pd.DataFrame) -> pd.Series:
    coluna_fornecedor = 'fornecedor' if 'fornecedor' in df.columns else 'fornecedores'
    fornecedores = df[coluna_fornecedor]

    def extrair_nome(valor):
        if isinstance(valor, (list, tuple, pd.Series)):
            return valor[0] if len(valor) > 0 else None
        if hasattr(valor, 'tolist') and not isinstance(valor, str):
            convertido = valor.tolist()
            if isinstance(convertido, list):
                return convertido[0] if convertido else None
            return convertido
        return valor

    return fornecedores.apply(extrair_nome)

def carregar_dados(caminho_parquet: str) -> pd.DataFrame:
    """Carrega os dados de um arquivo Parquet e trata possíveis erros.

    Args:
        caminho_parquet (str): Caminho para o arquivo Parquet.

    Returns:
        pd.DataFrame: DataFrame com os dados, ou None caso ocorra erro.
    """
    try:
        df = pd.read_parquet(caminho_parquet)
        if df.empty:
            raise pd.errors.EmptyDataError("Arquivo Parquet está vazio.")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo Parquet não encontrado em {caminho_parquet}")
        return None
    except pd.errors.EmptyDataError as e:
        print(f"Erro: {e}")
        return None
    except Exception as e:
        print(f"Erro ao ler o arquivo Parquet: {e}")
        return None

def analisar_evolucao_temporal(df: pd.DataFrame) -> plt.Figure:
    """Analisa a evolução temporal das despesas por tipo.

    Args:
        df (pd.DataFrame): DataFrame com os dados.

    Returns:
        plt.Figure: Figura com o gráfico.
    """
    df['dataDocumento'] = pd.to_datetime(df['dataDocumento'])
    df_tempo = df.groupby(['dataDocumento', 'tipoDespesa'])['total_despesas'].sum().reset_index()
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=df_tempo, x='dataDocumento', y='total_despesas', hue='tipoDespesa', ax=ax)
    ax.set_title('Evolução Temporal das Despesas por Tipo')
    ax.set_xlabel('Data')
    ax.set_ylabel('Total de Despesas')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    return fig


def analisar_distribuicao_fornecedores(df: pd.DataFrame) -> plt.Figure:
    """Analisa a distribuição das despesas por fornecedor.

    Args:
        df (pd.DataFrame): DataFrame com os dados.

    Returns:
        plt.Figure: Figura com o gráfico.
    """
    coluna_fornecedor = _normalizar_coluna_fornecedor(df)
    df_fornecedor = df.assign(fornecedor_normalizado=coluna_fornecedor).groupby('fornecedor_normalizado')['total_despesas'].sum().reset_index()
    df_fornecedor = df_fornecedor.sort_values(by='total_despesas', ascending=False).head(20)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=df_fornecedor, x='fornecedor_normalizado', y='total_despesas', ax=ax)
    ax.set_title('Distribuição das Despesas por Fornecedor (Top 20)')
    ax.set_xlabel('Fornecedor')
    ax.set_ylabel('Total de Despesas')
    ax.tick_params(axis='x', rotation=90)
    plt.tight_layout()
    return fig


def analisar_correlacao_tipos_despesa(df: pd.DataFrame) -> plt.Figure:
    """Analisa a correlação entre tipos de despesa (simplificado).

    Args:
        df (pd.DataFrame): DataFrame com os dados.

    Returns:
        plt.Figure: Figura com o gráfico.
    """
    df['dataDocumento'] = pd.to_datetime(df['dataDocumento'])
    df_correlacao = df.pivot_table(
        index='dataDocumento',
        columns='tipoDespesa',
        values='total_despesas',
        aggfunc='sum',
        fill_value=0,
    )
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(df_correlacao.corr(), annot=True, cmap='coolwarm', fmt=".2f", ax=ax)
    ax.set_title('Matriz de Correlação entre Tipos de Despesa (Simplificada)')
    return fig


def analisar_despesas_deputados(caminho_parquet: str) -> tuple:
    """Analisa dados de despesas de deputados e gera gráficos."""
    df = carregar_dados(caminho_parquet)
    if df is None:
        return None, None, None

    fig_tempo = analisar_evolucao_temporal(df)
    fig_fornecedor = analisar_distribuicao_fornecedores(df)
    fig_correlacao = analisar_correlacao_tipos_despesa(df)

    return fig_tempo, fig_fornecedor, fig_correlacao
if __name__ == "__main__":
    fig_tempo, fig_fornecedor, fig_correlacao = analisar_despesas_deputados("data/serie_despesas_diarias_deputados.parquet")

    if fig_tempo:
        fig_tempo.show()
    if fig_fornecedor:
        fig_fornecedor.show()
    if fig_correlacao:
        fig_correlacao.show()

