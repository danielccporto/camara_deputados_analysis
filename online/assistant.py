from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Evita crash no Windows por runtimes OpenMP duplicados (faiss/torch).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import faiss
import numpy as np
import pandas as pd
import streamlit as st
import torch
from transformers import AutoModel, AutoTokenizer

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - fallback when dependency is unavailable
    genai = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSISTANT_INDEX_PATH = DATA_DIR / "assistente_faiss.index"
ASSISTANT_META_PATH = DATA_DIR / "assistente_faiss_docs.json"
BERT_EMBEDDING_MODEL = "neuralmind/bert-base-portuguese-cased"
BERT_EMBEDDING_DIM = 768
ASSISTANT_SCHEMA_VERSION = 2


@dataclass
class AssistantKnowledgeBase:
    documents: list[dict[str, Any]]
    index: faiss.Index
    embedding_model: str


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _documents_require_rebuild(documentos: list[dict[str, Any]], require_despesas_deputado_doc: bool) -> bool:
    if not documentos:
        return True

    encontrou_doc_proposicoes = False
    encontrou_doc_despesas_deputado = False

    for doc in documentos:
        metadata = doc.get("metadata", {}) or {}
        doc_id = str(doc.get("id", ""))

        if doc_id.startswith("proposicoes_"):
            encontrou_doc_proposicoes = True
            if not metadata.get("proposicoes"):
                return True

        if doc_id == "despesas_deputados":
            encontrou_doc_despesas_deputado = True
            if not metadata.get("top_deputados"):
                return True

    if require_despesas_deputado_doc:
        return not (encontrou_doc_proposicoes and encontrou_doc_despesas_deputado)
    return not encontrou_doc_proposicoes


def _normalizar_fornecedores(valor: Any) -> str:
    if isinstance(valor, (list, tuple)):
        itens = []
        for item in valor:
            if item is None:
                continue
            if isinstance(item, (list, tuple)) and item:
                itens.append(str(item[0]))
            else:
                itens.append(str(item))
        return ", ".join(sorted(set(itens)))
    if hasattr(valor, "tolist") and not isinstance(valor, str):
        convertido = valor.tolist()
        if isinstance(convertido, list):
            return _normalizar_fornecedores(convertido)
        return str(convertido)
    return "" if valor is None else str(valor)


def _texto_curto(texto: str, limite: int = 1200) -> str:
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= limite else texto[: limite - 3] + "..."


def _texto_breve(texto: str, limite: int = 180) -> str:
    texto = " ".join(str(texto).split())
    return texto if len(texto) <= limite else texto[: limite - 3] + "..."


def _carregar_deputados(data_dir: Path) -> pd.DataFrame:
    caminho = data_dir / "deputados.parquet"
    if not caminho.exists():
        return pd.DataFrame()
    return pd.read_parquet(caminho)


def _carregar_despesas_agregadas(data_dir: Path) -> pd.DataFrame:
    caminho = data_dir / "serie_despesas_diarias_deputados.parquet"
    if not caminho.exists():
        return pd.DataFrame()
    df = pd.read_parquet(caminho)
    if "dataDocumento" in df.columns:
        df["dataDocumento"] = pd.to_datetime(df["dataDocumento"], errors="coerce")
    return df


def _carregar_despesas_detalhadas(data_dir: Path) -> pd.DataFrame:
    caminho = data_dir / "despesas_deputados_detalhadas.parquet"
    if not caminho.exists():
        return pd.DataFrame()
    df = pd.read_parquet(caminho)
    if "dataDocumento" in df.columns:
        df["dataDocumento"] = pd.to_datetime(df["dataDocumento"], errors="coerce")
    return df


def _carregar_proposicoes(data_dir: Path) -> pd.DataFrame:
    caminho = data_dir / "proposicoes_deputados.parquet"
    if not caminho.exists():
        return pd.DataFrame()
    df = pd.read_parquet(caminho)
    if "dataApresentacao" in df.columns:
        df["dataApresentacao"] = pd.to_datetime(df["dataApresentacao"], errors="coerce")
    return df


