# Sistema de Atendimento ao Cliente com IA — Projeto de Bloco

Sistema de atendimento ao cliente alimentado por inteligência artificial: um agente que recebe a
mensagem de um cliente e infere a **intenção** por trás dela (problema técnico, cobrança, dúvida de
produto, reembolso, cancelamento). Ao final do bloco, o sistema construído será também **atacado**
(red team) para descobrir falhas de segurança — por isso a API já nasce com autenticação JWT.

## Estado atual (TP1)

| Etapa | Status |
|---|---|
| 1. Documentação técnica do dataset | ✅ Concluída (abaixo e no notebook) |
| 2. EDA completo (inspeção, qualidade, limpeza, univariada) | ✅ Concluída — `eda/eda.ipynb` |
| 3. Hipóteses sobre as intenções dos usuários | ✅ Concluída — 5 hipóteses no notebook |
| 4. API FastAPI + JWT (`/health`, `/auth/token`, `/predict`) | ⏳ Próxima etapa |
| 5. DFD com trust boundaries + tríade CIA | ⏳ Próxima etapa |

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
├── fastapi/                           # vazio — código-fonte da API (etapa 4)
└── others/                            # vazio — DFD em .png (etapa 5)
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

### API FastAPI — ainda não incluída nesta etapa

O diretório `fastapi/` será preenchido na etapa 4; a execução prevista será:

```bash
cd fastapi
uvicorn main:app --reload
```

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

## Licença

- Dataset: CC0: Public Domain.
- Código deste repositório: para fins acadêmicos do Projeto de Bloco.
