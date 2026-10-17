"""Gera others/DFD.png e others/CIA.png a partir do estado atual da API.

Uso (a partir da raiz do repositório, com o ambiente do EDA ativo, que já
tem matplotlib):  python others/gerar_diagramas.py

Os diagramas refletem SOMENTE o que existe em fastapi/; componentes ainda
não implementados (banco de dados, modelo de classificação) aparecem
tracejados em cinza e marcados como PLANEJADO.
"""

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path(__file__).resolve().parent

TB_COLOR = "#c0392b"
PLANNED = "#9a9a9a"
PROC_FILL = "#e8f1fb"
STORE_FILL = "#fdf5e6"


# ---------------------------------------------------------------------------
# DFD
# ---------------------------------------------------------------------------


def _box(ax, x, y, w, h, text, fill="white", ls="-", ec="black", rounded=True, fs=9, color="black"):
    style = "round,pad=0.02,rounding_size=0.25" if rounded else "square,pad=0"
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fill, ec=ec, ls=ls, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color)


def _store(ax, x, y, w, h, text, ec="black", ls="-", color="black"):
    """Depósito de dados no estilo DFD: retângulo aberto à direita, com a
    coluna do identificador à esquerda."""
    ax.add_patch(Rectangle((x, y), w, h, fc=STORE_FILL if ls == "-" else "white", ec="none"))
    for yy in (y, y + h):
        ax.plot([x, x + w], [yy, yy], color=ec, lw=1.3, ls=ls)
    ax.plot([x, x], [y, y + h], color=ec, lw=1.3, ls=ls)
    ax.plot([x + 0.55, x + 0.55], [y, y + h], color=ec, lw=1.0, ls=ls)
    ident, label = text.split(" ", 1)
    ax.text(x + 0.27, y + h / 2, ident, ha="center", va="center", fontsize=8.5, weight="bold", color=color)
    ax.text(x + 0.55 + (w - 0.55) / 2, y + h / 2, label, ha="center", va="center", fontsize=8.5, color=color)


def _boundary(ax, x, y, w, h, label, color=TB_COLOR, label_y=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.3",
                                fc="none", ec=color, ls=(0, (6, 4)), lw=1.8))
    ax.text(x + 0.15, (label_y if label_y is not None else y + h + 0.12), label,
            ha="left", va="bottom", fontsize=9.5, weight="bold", color=color)


def _arrow(ax, p1, p2, label="", color="black", ls="-", rad=0.0, lx=0.0, ly=0.0, fs=8.2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=13, color=color,
                                 lw=1.2, ls=ls, connectionstyle=f"arc3,rad={rad}"))
    if label:
        mx, my = (p1[0] + p2[0]) / 2 + lx, (p1[1] + p2[1]) / 2 + ly
        ax.text(mx, my, label, ha="center", va="center", fontsize=fs, color=color,
                bbox=dict(fc="white", ec="none", pad=1.2))


