from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from joblib import dump, load

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - fallback when dependency is unavailable
    genai = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSISTANT_INDEX_PATH = DATA_DIR / "assistente_faiss.index"
ASSISTANT_META_PATH = DATA_DIR / "assistente_faiss_docs.json"
ASSISTANT_VECTORIZER_PATH = DATA_DIR / "assistente_faiss_vectorizer.joblib"


@dataclass
class AssistantKnowledgeBase:
    documents: list[dict[str, Any]]
    vectorizer: TfidfVectorizer
    index: faiss.Index


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


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
        if not filtrado.empty:
            colunas = [col for col in ["id", "ementa", "tema", "dataApresentacao"] if col in filtrado.columns]
            for _, linha in filtrado.head(5).iterrows():
                partes = []
                for coluna in colunas:
                    valor = linha[coluna]
                    if pd.isna(valor):
                        continue
                    partes.append(f"{coluna}: {valor}")
                resumo_textual.append(" | ".join(partes))
        else:
            resumo_textual.append("Sem registros suficientes para esse tema na base atual.")

        texto = f"Tema {tema}. " + " || ".join(resumo_textual)
        documentos.append(
            _doc(
                f"proposicoes_{tema.lower().replace(' ', '_')}",
                f"Proposições sobre {tema}",
                texto,
                "data/proposicoes_deputados.parquet",
                {"tema": tema, "quantidade": int(len(filtrado))},
            )
        )

    if sumarizacoes:
        documentos.append(
            _doc(
                "sumarizacoes_gerais",
                "Sumarizações de proposições",
                " ".join(sumarizacoes[:10]),
                "data/sumarizacao_proposicoes.json",
                {"quantidade_resumos": len(sumarizacoes)},
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


def _vectorizar_documentos(documentos: list[dict[str, Any]], vectorizer: TfidfVectorizer | None = None) -> tuple[TfidfVectorizer, np.ndarray]:
    textos = [f"{doc['title']}. {doc['text']}" for doc in documentos]
    if vectorizer is None:
        vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)
        matriz = vectorizer.fit_transform(textos)
    else:
        matriz = vectorizer.transform(textos)
    matriz = normalize(matriz, norm="l2", axis=1)
    return vectorizer, matriz.astype(np.float32).toarray()


@st.cache_resource(show_spinner=False)
def build_knowledge_base(base_dir: str | None = None) -> AssistantKnowledgeBase:
    base_path = Path(base_dir) if base_dir else BASE_DIR
    documentos = montar_documentos(base_path)
    if not documentos:
        raise FileNotFoundError("Nenhum documento disponível para o assistente.")

    if ASSISTANT_INDEX_PATH.exists() and ASSISTANT_META_PATH.exists() and ASSISTANT_VECTORIZER_PATH.exists() and base_path == BASE_DIR:
        vectorizer = load(ASSISTANT_VECTORIZER_PATH)
        documentos = _read_json(ASSISTANT_META_PATH, [])
        index = faiss.read_index(str(ASSISTANT_INDEX_PATH))
        return AssistantKnowledgeBase(documents=documentos, vectorizer=vectorizer, index=index)

    vectorizer, embeddings = _vectorizar_documentos(documentos)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    if base_path == BASE_DIR:
        base_path.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(ASSISTANT_INDEX_PATH))
        _save_json(ASSISTANT_META_PATH, documentos)
        dump(vectorizer, ASSISTANT_VECTORIZER_PATH)

    return AssistantKnowledgeBase(documents=documentos, vectorizer=vectorizer, index=index)


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

    if not subperguntas:
        subperguntas.append(pergunta.strip())

    return list(dict.fromkeys(subperguntas))


def buscar_contexto(pergunta: str, kb: AssistantKnowledgeBase, top_k: int = 3) -> list[dict[str, Any]]:
    query_vec = kb.vectorizer.transform([pergunta])
    query_vec = normalize(query_vec, norm="l2", axis=1).astype(np.float32).toarray()
    scores, indices = kb.index.search(query_vec, top_k)
    resultados = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(kb.documents):
            continue
        doc = kb.documents[idx]
        resultados.append({"score": float(score), **doc})
    return resultados


def _resposta_rules_based(pergunta: str, contexto: list[dict[str, Any]], kb: AssistantKnowledgeBase) -> str:
    pergunta_norm = pergunta.lower()

    for doc in contexto:
        metadata = doc.get("metadata", {})
        if "partido" in pergunta_norm and metadata.get("tipo") == "partidos":
            top = metadata.get("top_partidos", {})
            if top:
                partido_top = max(top.items(), key=lambda item: item[1])
                return f"O partido com mais deputados, na base atual, é {partido_top[0]} com {partido_top[1]} parlamentares."

        if ("tipo de despesa" in pergunta_norm or "despesa mais" in pergunta_norm) and metadata.get("top_tipo"):
            return f"O tipo de despesa mais declarado é {metadata['top_tipo']}, com R$ {metadata['top_valor']:,.2f}."

        if "economia" in pergunta_norm and metadata.get("tema") == "Economia":
            return doc["text"]

        if ("ciência" in pergunta_norm or "tecnologia" in pergunta_norm or "inovação" in pergunta_norm) and metadata.get("tema") == "Ciência, Tecnologia e Inovação":
            return doc["text"]

        if "despesas" in pergunta_norm and metadata.get("top_deputados"):
            top = metadata.get("top_deputados", {})
            deputado_top = max(top.items(), key=lambda item: item[1])
            return f"O deputado com mais despesas na base detalhada é {deputado_top[0]} com R$ {deputado_top[1]:,.2f}."

    if "deputado com mais despesas" in pergunta_norm:
        return "A base atual não possui o detalhamento por deputado. Para responder com precisão, gere data/despesas_deputados_detalhadas.parquet na coleta atualizada."

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


def render_assistant_tab(base_dir: str | None = None) -> None:
    st.title("🤖 Assistente Legislativo")
    st.caption("Busca semântica com FAISS e respostas guiadas por Self-Ask.")

    if st.button("Recriar índice FAISS", type="secondary"):
        build_knowledge_base(base_dir)
        st.success("Índice reconstruído com sucesso.")

    pergunta = st.text_area(
        "Digite sua pergunta",
        value="Quais são as informações mais relevantes sobre as proposições que falam de Economia?",
        height=120,
    )

    if st.button("Responder", type="primary"):
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
