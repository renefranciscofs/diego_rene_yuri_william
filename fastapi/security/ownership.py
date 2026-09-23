"""Verificação de ownership (BOLA — OWASP API1:2023: Broken Object Level
Authorization).

Nota de aplicabilidade
-----------------------
Nenhuma rota desta API retorna hoje um recurso persistido por ID: não
há camada de banco de dados (``security/users.py`` usa um dicionário
Python em memória, não uma tabela) e ``POST /predict`` não lê nem grava
nenhum recurso identificável — apenas recebe um texto e devolve uma
predição fixa (placeholder). Por isso não existe, no estado atual, uma
rota "que retorna recursos por ID" para aplicar a checagem de
ownership.

Este módulo existe para que o padrão já esteja pronto e seja
reaproveitado assim que uma rota desse tipo for adicionada — por
exemplo, ao integrar o modelo de classificação com um histórico de
predições por usuário (``GET /tickets/{ticket_id}``). Uso pretendido,
já com uma eventual camada de persistência via SQLModel (ver nota sobre
SQL no README/SECURITY.md):

    ticket = session.exec(
        select(Ticket).where(Ticket.id == ticket_id)
    ).first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Recurso não encontrado")
    ensure_owner(ticket.owner_username, current_user)  # checagem BOLA
    return ticket

Por que 404 e não 403 quando o dono não confere? Retornar 403
confirmaria para um atacante que o recurso existe (só que pertence a
outra pessoa), permitindo enumerar IDs válidos por tentativa e erro.
Responder 404 — idêntico ao caso "recurso realmente não existe" — evita
esse vazamento de informação.
"""

from fastapi import HTTPException, status

from models.user import User


def ensure_owner(resource_owner_username: str, current_user: User) -> None:
    """Garante que ``current_user`` é o dono do recurso. Levanta 404
    (não 403 — ver docstring do módulo) caso contrário."""
    if resource_owner_username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado",
        )
