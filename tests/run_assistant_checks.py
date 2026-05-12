from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from online.assistant import build_knowledge_base, responder_pergunta


def _write_fixture(base_dir: Path) -> None:
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    deputados = pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "nome": ["Ana", "Bruno", "Carla", "Daniel"],
            "siglaPartido": ["PT", "PT", "PL", "PL"],
        }
    )
    deputados.to_parquet(data_dir / "deputados.parquet", index=False)

    despesas_agregadas = pd.DataFrame(
        {
            "dataDocumento": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "tipoDespesa": ["Locomoção", "Locomoção", "Divulgação"],
            "total_despesas": [100.0, 250.0, 80.0],
            "fornecedores": [["Fornecedor A"], ["Fornecedor B"], ["Fornecedor C"]],
        }
    )
    despesas_agregadas.to_parquet(data_dir / "serie_despesas_diarias_deputados.parquet", index=False)

    despesas_detalhadas = pd.DataFrame(
        {
            "idDeputado": [1, 1, 2, 2, 2],
            "nomeDeputado": ["Ana", "Ana", "Bruno", "Bruno", "Bruno"],
            "dataDocumento": ["2026-01-01", "2026-01-02", "2026-01-01", "2026-01-02", "2026-01-03"],
            "tipoDespesa": ["Locomoção", "Locomoção", "Divulgação", "Divulgação", "Divulgação"],
            "nomeFornecedor": ["Fornecedor A", "Fornecedor B", "Fornecedor C", "Fornecedor C", "Fornecedor D"],
            "total_despesas": [100.0, 250.0, 80.0, 200.0, 300.0],
        }
    )
    despesas_detalhadas.to_parquet(data_dir / "despesas_deputados_detalhadas.parquet", index=False)

    proposicoes = pd.DataFrame(
        {
            "id": [10, 11, 12],
            "ementa": [
                "Cria incentivos para pesquisa e inovação tecnológica.",
                "Institui medidas de apoio à economia e ao emprego.",
                "Regulamenta ciência, tecnologia e inovação em escolas.",
            ],
            "tema": ["Ciência, Tecnologia e Inovação", "Economia", "Ciência, Tecnologia e Inovação"],
            "dataApresentacao": ["2026-01-01", "2026-01-02", "2026-01-03"],
        }
    )
    proposicoes.to_parquet(data_dir / "proposicoes_deputados.parquet", index=False)

    with open(data_dir / "sumarizacao_proposicoes.json", "w", encoding="utf-8") as file:
        json.dump({"resumos": ["Resumo de inovação", "Resumo de economia"]}, file, ensure_ascii=False, indent=2)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = Path(temp_dir)
        _write_fixture(base_dir)

        kb = build_knowledge_base(str(base_dir))
        assert len(kb.documents) >= 4, "Esperava ao menos 4 documentos no índice"

        respostas = {
            "partidos": responder_pergunta("Qual é o partido político com mais deputados na câmara?", str(base_dir)),
            "despesas": responder_pergunta("Qual é o deputado com mais despesas na câmara?", str(base_dir)),
            "tipo": responder_pergunta("Qual é o tipo de despesa mais declarada pelos deputados da câmara?", str(base_dir)),
            "economia": responder_pergunta("Quais são as informações mais relevantes sobre as proposições que falam de Economia?", str(base_dir)),
            "ciencia": responder_pergunta("Quais são as informações mais relevantes sobre as proposições que falam de 'Ciência, Tecnologia e Inovação'?", str(base_dir)),
        }

        assert "PT" in respostas["partidos"]["answer"], respostas["partidos"]["answer"]
        assert "Bruno" in respostas["despesas"]["answer"], respostas["despesas"]["answer"]
        assert "Locomoção" in respostas["tipo"]["answer"], respostas["tipo"]["answer"]
        assert "Economia" in respostas["economia"]["answer"], respostas["economia"]["answer"]
        assert "Ciência, Tecnologia e Inovação" in respostas["ciencia"]["answer"], respostas["ciencia"]["answer"]

        print("assistant_checks_ok")


if __name__ == "__main__":
    main()
