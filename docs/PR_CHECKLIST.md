# Checklist de PR

## Resumo
- [ ] A PR descreve claramente o problema e a solução.
- [ ] O título é objetivo e no padrão do projeto.
- [ ] O impacto funcional foi documentado.

## Qualidade
- [ ] Dashboard abre sem erros nas abas Overview, Despesas, Proposições e Assistente.
- [ ] `tests/run_basic_checks.py` executa sem falhas.
- [ ] `tests/run_assistant_checks.py` executa sem falhas.
- [ ] Mudanças não quebram fluxo existente.

## Dados e Artefatos
- [ ] Nenhum arquivo local temporário foi incluído indevidamente.
- [ ] Arquivos gerados (cache/FAISS/logs) não foram commitados.
- [ ] Apenas dados necessários ao projeto foram versionados.

## Evidências
- [ ] Incluiu screenshots ou descrição do comportamento final.
- [ ] Incluiu comandos usados para validação.

## Segurança
- [ ] Sem chaves/API keys no commit.
- [ ] `.env` não foi versionado.
