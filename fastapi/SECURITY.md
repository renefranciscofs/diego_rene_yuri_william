# Controles de segurança aplicados

Este documento registra os controles de segurança aplicados à API (`fastapi/`) e a
justificativa técnica de cada escolha, conforme pedido na etapa de hardening do
Projeto de Bloco.

## 1. Controles OWASP Top 10 / API Security Top 10

### 1.1 Pydantic com `extra='forbid'` em todos os modelos de entrada

- Adicionado `models/base.py::StrictBaseModel`, com `model_config =
  ConfigDict(extra="forbid")`.
- `models/predict.py::PredictRequest` — único modelo usado como corpo de
  requisição (`Body`) na API hoje — passa a herdar de `StrictBaseModel`.
- Efeito: um payload em `POST /predict` com qualquer campo além de
  `ticket_subject`/`ticket_description` é rejeitado com `422 Unprocessable
  Entity`, em vez de ter o campo extra ignorado silenciosamente. Mitiga
  ataques de "mass assignment" / API3:2023 (Broken Object Property Level
  Authorization).
- `POST /auth/token` usa `OAuth2PasswordRequestForm` (dependência nativa do
  FastAPI baseada em `Form(...)`, não um `BaseModel`), então `extra='forbid'`
  não se aplica diretamente a ela — campos de formulário extras são apenas
  ignorados pelo parser, sem risco de mass assignment (não há nenhum campo
  sensível como `is_admin` no formulário de login).

### 1.2 SQLModel com queries parametrizadas (sem SQL raw)

**Nota de aplicabilidade:** a API não possui, no estado atual, nenhuma
camada de persistência em banco de dados. `security/users.py` usa um
dicionário Python em memória (`_FAKE_USERS_DB`) como base de usuários de
demonstração, e não há SQL de nenhum tipo no projeto — logo, não há
superfície de SQL injection para corrigir hoje.

Ainda assim, o código foi documentado (comentário em `security/users.py`)
para deixar explícito o padrão a seguir assim que uma base de dados real for
introduzida (próxima etapa natural, ao integrar o modelo de classificação
com histórico de predições por usuário):

- Usar **SQLModel** (ou SQLAlchemy Core/ORM) com queries construídas via
  API do próprio ORM — ex. `session.exec(select(User).where(User.username
  == username))` — nunca SQL montado por f-string/`%`/concatenação com
  input do usuário.
- Isso garante que os valores de entrada sejam sempre passados como
  parâmetros vinculados (bind parameters) pelo driver do banco, eliminando a
  classe de vulnerabilidade de SQL Injection (OWASP A03:2021).

### 1.3 Verificação de ownership (BOLA) nas rotas que retornam recursos por ID

Criado `security/ownership.py::ensure_owner(resource_owner_username,
current_user)` e aplicado em `GET /predictions/{prediction_id}`
(`routes/predict.py`, adicionada na etapa de testes). Padrão de uso com uma futura camada de persistência:

```python
ticket = session.exec(select(Ticket).where(Ticket.id == ticket_id)).first()
if ticket is None:
    raise HTTPException(status_code=404, detail="Recurso não encontrado")
ensure_owner(ticket.owner_username, current_user)  # checagem BOLA
return ticket
```

A função responde com `404` (não `403`) quando o usuário autenticado não é o
dono do recurso, para não confirmar a um atacante que o ID existe mas
pertence a outra pessoa (evita enumeração de recursos — OWASP API1:2023,
Broken Object Level Authorization).

## 2. Headers de segurança HTTP e CORS

Implementado em `security/headers.py` (`SecurityHeadersMiddleware`,
registrado em `main.py`), aplicado a toda resposta:

| Header | Valor | Objetivo |
| --- | --- | --- |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | Força HTTPS por 2 anos, mitiga downgrade/SSL stripping (só tem efeito atrás de HTTPS) |
| `X-Content-Type-Options` | `nosniff` | Impede MIME sniffing pelo navegador |
| `X-Frame-Options` | `DENY` | Impede embutir respostas em `<iframe>` (clickjacking) |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | API JSON pura: política mais restritiva possível |
| `Referrer-Policy` | `no-referrer` | Evita vazar a URL (possíveis tokens/IDs) via header `Referer` |

**Exceção:** `/docs`, `/redoc` e `/openapi.json` (Swagger UI/ReDoc nativos do FastAPI)
não recebem o header `Content-Security-Policy`. Essas páginas carregam CSS/JS de um
CDN externo (`cdn.jsdelivr.net`); `default-src 'none'` bloquearia esses recursos e
deixaria a página em branco no navegador. Os demais headers de segurança continuam
aplicados normalmente a essas rotas.