def _carregar_sumarizacoes(data_dir: Path) -> list[str]:
    caminho = data_dir / "sumarizacao_proposicoes.json"
    dados = _read_json(caminho, {})
    resumoss = dados.get("resumos", [])
    return [str(item) for item in resumoss if str(item).strip()]


def _doc(doc_id: str, title: str, text: str, source: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": doc_id,
        "title": title,
        "text": _texto_curto(text),
        "source": source,
        "metadata": metadata or {},
    }


def _build_party_document(df_deputados: pd.DataFrame) -> dict[str, Any] | None:
    if df_deputados.empty or "siglaPartido" not in df_deputados.columns:
        return None
    distribuicao = df_deputados["siglaPartido"].value_counts().head(10)
    partes = [f"{partido}: {quantidade} deputados" for partido, quantidade in distribuicao.items()]
    texto = "Distribuição de deputados por partido. " + "; ".join(partes)
    return _doc(
        "deputados_partidos",
        "Partidos com mais deputados",
        texto,
        "data/deputados.parquet",
        {"tipo": "partidos", "top_partidos": distribuicao.to_dict()},
    )


def _build_expense_documents(df_despesas: pd.DataFrame, df_detalhadas: pd.DataFrame) -> list[dict[str, Any]]:
    documentos: list[dict[str, Any]] = []
    if df_despesas.empty:
        return documentos

    total_gasto = float(df_despesas["total_despesas"].sum()) if "total_despesas" in df_despesas.columns else 0.0

    if "tipoDespesa" in df_despesas.columns and "total_despesas" in df_despesas.columns:
        por_tipo = df_despesas.groupby("tipoDespesa", dropna=False)["total_despesas"].sum().sort_values(ascending=False)
        tipo_top = por_tipo.index[0]
        texto = f"Total gasto agregado de R$ {total_gasto:,.2f}. O tipo de despesa mais declarado é {tipo_top} com R$ {por_tipo.iloc[0]:,.2f}."
        documentos.append(
            _doc(
                "despesas_tipo",
                "Tipo de despesa mais declarado",
                texto,
                "data/serie_despesas_diarias_deputados.parquet",
                {"total_gasto": total_gasto, "top_tipo": str(tipo_top), "top_valor": float(por_tipo.iloc[0])},
            )
        )

    if "fornecedores" in df_despesas.columns and "total_despesas" in df_despesas.columns:
        fornecedores = df_despesas["fornecedores"].apply(_normalizar_fornecedores)
        df_fornecedores = df_despesas.assign(fornecedor_normalizado=fornecedores)
        top_fornecedores = (
            df_fornecedores.groupby("fornecedor_normalizado", dropna=False)["total_despesas"].sum().sort_values(ascending=False).head(5)
        )
        texto = "Fornecedores mais recorrentes nas despesas agregadas: " + "; ".join(
            f"{fornecedor}: R$ {valor:,.2f}" for fornecedor, valor in top_fornecedores.items()
        )
        documentos.append(
            _doc(
                "despesas_fornecedores",
                "Fornecedores recorrentes",
                texto,
                "data/serie_despesas_diarias_deputados.parquet",
                {"top_fornecedores": {str(k): float(v) for k, v in top_fornecedores.items()}},
            )
        )

    if not df_detalhadas.empty and {"nomeDeputado", "total_despesas"}.issubset(df_detalhadas.columns):
        top_deputados = (
            df_detalhadas.groupby("nomeDeputado", dropna=False)["total_despesas"].sum().sort_values(ascending=False).head(5)
        )
        texto = "Deputados com mais despesas na base detalhada: " + "; ".join(
            f"{deputado}: R$ {valor:,.2f}" for deputado, valor in top_deputados.items()
        )
        documentos.append(
            _doc(
                "despesas_deputados",
                "Deputado com mais despesas",
                texto,
                "data/despesas_deputados_detalhadas.parquet",
                {"top_deputados": {str(k): float(v) for k, v in top_deputados.items()}},
            )
        )
    elif {"nomeDeputado", "total_despesas"}.issubset(df_despesas.columns):
        top_deputados = (
            df_despesas.groupby("nomeDeputado", dropna=False)["total_despesas"].sum().sort_values(ascending=False).head(5)
        )
        texto = "Deputados com mais despesas na base atual: " + "; ".join(
            f"{deputado}: R$ {valor:,.2f}" for deputado, valor in top_deputados.items()
        )
        documentos.append(
            _doc(
                "despesas_deputados",
                "Deputado com mais despesas",
                texto,
                "data/serie_despesas_diarias_deputados.parquet",
                {"top_deputados": {str(k): float(v) for k, v in top_deputados.items()}},
            )
        )

    return documentos