def draw_dfd():
    fig, ax = plt.subplots(figsize=(17, 10.5))
    ax.set_xlim(0, 17)
    ax.set_ylim(-1.6, 10.6)
    ax.axis("off")

    ax.text(8.5, 10.35, "DFD — Sistema de Atendimento ao Cliente com IA (estado atual da API)",
            ha="center", fontsize=14, weight="bold")

    # Entidade externa
    _box(ax, 0.2, 4.3, 2.3, 1.6, "E1\nCliente da API\n(app, navegador,\nSwagger UI)",
         fill="#f4f4f4", rounded=False, fs=9.5)

    # TB1: fronteira rede/Internet ↔ processo da API
    _boundary(ax, 3.3, 0.5, 9.0, 9.1,
              "TB1 — Fronteira Rede/Internet ↔ Processo da API (uvicorn + FastAPI, memória do processo)")

    _box(ax, 3.7, 4.25, 2.3, 1.7, "P0\nMiddlewares\nCORS (allowlist) +\nheaders de segurança",
         fill=PROC_FILL)
    _box(ax, 3.7, 7.3, 2.3, 1.3, "P1\nGET /health", fill=PROC_FILL)
    _box(ax, 7.0, 7.1, 2.5, 1.7, "P2\nPOST /auth/token\nrate limit +\nbcrypt + emite JWT",
         fill=PROC_FILL)
    _box(ax, 7.0, 4.25, 2.5, 1.7, "P3\nget_current_user\nvalida JWT (HS256,\nexp, sub, usuário)",
         fill=PROC_FILL)
    _box(ax, 7.0, 1.0, 2.5, 1.9, "P4\nPOST /predict\nGET /predictions/{id}\n+ ensure_owner (BOLA)\nintenção placeholder",
         fill=PROC_FILL)

    _store(ax, 10.4, 8.05, 1.75, 0.8, "D2 Tentativas\nde login (dict)")
    _store(ax, 10.4, 6.2, 1.75, 0.8, "D1 Usuários\n(dict em memória)")
    _store(ax, 10.4, 1.5, 1.75, 0.9, "D3 Histórico de\npredições (dict)")

    # TB2: processo ↔ configuração/segredos do host
    _boundary(ax, 13.0, 5.6, 3.8, 3.0, "TB2 — Processo da API ↔ Host (segredos)")
    _store(ax, 13.3, 6.3, 3.2, 1.5, "D4 Arquivo .env\nJWT_SECRET_KEY,\nALLOWED_ORIGINS,\nlimites de rate limit")

    # TB3 (planejada): processo ↔ serviços de dados
    _boundary(ax, 13.0, 0.5, 3.8, 4.0, "TB3 (PLANEJADA) — API ↔ serviços de dados", color=PLANNED)
    _store(ax, 13.3, 2.9, 3.2, 0.9, "D5 Banco de dados\n(SQLModel) — PLANEJADO", ec=PLANNED, ls="--", color=PLANNED)
    _box(ax, 13.3, 0.9, 3.2, 1.3, "P5 Modelo de classificação\nde intenção — PLANEJADO",
         ls="--", ec=PLANNED, color=PLANNED, fs=8.5)

    # Fluxos — entrada única pela TB1 via P0
    _arrow(ax, (2.5, 5.45), (3.7, 5.45), "1–4 req. HTTP", ly=0.28)
    _arrow(ax, (3.7, 4.75), (2.5, 4.75), "respostas", ly=-0.28)
    _arrow(ax, (4.85, 5.95), (4.85, 7.3), "1 /health", lx=-0.05)
    _arrow(ax, (6.0, 5.75), (7.0, 7.6), "2 username,\npassword (form)", lx=-0.25, ly=0.15)
    _arrow(ax, (6.0, 5.1), (7.0, 5.1), "3–4 Bearer\n+ corpo", ly=0.0)
    _arrow(ax, (8.25, 4.25), (8.25, 2.9), "User\nautenticado", lx=0.55)

    _arrow(ax, (9.5, 8.45), (10.4, 8.45), "tentativas", ly=0.25, fs=7.8)
    _arrow(ax, (10.4, 6.85), (9.5, 7.35), "hash", ly=0.22, fs=7.8)
    _arrow(ax, (10.4, 6.35), (9.5, 5.6), "existe?", ly=-0.25, lx=0.25, fs=7.8)
    _arrow(ax, (9.5, 1.75), (10.4, 1.75), "grava", ly=-0.22, fs=7.8)
    _arrow(ax, (10.4, 2.2), (9.5, 2.2), "lê + dono", ly=0.22, fs=7.8)

    _arrow(ax, (13.3, 7.05), (12.3, 7.05), "lido no startup\n(config.py)", ly=-0.75, lx=0.15, fs=7.8)
    _arrow(ax, (12.15, 1.95), (13.3, 3.2), "futuro", color=PLANNED, ls="--", fs=7.8)
    _arrow(ax, (9.5, 1.3), (13.3, 1.3), "futuro: texto do ticket → intenção + confidence",
           color=PLANNED, ls="--", ly=-0.25, fs=7.8, lx=0.6)

    # Legenda
    legend = (
        "Fluxos:  1 GET /health → 200 {status: ok}   ·   2 POST /auth/token → 200 JWT | 401 credenciais | 429 rate limit   ·   "
        "3 POST /predict + Bearer → 200 {id, intent, confidence} | 401 | 422\n"
        "4 GET /predictions/{id} + Bearer → 200 se o usuário for o dono | 404 se for de outro usuário ou não existir (BOLA)   ·   "
        "Tracejado vermelho = trust boundary   ·   Cinza tracejado = componente PLANEJADO (não implementado)"
    )
    ax.text(8.5, -0.75, legend, ha="center", va="center", fontsize=8.6,
            bbox=dict(fc="#fafafa", ec="#cccccc", pad=6))

    fig.savefig(OUT / "DFD.png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------------------
# CIA
# ---------------------------------------------------------------------------

# (componente, status, confidencialidade, integridade, disponibilidade)
CIA_ROWS = [
    ("E1 Cliente da API", "Implementado",
     "Credenciais e JWT ficam com o cliente; só trafegam no form de login e no header Authorization (nunca em URL).",
     "Todo dado enviado é revalidado pela API (Pydantic); o cliente não é confiável (TB1).",
     "Recebe 429 + Retry-After ao exceder o limite de login, em vez de ter a conta travada."),
    ("P0 Middlewares (CORS + headers)", "Implementado",
     "CORS por allowlist (ALLOWED_ORIGINS), sem cookies; Referrer-Policy no-referrer.",
     "CSP default-src 'none', X-Frame-Options DENY e nosniff impedem uso da resposta em outro contexto.",
     "Middleware leve, sem I/O externo."),
    ("P2/P3 Autenticação JWT + OAuth2", "Implementado",
     "JWT_SECRET_KEY só no .env; senhas com hash bcrypt; mesma mensagem 401 para usuário inexistente e senha errada.",
     "Assinatura HS256 (só esse algoritmo é aceito); token adulterado, expirado, sem 'sub' ou de usuário inexistente → 401.",
     "Rate limit 5/60s por IP e por username mitiga brute force sem derrubar o serviço."),
    ("P4 /predict e /predictions/{id}", "Implementado (placeholder)",
     "Rota protegida por Bearer; ensure_owner retorna 404 para recurso de outro usuário (BOLA, sem enumeração).",
     "extra='forbid' + limites de tamanho → 422; resposta tipada (intent enum, confidence ∈ [0,1]).",
     "Resposta fixa sem inferência; limite de 5.000 caracteres no texto evita payloads gigantes."),
    ("D1 Usuários (dict em memória)", "Implementado",
     "Guarda somente hash bcrypt, nunca a senha em texto.",
     "Somente leitura em execução; não há rota que altere usuários.",
     "Volátil: recriado a cada start (aceitável para demonstração)."),
    ("D2 Tentativas de login (dict)", "Implementado",
     "Guarda apenas chaves ip:/user: e timestamps.",
     "Acesso protegido por lock contra condições de corrida.",
     "Por processo: com várias réplicas o limite não é global (Redis no futuro)."),
    ("D3 Histórico de predições (dict)", "Implementado",
     "Cada registro tem dono; leitura só pelo dono. IDs UUID4 não sequenciais.",
     "Escrita apenas via POST /predict autenticado, protegida por lock.",
     "Volátil: perdido ao reiniciar o processo."),
    ("D4 Arquivo .env (segredos)", "Implementado",
     "Fora do git (.gitignore); só .env.example é versionado.",
     "Lido uma vez no startup; JWT_EXPIRE_MINUTES inválido aborta a inicialização.",
     "Sem JWT_SECRET_KEY a API não inicia (falha segura)."),
    ("Dados dos tickets (em trânsito)", "Implementado",
     "HTTP em ambiente local; HTTPS obrigatório antes de qualquer implantação (HSTS já enviado).",
     "Validados pelo Pydantic na entrada.",
     "Dependem da disponibilidade de P4."),
    ("D5 Banco de dados (SQLModel)", "PLANEJADO",
     "Acesso por usuário de serviço com privilégio mínimo; conexão TLS.",
     "Queries parametrizadas pelo ORM (sem SQL cru); ownership por coluna owner.",
     "Backups e persistência substituem D1/D3 em memória."),
    ("P5 Modelo de classificação", "PLANEJADO",
     "Texto dos tickets não deve ser logado nem enviado a terceiros.",
     "Artefato do modelo versionado e com hash verificado.",
     "Timeout na inferência para não travar a API."),
]


def draw_cia():
    wrap = lambda s, w: "\n".join(textwrap.wrap(s, w))
    headers = ["Componente", "Status", "Confidencialidade (C)", "Integridade (I)", "Disponibilidade (A)"]
    widths = [0.15, 0.10, 0.25, 0.25, 0.25]
    wrap_w = [20, 13, 40, 40, 40]
    cells = [[wrap(c, w) for c, w in zip(row, wrap_w)] for row in CIA_ROWS]
    heights = [max(c.count("\n") + 1 for c in row) for row in cells]

    fig, ax = plt.subplots(figsize=(17, 0.27 * (sum(heights) + 2 * len(cells)) + 1.0))
    fig.subplots_adjust(top=0.95, bottom=0.05)
    ax.axis("off")
    ax.set_title("Tríade CIA aplicada aos componentes do DFD (estado atual + componentes planejados)",
                 fontsize=13, weight="bold", pad=12)
    table = ax.table(cellText=cells, colLabels=headers, colWidths=widths, loc="upper center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(8.6)
    unit = 1.0 / (sum(heights) + 2 * len(cells) + 2)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_height(unit * 2)
            cell.set_facecolor("#dfe8f3")
            cell.set_text_props(weight="bold", ha="center")
            continue
        planned = CIA_ROWS[r - 1][1] == "PLANEJADO"
        cell.set_height(unit * (heights[r - 1] + 2))
        if planned:
            cell.set_facecolor("#f2f2f2")
            cell.get_text().set_color("#666666")
            cell.get_text().set_style("italic")
        if c in (0, 1):
            cell.get_text().set_weight("bold")

    fig.text(0.5, 0.005, "Linhas em cinza/itálico: componentes PLANEJADOS (ainda não implementados); "
             "requisitos que deverão atender quando forem adicionados.",
             ha="center", fontsize=9, color="#555555")
    fig.savefig(OUT / "CIA.png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    draw_dfd()
    draw_cia()
    print(f"Gerados: {OUT / 'DFD.png'} e {OUT / 'CIA.png'}")
