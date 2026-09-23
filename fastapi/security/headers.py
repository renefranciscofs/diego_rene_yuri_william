"""Middleware de headers de segurança HTTP.

Headers aplicados a toda resposta da API:

- ``Strict-Transport-Security`` (HSTS): instrui o navegador a só falar
  HTTPS com este host pelos próximos 2 anos, incluindo subdomínios.
  Mitiga downgrade attacks / SSL stripping. Só tem efeito real quando a
  API é servida atrás de HTTPS (ex.: proxy reverso em produção) — é
  inofensivo em desenvolvimento HTTP local, o navegador simplesmente
  ignora o header fora de um contexto HTTPS.
- ``X-Content-Type-Options: nosniff`` — impede que o navegador tente
  "adivinhar" o MIME type de uma resposta, mitigando ataques de MIME
  sniffing.
- ``X-Frame-Options: DENY`` — impede que qualquer resposta da API seja
  embutida em um ``<iframe>``, mitigando clickjacking. Como esta é uma
  API JSON pura (não serve páginas HTML), não há motivo legítimo para
  ser enquadrada por outro site.
- ``Content-Security-Policy: default-src 'none'; frame-ancestors 'none'``
  — a API não serve HTML/JS/CSS, então a política mais restritiva
  possível é aplicada: bloqueia qualquer carregamento de recurso e
  reforça o ``X-Frame-Options`` via ``frame-ancestors``.
- ``Referrer-Policy: no-referrer`` — evita vazar a URL completa da
  requisição (que pode conter tokens/IDs em query string) para
  terceiros via header ``Referer``.

Usamos ``setdefault`` ao aplicar os headers para nunca sobrescrever um
valor que uma rota específica já tenha definido explicitamente.

Exceção: ``/docs``, ``/redoc`` e ``/openapi.json`` (Swagger UI/ReDoc do
próprio FastAPI) ficam de fora do CSP ``default-src 'none'``. Essas
páginas carregam CSS/JS de um CDN externo (``cdn.jsdelivr.net``); a
política restritiva bloquearia esses recursos e deixaria a página em
branco no navegador. As demais respostas da API (JSON) continuam com o
CSP mais restritivo — ele não tem efeito prático sobre uma resposta
JSON, mas mantém a postura "secure by default" onde não há motivo para
abrir exceção.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
}

_DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        headers = _SECURITY_HEADERS
        if request.url.path in _DOCS_PATHS:
            headers = {
                k: v for k, v in _SECURITY_HEADERS.items() if k != "Content-Security-Policy"
            }
        for header, value in headers.items():
            response.headers.setdefault(header, value)
        return response