def _build_proposition_documents(df_proposicoes: pd.DataFrame, sumarizacoes: list[str]) -> list[dict[str, Any]]:
    documentos: list[dict[str, Any]] = []
    if df_proposicoes.empty:
        return documentos

    temas_alvo = {
        "Economia": ["economia", "fiscal", "tribut", "financeir", "banc", "mercado"],
        "Ciência, Tecnologia e Inovação": ["ciência", "tecnologia", "inovação", "software", "pesquisa", "telecom", "comput"],
    }

    for tema, palavras in temas_alvo.items():
        if "tema" in df_proposicoes.columns:
            mascara_tema = df_proposicoes["tema"].astype(str).str.contains(tema, case=False, na=False)
        else:
            mascara_tema = pd.Series([False] * len(df_proposicoes), index=df_proposicoes.index)

        if "ementa" in df_proposicoes.columns:
            mascara_texto = df_proposicoes["ementa"].astype(str).str.contains("|".join(palavras), case=False, na=False, regex=True)
        else:
            mascara_texto = pd.Series([False] * len(df_proposicoes), index=df_proposicoes.index)

        filtrado = df_proposicoes[mascara_tema | mascara_texto].copy()
        resumo_textual = []
        itens_struct: list[dict[str, Any]] = []
        if not filtrado.empty:
            colunas = [col for col in ["id", "ementa", "tema", "dataApresentacao"] if col in filtrado.columns]
            for _, linha in filtrado.head(5).iterrows():
                partes = []
                item_meta: dict[str, Any] = {}
                for coluna in colunas:
                    valor = linha[coluna]
                    if pd.isna(valor):
                        continue
                    partes.append(f"{coluna}: {valor}")
                    item_meta[coluna] = str(valor)
                resumo_textual.append(" | ".join(partes))
                if item_meta:
                    itens_struct.append(item_meta)
        else:
            resumo_textual.append("Sem registros suficientes para esse tema na base atual.")

        texto = f"Tema {tema}. Foram encontradas {len(filtrado)} proposições relevantes na base local."
        documentos.append(
            _doc(
                f"proposicoes_{tema.lower().replace(' ', '_')}",
                f"Proposições sobre {tema}",
                texto,
                "data/proposicoes_deputados.parquet",
                {"tema": tema, "quantidade": int(len(filtrado)), "proposicoes": itens_struct, "resumo_textual": resumo_textual},
            )
        )

    if sumarizacoes:
        resumos_curtos = [_texto_breve(item, limite=220) for item in sumarizacoes[:5]]
        documentos.append(
            _doc(
                "sumarizacoes_gerais",
                "Sumarizações de proposições",
                "Resumo consolidado das proposições da base local.",
                "data/sumarizacao_proposicoes.json",
                {"quantidade_resumos": len(sumarizacoes), "resumos_curtos": resumos_curtos},
            )
        )

    return documentos


def montar_documentos(base_dir: Path | None = None) -> list[dict[str, Any]]:
    base_dir = base_dir or BASE_DIR
    data_dir = base_dir / "data"

    df_deputados = _carregar_deputados(data_dir)
    df_despesas = _carregar_despesas_agregadas(data_dir)
    df_detalhadas = _carregar_despesas_detalhadas(data_dir)
    df_proposicoes = _carregar_proposicoes(data_dir)
    sumarizacoes = _carregar_sumarizacoes(data_dir)

    documentos: list[dict[str, Any]] = []

    doc_partidos = _build_party_document(df_deputados)
    if doc_partidos:
        documentos.append(doc_partidos)

    documentos.extend(_build_expense_documents(df_despesas, df_detalhadas))
    documentos.extend(_build_proposition_documents(df_proposicoes, sumarizacoes))

    return documentos


