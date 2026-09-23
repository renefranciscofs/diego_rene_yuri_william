# Sistema de Atendimento ao Cliente com IA — Projeto de Bloco

Sistema de atendimento ao cliente alimentado por inteligência artificial: um agente que recebe a
mensagem de um cliente e infere a **intenção** por trás dela (problema técnico, cobrança, dúvida de
produto, reembolso, cancelamento). Ao final do bloco, o sistema construído será também **atacado**
(red team) para descobrir falhas de segurança — por isso a API já nasce com autenticação JWT.

## Estado atual (TP1)

| Etapa                                                       | Status                                 |
| ----------------------------------------------------------- | -------------------------------------- |
| 1. Documentação técnica do dataset                          | ✅ Concluída (abaixo e no notebook)    |
| 2. EDA completo (inspeção, qualidade, limpeza, univariada)  | ✅ Concluída — `eda/eda.ipynb`         |
| 3. Hipóteses sobre as intenções dos usuários                | ✅ Concluída — 5 hipóteses no notebook |
| 4. API FastAPI + JWT (`/health`, `/auth/token`, `/predict`) | ✅ Estrutura inicial — `fastapi/`      |
| 5. DFD com trust boundaries + tríade CIA                    | ✅ Concluída - `others/`               |

## Dataset: Customer Support Ticket Dataset

- **Fonte:** [Kaggle — suraj520/customer-support-ticket-dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)
- **Licença:** CC0: Public Domain (uso livre, inclusive comercial)
- **Arquivo:** `customer_support_tickets.csv` — 8.469 registros × 17 colunas (~3,9 MB)
- **Domínio:** tickets de suporte de produtos de tecnologia (laptops, smartphones, TVs, acessórios)
- **Alvo da classificação de intenção:** `Ticket Type` (5 classes balanceadas: technical issue,
  billing inquiry, product inquiry, refund request, cancellation request)
- **Texto para NLP:** `Ticket Subject` (16 assuntos) e `Ticket Description` (descrição longa)
- **Dimensões de contexto:** cliente (idade, gênero), produto (42), status, prioridade, canal,
  tempos de resposta/resolução, satisfação (1–5)
- **Natureza:** sintética — artefatos de geração identificados no EDA (placeholder
  `{product_purchased}` em 100% das descrições, janela de tickets de ~2,5 dias, resoluções
  anteriores a primeiras respostas em ~83% dos casos)

**Motivo da escolha:** aderência direta ao objetivo do bloco (texto livre + rótulo de intenção =
matéria-prima de um agente de IA), riqueza de dimensões de contexto, problema multiclasse
balanceado e realista, e licença CC0 compatível com repositório público.

## Estrutura de pastas (estado atual do desenvolvimento)

```
.
├── README.md                          # este arquivo
├── requirements.txt                   # dependências Python
├── .gitignore                         # ignora .venv/, caches e artefatos de kernel
├── data/
│   ├── customer_support_tickets.csv         # dataset original (Kaggle)
│   └── customer_support_tickets_clean.csv   # versão limpa (gerada pela célula de limpeza do EDA)
├── eda/
│   └── eda.ipynb                      # EDA completo — único .ipynb, já executado com gráficos embutidos
├── fastapi/                           # código-fonte da API (etapa 4)
│   ├── main.py                        # ponto de entrada (uvicorn main:app --reload)
│   ├── requirements.txt               # dependências da API (isoladas das do EDA)
│   ├── .env.example                   # variáveis de ambiente esperadas (JWT_SECRET_KEY, ...)
│   ├── routes/                        # endpoints: health, auth, predict
│   ├── models/                        # schemas Pydantic de entrada/saída
│   └── security/                      # JWT, OAuth2PasswordBearer, base de usuários
└── others/                            # DFD e CIA em .png (etapa 5)
    └── CIA.png                        # análise CIA
    └── DFD.png                        # análise DFD
```

## Instalação

**Pré-requisitos:** Python 3.10+, git.

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd <repositorio>

# 2. Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate            # Linux/macOS

# 3. Instalar dependências
pip install -r requirements.txt
```

> O dataset original já está versionado em `data/`. Para (re)baixar da fonte:
> `python -c "import kagglehub; print(kagglehub.dataset_download('suraj520/customer-support-ticket-dataset'))"`

## Execução

### EDA (notebook)

```bash
source .venv/bin/activate
jupyter notebook eda/eda.ipynb
```

O notebook já é entregue executado (saídas e gráficos embutidos). Segue a estrutura pedida no TP:
(1) compreensão do problema e do dataset, (2) inspeção inicial, (3) verificação da qualidade dos
dados, (4) limpeza e preparação, (5) análise univariada com histogramas, (6) hipóteses sobre as
intenções. Atenção: reexecutar a célula de limpeza regenera `data/customer_support_tickets_clean.csv`.

### API FastAPI

```bash
cd fastapi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # gera um valor aleatório
# cole o valor gerado em JWT_SECRET_KEY dentro de .env
uvicorn main:app --reload
```

> Também defina `ALLOWED_ORIGINS` (origens de CORS autorizadas) e, opcionalmente,
> `AUTH_RATE_LIMIT_MAX_ATTEMPTS`/`AUTH_RATE_LIMIT_WINDOW_SECONDS` no `.env` — valores
> padrão e justificativa em [`fastapi/SECURITY.md`](fastapi/SECURITY.md).

Endpoints disponíveis (docs interativas em `http://127.0.0.1:8000/docs`):

- `GET /health` — verificação de disponibilidade, sem autenticação.
- `POST /auth/token` — login (`OAuth2PasswordRequestForm`: `username`/`password`) e emissão de
  token JWT. Usuário de demonstração: `admin` / `admin123` (base em memória, ver
  `security/users.py` — trocar por uma base real antes de produção).
- `POST /predict` — protegido por Bearer token; recebe `ticket_subject`/`ticket_description` e
  retorna a intenção prevista, dentre as 5 classes de `Ticket Type` do dataset (`Technical issue`,
  `Billing inquiry`, `Product inquiry`, `Refund request`, `Cancellation request` — ver
  `models/predict.py::Intent`). Ainda é um placeholder: a integração com o modelo de classificação
  será feita em etapa futura.

## Hipóteses sobre as intenções dos usuários (resumo)

1. **Intenções equilibradas** — 5 classes entre 19,3% e 20,7%: não há intenção dominante;
   classificador multiclasse balanceado (baseline ≈ 20%).
2. **Prioridade não reflete intenção real de urgência** — ~50% dos tickets `High`/`Critical`
   vs. 33% fechados: urgência declarada é inflada/aleatória.
3. **Contato majoritariamente textual e digital** — ~75% por Email/Chat/Social media: valida
   agente baseado em NLP sobre texto.
4. **A intenção depende do tipo de problema, não do produto** — 42 produtos, top-1 ≈ 2,8%:
   o modelo generaliza sem features de produto.
5. **Texto bruto insuficiente para inferir intenção** — 100% das descrições com placeholder e
   ~69% em template fixo: risco de overfitting lexical; usar `Subject`/`Type` como sinal central.

Detalhamento completo, com as estatísticas que sustentam cada hipótese, no notebook (`eda/eda.ipynb`, Seção 6).

## DFD
![alt text](others/DFD.png)

## CIA
![alt text](others/CIA.png)
## Licença

- Dataset: CC0: Public Domain.
- Código deste repositório: para fins acadêmicos do Projeto de Bloco.