CORS (`CORSMiddleware` em `main.py`) configurado com:

- `allow_origins`: allowlist explícita via variável de ambiente
  `ALLOWED_ORIGINS` (lista separada por vírgula) — nunca `"*"` em produção.
- `allow_credentials=False`: a autenticação é via Bearer token no header
  `Authorization`, não via cookies, então não há necessidade (nem é seguro)
  combinar `allow_credentials=True` com origens amplas.
- `allow_methods`/`allow_headers` restritos ao que a API realmente usa
  (`GET`, `POST`; `Authorization`, `Content-Type`).

## 3. Rate limiting em `POST /auth/token`

Implementado em `security/rate_limit.py` e aplicado em `routes/auth.py`.

**Limite escolhido: 5 tentativas por 60 segundos**, em duas dimensões
independentes — por IP do cliente (via dependency `enforce_auth_rate_limit`)
e por `username` informado no formulário (via `check_rate_limit` chamado
dentro da rota, já que o username só está disponível após o parse do
form).

**Justificativa técnica:**

- OWASP API4:2023 (Unrestricted Resource Consumption) e o OWASP
  Authentication Cheat Sheet recomendam limitar tentativas de login para
  mitigar força bruta e credential stuffing.
- 5/min é o valor mais comum em guias de hardening (NIST SP 800-63B §5.2.2
  recomenda limitar tentativas falhas consecutivas) como equilíbrio entre
  usabilidade — um usuário real raramente erra a senha mais de 3-4 vezes
  seguidas — e dificultar brute force: a esse ritmo, varrer um espaço de
  senhas numéricas de 6 dígitos levaria da ordem de meses.
- Limitar **só** por IP não impede credential stuffing distribuído (vários
  IPs testando a mesma conta); limitar **só** por username não impede um
  único IP de testar várias contas. As duas dimensões juntas cobrem ambos os
  cenários.
- Excede o limite → `HTTP 429 Too Many Requests` com header `Retry-After`
  (RFC 6585).

**Limitação conhecida:** a implementação usa um contador em memória de
processo (`dict` + lock), suficiente para a instância única deste projeto
acadêmico. Em produção com múltiplas réplicas, o mesmo contrato (uma função
que lança 429 ao estourar o limite) deveria ser respaldado por um
armazenamento compartilhado entre instâncias, como Redis, para que o limite
valha globalmente e não por processo.

## Variáveis de ambiente novas

Ver `.env.example`:

```
ALLOWED_ORIGINS=http://localhost:3000
AUTH_RATE_LIMIT_MAX_ATTEMPTS=5
AUTH_RATE_LIMIT_WINDOW_SECONDS=60
```

## 4. Organização da autenticação e testes de token (feedback da avaliação)

- `security/config.py` foi reorganizado em seções numeradas: **(1) Autenticação (JWT +
  OAuth2PasswordBearer)**, **(2) CORS**, **(3) Rate limiting**. É o único módulo que lê o
  ambiente.
- A rota de emissão do token passou a ser definida uma única vez (`AUTH_ROUTER_PREFIX`,
  `AUTH_TOKEN_PATH`, `AUTH_TOKEN_URL`) e é usada tanto pelo router (`routes/auth.py`) quanto pelo
  `OAuth2PasswordBearer(tokenUrl=AUTH_TOKEN_URL)` (`security/oauth2.py`) — antes eram duas strings
  soltas que podiam divergir.
- `JWT_EXPIRE_MINUTES` precisa ser um inteiro positivo; caso contrário a API não inicia (falha
  segura, assim como já acontece sem `JWT_SECRET_KEY`).
- O fluxo JWT/OAuth2PasswordBearer não mudou: login → JWT HS256 com `sub`/`exp` →
  `Depends(get_current_user)` nas rotas protegidas.

Testes automatizados de token em `tests/test_security.py` (todos esperam `401`):

| Caso | Teste |
| --- | --- |
| Token ausente | `test_predict_without_token_returns_401`, `test_get_prediction_without_token_returns_401` |
| Token malformado / assinatura forjada | `test_predict_with_invalid_token_returns_401` |
| Token sem assinatura (`"alg": "none"`) | `test_predict_with_alg_none_token_returns_401` |
| Token sem a claim `sub` | `test_predict_with_token_without_sub_returns_401` |
| Token de usuário inexistente | `test_predict_with_token_for_unknown_user_returns_401` |
| Token expirado | `test_predict_with_expired_token_returns_401` |