@st.cache_resource(show_spinner=False)
def _load_embedding_model(model_name: str = BERT_EMBEDDING_MODEL) -> tuple[AutoTokenizer, AutoModel, str]:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    return tokenizer, model, device


def _embed_texts(textos: list[str], model_name: str = BERT_EMBEDDING_MODEL, batch_size: int = 16) -> np.ndarray:
    tokenizer, model, device = _load_embedding_model(model_name)
    batches = []

    for i in range(0, len(textos), batch_size):
        trecho = textos[i : i + batch_size]
        entradas = tokenizer(
            trecho,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
        )
        entradas = {k: v.to(device) for k, v in entradas.items()}

        with torch.no_grad():
            saidas = model(**entradas)
            hidden = saidas.last_hidden_state
            mascara = entradas["attention_mask"].unsqueeze(-1)
            soma = (hidden * mascara).sum(dim=1)
            divisao = mascara.sum(dim=1).clamp(min=1)
            embeddings = soma / divisao
        batches.append(embeddings.cpu().numpy().astype(np.float32))

    matriz = np.vstack(batches)
    faiss.normalize_L2(matriz)
    return matriz


@st.cache_resource(show_spinner=False)
def build_knowledge_base(base_dir: str | None = None) -> AssistantKnowledgeBase:
    base_path = Path(base_dir) if base_dir else BASE_DIR
    require_despesas_deputado_doc = (base_path / "data" / "despesas_deputados_detalhadas.parquet").exists()
    documentos = montar_documentos(base_path)
    if not documentos:
        raise FileNotFoundError("Nenhum documento disponível para o assistente.")

    if ASSISTANT_INDEX_PATH.exists() and ASSISTANT_META_PATH.exists() and base_path == BASE_DIR:
        dados_meta = _read_json(ASSISTANT_META_PATH, {})
        if isinstance(dados_meta, dict):
            documentos = dados_meta.get("documents", [])
            embedding_model = dados_meta.get("embedding_model", BERT_EMBEDDING_MODEL)
            schema_version = int(dados_meta.get("schema_version", 0))
        else:
            documentos = dados_meta
            embedding_model = BERT_EMBEDDING_MODEL
            schema_version = 0
        index = faiss.read_index(str(ASSISTANT_INDEX_PATH))

        # Se existir índice antigo (ex.: TF-IDF) ou dimensão incompatível, força rebuild.
        if (
            embedding_model == BERT_EMBEDDING_MODEL
            and index.d == BERT_EMBEDDING_DIM
            and schema_version >= ASSISTANT_SCHEMA_VERSION
            and not _documents_require_rebuild(documentos, require_despesas_deputado_doc=require_despesas_deputado_doc)
        ):
            return AssistantKnowledgeBase(documents=documentos, index=index, embedding_model=embedding_model)

    textos = [f"{doc['title']}. {doc['text']}" for doc in documentos]
    embeddings = _embed_texts(textos, model_name=BERT_EMBEDDING_MODEL)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    if base_path == BASE_DIR:
        base_path.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(ASSISTANT_INDEX_PATH))
        _save_json(
            ASSISTANT_META_PATH,
            {
                "schema_version": ASSISTANT_SCHEMA_VERSION,
                "embedding_model": BERT_EMBEDDING_MODEL,
                "documents": documentos,
            },
        )

    return AssistantKnowledgeBase(documents=documentos, index=index, embedding_model=BERT_EMBEDDING_MODEL)


