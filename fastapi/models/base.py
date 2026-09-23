from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """Base para os modelos de ENTRADA (request bodies) da API.

    OWASP API3:2023 (Broken Object Property Level Authorization) e a
    prática de "mass assignment": ao proibir campos extras não
    declarados no schema, evitamos que um cliente envie atributos
    inesperados (ex.: um campo que não faça parte do contrato da rota)
    e que eles sejam silenciosamente ignorados — ou, em modelos menos
    cuidadosos, aceitos — pelo parser. Um payload com campo desconhecido
    passa a resultar em HTTP 422 (Unprocessable Entity) em vez de ser
    processado.

    Todo novo modelo Pydantic usado como corpo de requisição (`Body`)
    deve herdar desta classe em vez de `pydantic.BaseModel` diretamente.
    """

    model_config = ConfigDict(extra="forbid")
