"""Rate limiting para o endpoint de autenticação (``POST /auth/token``).

Escolha e justificativa técnica
--------------------------------
OWASP API4:2023 (Unrestricted Resource Consumption) e o OWASP
Authentication Cheat Sheet recomendam limitar tentativas de login para
mitigar ataques de força bruta e credential stuffing. Sem um limite, um
atacante pode testar milhares de combinações de usuário/senha por
segundo contra ``/auth/token``.

Limite escolhido: **5 tentativas por 60 segundos**, aplicado em duas
dimensões independentes — por endereço IP do cliente e por ``username``
informado no formulário.

- **Por que 5 tentativas / 60s?** É o valor mais frequentemente citado
  em guias de hardening (o NIST SP 800-63B, seção 5.2.2, recomenda
  limitar o número de tentativas falhas consecutivas; implementações de
  referência como o OWASP costumam usar 3-5/min como ponto de partida)
  como equilíbrio entre usabilidade — um usuário real raramente erra a
  senha mais de 3-4 vezes seguidas — e dificultar brute force: a 5
  tentativas/min, varrer um espaço de senhas numéricas de 6 dígitos
  levaria da ordem de meses, tornando o ataque impraticável.
- **Por que limitar por IP *e* por username, e não só um dos dois?**
  Limitar somente por IP não impede credential stuffing distribuído
  (muitos IPs diferentes testando a mesma conta-alvo). Limitar somente
  por username não impede um único IP de testar várias contas
  diferentes em sequência. Aplicar as duas dimensões cobre os dois
  cenários de ataque.
- **Implementação:** janela fixa em memória de processo (``dict`` com
  timestamps protegido por lock), suficiente para uma única
  instância/processo, como é o caso deste projeto acadêmico. Em
  produção com múltiplas réplicas, o mesmo contrato (uma função que
  lança 429 ao estourar o limite) deve ser respaldado por um
  armazenamento compartilhado entre instâncias (ex.: Redis) — trocar a
  estrutura em memória por, por exemplo, ``INCR``+``EXPIRE`` no Redis
  não muda a interface pública deste módulo.

A resposta ao exceder o limite é ``HTTP 429 Too Many Requests`` com
header ``Retry-After``, conforme RFC 6585.
"""

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

from security.config import (
    AUTH_RATE_LIMIT_MAX_ATTEMPTS,
    AUTH_RATE_LIMIT_WINDOW_SECONDS,
)

_attempts_by_key: dict[str, list[float]] = defaultdict(list)
_lock = Lock()


def _prune_and_count(key: str, now: float) -> int:
    window_start = now - AUTH_RATE_LIMIT_WINDOW_SECONDS
    attempts = [ts for ts in _attempts_by_key[key] if ts > window_start]
    _attempts_by_key[key] = attempts
    return len(attempts)


def check_rate_limit(key: str) -> None:
    """Levanta HTTP 429 se ``key`` (ex.: ``ip:...`` ou ``user:...``)
    já acumulou ``AUTH_RATE_LIMIT_MAX_ATTEMPTS`` tentativas dentro da
    janela de ``AUTH_RATE_LIMIT_WINDOW_SECONDS``. Caso contrário,
    registra a tentativa atual."""
    now = time.monotonic()
    with _lock:
        count = _prune_and_count(key, now)
        if count >= AUTH_RATE_LIMIT_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas de login. Tente novamente em instantes.",
                headers={"Retry-After": str(AUTH_RATE_LIMIT_WINDOW_SECONDS)},
            )
        _attempts_by_key[key].append(now)


def enforce_auth_rate_limit(request: Request) -> None:
    """Dependency FastAPI para ``/auth/token``: aplica o limite por IP
    do cliente. O limite por ``username`` é aplicado separadamente
    dentro da rota, pois o username só fica disponível após o parse do
    form (``OAuth2PasswordRequestForm``) — ver ``routes/auth.py``."""
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(f"ip:{client_ip}")