def decompor_pergunta(pergunta: str) -> list[str]:
    pergunta_norm = pergunta.lower()
    subperguntas: list[str] = []

    if "partido" in pergunta_norm and "deput" in pergunta_norm:
        subperguntas.append("Qual partido político tem mais deputados na Câmara?")
    if "mais desp" in pergunta_norm or "despesas" in pergunta_norm:
        subperguntas.append("Qual deputado tem mais despesas na Câmara?")
    if "tipo de despesa" in pergunta_norm or "despesa mais" in pergunta_norm:
        subperguntas.append("Qual é o tipo de despesa mais declarada pelos deputados?")
    if "economia" in pergunta_norm:
        subperguntas.append("Quais são as informações mais relevantes sobre as proposições que falam de Economia?")
    if "ciência" in pergunta_norm or "tecnologia" in pergunta_norm or "inovação" in pergunta_norm:
        subperguntas.append("Quais são as informações mais relevantes sobre as proposições que falam de Ciência, Tecnologia e Inovação?")
    if "self-ask" in pergunta_norm or "self ask" in pergunta_norm or "técnica" in pergunta_norm:
        subperguntas.append("Como a técnica Self-Ask funciona neste assistente da Câmara dos Deputados?")

    if not subperguntas:
        subperguntas.append(pergunta.strip())

    return list(dict.fromkeys(subperguntas))


def buscar_contexto(pergunta: str, kb: AssistantKnowledgeBase, top_k: int = 3) -> list[dict[str, Any]]:
    query_vec = _embed_texts([pergunta], model_name=kb.embedding_model)
    scores, indices = kb.index.search(query_vec, top_k)
    resultados = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(kb.documents):
            continue
        doc = kb.documents[idx]
        resultados.append({"score": float(score), **doc})
    return resultados


def _sintetizar_tema_proposicoes(metadata: dict[str, Any], tema: str) -> str:
    itens = metadata.get("proposicoes", [])
    quantidade = metadata.get("quantidade", len(itens))
    if not itens:
        return f"Para {tema}, não há proposições suficientes na base local atual."

    linhas = [f"Foram encontradas {quantidade} proposições relevantes sobre {tema} na base atual."]
    linhas.append("Principais pontos identificados:")
    for idx, item in enumerate(itens[:3], start=1):
        id_prop = item.get("id", "s/ id")
        ementa = _texto_breve(item.get("ementa", "Sem ementa"), limite=220)
        tema_item = item.get("tema", tema)
        linhas.append(f"{idx}. PL/Proposição {id_prop} ({tema_item}): {ementa}")

    return "\n".join(linhas)


def _compute_top_deputado_on_demand() -> str:
    # Tenta calcular o deputado com mais despesas a partir dos arquivos disponíveis
    df_det = _carregar_despesas_detalhadas(DATA_DIR)
    if not df_det.empty and {"nomeDeputado", "total_despesas"}.issubset(df_det.columns):
        top = df_det.groupby("nomeDeputado", dropna=False)["total_despesas"].sum().sort_values(ascending=False)
        if not top.empty:
            nome, valor = top.index[0], float(top.iloc[0])
            return f"O deputado com mais despesas na base detalhada é {nome} com R$ {valor:,.2f}."

    df_agg = _carregar_despesas_agregadas(DATA_DIR)
    # tentar colunas alternativas de nome
    nome_cols = [c for c in ("nomeDeputado", "nomeParlamentar", "nome", "deputado") if c in df_agg.columns]
    if not df_agg.empty and nome_cols and "total_despesas" in df_agg.columns:
        col = nome_cols[0]
        top = df_agg.groupby(col, dropna=False)["total_despesas"].sum().sort_values(ascending=False)
        if not top.empty:
            nome, valor = top.index[0], float(top.iloc[0])
            return f"O deputado com mais despesas na base disponível é {nome} com R$ {valor:,.2f}."

    return "A base atual não possui o detalhamento por deputado. Para responder com precisão, gere data/despesas_deputados_detalhadas.parquet na coleta atualizada."


