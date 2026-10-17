"""Schemas Pydantic: o contrato de entrada e saída da API.

Não contêm lógica de negócio. Modelos de ENTRADA herdam de
`base.StrictBaseModel` (extra='forbid' → 422 para campos não declarados).

- `base.py`    — StrictBaseModel (base de todos os request bodies).
- `predict.py` — Intent, PredictRequest, PredictResponse (contrato de /predict).
- `token.py`   — Token (resposta de /auth/token).
- `user.py`    — User (usuário autenticado repassado às rotas).
"""