def _compute_proposicoes_on_demand(tema: str) -> str:
    df = _carregar_proposicoes(DATA_DIR)
    if df.empty:
        return f"Para {tema}, não há proposições suficientes na base local atual."

    palavras_map = {
        "Economia": ["economia", "fiscal", "tribut", "financeir", "banc", "mercado"],
        "Ciência, Tecnologia e Inovação": ["ciência", "tecnologia", "inovação", "software", "pesquisa", "telecom", "comput"],
    }
    palavras = palavras_map.get(tema, [tema.lower()])

    if "tema" in df.columns:
        mask_tema = df["tema"].astype(str).str.contains(tema, case=False, na=False)
    else:
        mask_tema = pd.Series([False] * len(df), index=df.index)

    if "ementa" in df.columns:
        mask_text = df["ementa"].astype(str).str.contains("|".join(palavras), case=False, na=False, regex=True)
    else:
        mask_text = pd.Series([False] * len(df), index=df.index)

    filtrado = df[mask_tema | mask_text].copy()
    if filtrado.empty:
        return f"Para {tema}, não há proposições suficientes na base local atual."

    linhas = [f"Foram encontradas {len(filtrado)} proposições relevantes sobre {tema} na base local."]
    linhas.append("Principais proposições encontradas:")
    colunas = [col for col in ["id", "ementa", "tema", "dataApresentacao"] if col in filtrado.columns]

    # Escolher coluna de data disponível para ordenação, se houver
    sort_candidates = ["dataApresentacao", "data_apresentacao", "dataApresentacao_iso", "data"]
    sort_col = next((c for c in sort_candidates if c in filtrado.columns), None)
    if sort_col:
        try:
            filtrado[sort_col] = pd.to_datetime(filtrado[sort_col], errors="coerce")
        except Exception:
            pass
        ordered = filtrado.sort_values(sort_col, ascending=False)
    else:
        ordered = filtrado

    for idx, (_, row) in enumerate(ordered.head(5).iterrows(), start=1):
        partes = []
        for col in colunas:
            val = row.get(col)
            if pd.isna(val):
                continue
            partes.append(f"{col}: {_texto_breve(val, limite=140)}")
        linhas.append(f"{idx}. " + " | ".join(partes))

    return "\n".join(linhas)


def _explicar_self_ask() -> str:
    return (
        "A técnica Self-Ask é usada aqui em três etapas: "
        "(1) decompomos a pergunta em subperguntas objetivas (partido, deputado, tipo de despesa, tema de proposição), "
        "(2) recuperamos contexto na base vetorial FAISS usando embeddings BERT em português, "
        "e (3) sintetizamos a resposta final apenas com evidências da base local, informando quando dados faltam."
    )


def _resposta_rules_based(pergunta: str, contexto: list[dict[str, Any]], kb: AssistantKnowledgeBase) -> str:
    pergunta_norm = pergunta.lower()

    if "self-ask" in pergunta_norm or "self ask" in pergunta_norm or "técnica" in pergunta_norm:
        return _explicar_self_ask()

    for doc in contexto:
        metadata = doc.get("metadata", {})
        if "partido" in pergunta_norm and metadata.get("tipo") == "partidos":
            top = metadata.get("top_partidos", {})
            if top:
                partido_top = max(top.items(), key=lambda item: item[1])
                return f"O partido com mais deputados, na base atual, é {partido_top[0]} com {partido_top[1]} parlamentares."

        if ("tipo de despesa" in pergunta_norm or "despesa mais" in pergunta_norm) and metadata.get("top_tipo"):
            return f"O tipo de despesa mais declarado é {metadata['top_tipo']}, com R$ {metadata['top_valor']:,.2f}."
        if ("tipo de despesa" in pergunta_norm or "despesa mais" in pergunta_norm):
            if metadata.get("top_tipo"):
                return f"O tipo de despesa mais declarado é {metadata['top_tipo']}, com R$ {metadata['top_valor']:,.2f}."
            # tentativa on-demand
            df_agg_local = _carregar_despesas_agregadas(DATA_DIR)
            if not df_agg_local.empty and 'tipoDespesa' in df_agg_local.columns and 'total_despesas' in df_agg_local.columns:
                por_tipo = df_agg_local.groupby('tipoDespesa', dropna=False)['total_despesas'].sum().sort_values(ascending=False)
                if not por_tipo.empty:
                    top_tipo = por_tipo.index[0]
                    return f"O tipo de despesa mais declarado é {top_tipo}, com R$ {float(por_tipo.iloc[0]):,.2f}."
        if "economia" in pergunta_norm and metadata.get("tema") == "Economia":
            if metadata.get('proposicoes'):
                return _sintetizar_tema_proposicoes(metadata, "Economia")
            # tentar on-demand
            return _compute_proposicoes_on_demand("Economia")

        if ("ciência" in pergunta_norm or "tecnologia" in pergunta_norm or "inovação" in pergunta_norm) and metadata.get("tema") == "Ciência, Tecnologia e Inovação":
            if metadata.get('proposicoes'):
                return _sintetizar_tema_proposicoes(metadata, "Ciência, Tecnologia e Inovação")
            return _compute_proposicoes_on_demand("Ciência, Tecnologia e Inovação")

        if "despesas" in pergunta_norm and metadata.get("top_deputados"):
            top = metadata.get("top_deputados", {})
            deputado_top = max(top.items(), key=lambda item: item[1])
            return f"O deputado com mais despesas na base detalhada é {deputado_top[0]} com R$ {deputado_top[1]:,.2f}."

    if "deputado com mais despesas" in pergunta_norm:
        return _compute_top_deputado_on_demand()

    if contexto:
        return contexto[0]["text"]

    return "Não encontrei contexto suficiente na base local para responder."


def responder_pergunta(pergunta: str, base_dir: str | None = None) -> dict[str, Any]:
    kb = build_knowledge_base(base_dir)
    subperguntas = decompor_pergunta(pergunta)
    contexto = buscar_contexto(pergunta, kb, top_k=4)
    contexto_texto = "\n\n".join(
        f"[{idx + 1}] {item['title']} | fonte: {item['source']} | score: {item['score']:.3f}\n{item['text']}"
        for idx, item in enumerate(contexto)
    )

    prompt = f"""
Você é um assistente analítico sobre a Câmara dos Deputados.

Use a técnica Self-Ask de forma interna:
1. Reescreva a pergunta em subperguntas.
2. Responda usando apenas o contexto fornecido.
3. Se faltarem dados na base local, diga isso explicitamente.
4. Responda em português, de forma objetiva.

Pergunta original: {pergunta}
Subperguntas: {subperguntas}

Contexto recuperado:
{contexto_texto}
""".strip()

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key and genai is not None:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            answer = getattr(response, "text", None) or _resposta_rules_based(pergunta, contexto, kb)
        except Exception:
            answer = _resposta_rules_based(pergunta, contexto, kb)
    else:
        answer = _resposta_rules_based(pergunta, contexto, kb)

    return {
        "question": pergunta,
        "subquestions": subperguntas,
        "answer": answer,
        "context": contexto,
        "prompt": prompt,
    }


def render_assistant_tab(base_dir: str | None = None, show_title: bool = True, key_prefix: str = "assistant") -> None:
    if show_title:
        st.title("🤖 Assistente Legislativo")
    else:
        st.subheader("🤖 Assistente Legislativo")

    st.caption(
        "Busca semântica com FAISS e embeddings do modelo neuralmind/bert-base-portuguese-cased. "
        "A resposta final usa a técnica Self-Ask."
    )

    with st.expander("Como o Self-Ask é aplicado neste contexto?"):
        st.write(_explicar_self_ask())

    if st.button("Recriar índice FAISS", type="secondary", key=f"{key_prefix}_rebuild"):
        build_knowledge_base.clear()
        build_knowledge_base(base_dir)
        st.success("Índice reconstruído com sucesso.")

    pergunta = st.text_area(
        "Digite sua pergunta",
        value="Quais são as informações mais relevantes sobre as proposições que falam de Economia?",
        height=120,
        key=f"{key_prefix}_question",
    )

    if st.button("Responder", type="primary", key=f"{key_prefix}_answer"):
        if not pergunta.strip():
            st.warning("Digite uma pergunta para continuar.")
            return

        resultado = responder_pergunta(pergunta, base_dir)

        st.subheader("Resposta")
        st.write(resultado["answer"])

        st.subheader("Subperguntas")
        for item in resultado["subquestions"]:
            st.markdown(f"- {item}")

        st.subheader("Contexto recuperado")
        if resultado["context"]:
            for item in resultado["context"]:
                with st.container():
                    st.markdown(f"**{item['title']}**")
                    st.caption(f"Fonte: {item['source']} | Score: {item['score']:.3f}")
                    st.write(item["text"])
        else:
            st.info("Nenhum contexto recuperado.")
