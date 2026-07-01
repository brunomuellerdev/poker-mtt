# Deploy — Render (app) + Neon (Postgres)

Arquitetura: **um único serviço** no Render (Docker) que roda o FastAPI e
**serve o frontend já buildado** na mesma origem. Banco no **Neon** (Postgres
permanente, tier grátis). Sem CORS, sem dor de cookie cross-site.

```
┌─────────────────────────────┐        ┌──────────────────────┐
│ Render Web Service (Docker) │        │ Neon (Postgres)      │
│  FastAPI  +  React estático │──SSL──▶│  free, permanente    │
│  poker-mtt.onrender.com     │        │  scale-to-zero       │
└─────────────────────────────┘        └──────────────────────┘
```

## O que já está no repositório

- `Dockerfile` — build multi-stage: node builda o frontend → python instala o
  backend e copia o build para `app/static`. No start roda `alembic upgrade
  head` e sobe o uvicorn.
- `render.yaml` — Blueprint do serviço web (plano free, Docker, healthcheck).
- `backend/app/main.py` — serve `app/static` e faz fallback SPA para deep links.

---

## Passo 1 — Criar o banco no Neon

1. Crie conta em https://neon.com (sem cartão).
2. **Create project** → escolha uma região perto de você (ex: AWS us-east / sa-east).
3. No dashboard, copie a **connection string**. Ela vem assim:
   ```
   postgresql://USER:PASSWORD@ep-xxx.REGION.aws.neon.tech/DBNAME?sslmode=require
   ```
4. **Converta o esquema** para o driver do projeto (psycopg): troque
   `postgresql://` por `postgresql+psycopg://`, mantendo o `?sslmode=require`:
   ```
   postgresql+psycopg://USER:PASSWORD@ep-xxx.REGION.aws.neon.tech/DBNAME?sslmode=require
   ```
   Guarde essa string — é o `DATABASE_URL`.

> As migrations (JSONB, colunas geradas, CHECK/enum, clock_timestamp) rodam
> exatamente como no Postgres local; o Neon é Postgres real.

---

## Passo 2 — Subir o código para o GitHub

O Render faz deploy a partir de um repositório Git. Se ainda não tem:

```bash
cd poker-mtt
git init
git add .
git commit -m "deploy: render + neon"
# crie um repo vazio no GitHub e:
git remote add origin https://github.com/SEU_USUARIO/poker-mtt.git
git push -u origin main
```

O `Dockerfile` e o `render.yaml` estão na **raiz** do repositório — é de lá que
o Render lê.

---

## Passo 3 — Criar o serviço no Render (via Blueprint)

1. Conta em https://render.com (sem cartão para o plano free).
2. **New** → **Blueprint** → conecte o repositório do GitHub.
3. O Render lê o `render.yaml` e propõe criar o serviço `poker-mtt`.
4. Ele vai pedir os valores das env vars marcadas como `sync: false`:
   - **DATABASE_URL** → a string do Neon do Passo 1 (com `+psycopg` e `sslmode=require`).
   - **JWT_SECRET** → um segredo forte. Gere um:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   (`DEBUG=false` e `COOKIE_SECURE=true` já vêm do `render.yaml`.)
5. **Apply** / **Create**. O primeiro build leva alguns minutos (builda o
   frontend + instala o backend). No deploy, o container roda as migrations
   automaticamente antes de subir.

Ao final você tem `https://poker-mtt.onrender.com` no ar.

---

## Passo 4 — Verificar

- `https://poker-mtt.onrender.com/health` → `{"status":"ok"}`
- `https://poker-mtt.onrender.com/` → a aplicação carrega.
- Registre um usuário, crie um torneio, dê refresh em `/tournaments` (o
  fallback SPA garante que deep links funcionam).

---

## Comportamento do tier grátis (esperado)

- **Cold start**: o serviço hiberna após ~15 min sem tráfego; a primeira
  requisição seguinte leva ~30-60s. Depois fica rápido. (Você aceitou isso.)
- **Neon scale-to-zero**: o banco "dorme" após ~5 min ocioso e acorda em ~1s na
  próxima query. Dados **nunca** são apagados (tier permanente).
- **750h/mês** de web service no Render cobrem 1 serviço 24/7 com folga.

---

## Atualizações futuras

Todo `git push` para a branch conectada dispara um novo build e deploy
automático, rodando as migrations pendentes. Fluxo normal:

```bash
git add .
git commit -m "feature X"
git push
```

---

## Notas / troubleshooting

- **Cookie de refresh**: em produção usa `Secure` (só HTTPS) + `SameSite=Lax`.
  Como frontend e API estão na **mesma origem**, funciona sem CORS. Se algum dia
  separar os domínios, aí sim precisaria `SameSite=None; Secure` + CORS com
  credenciais — não é o caso aqui.
- **DATABASE_URL sem `+psycopg`**: se esquecer de converter o esquema, o
  SQLAlchemy tenta o driver errado. Sempre `postgresql+psycopg://...`.
- **Migrations falhando no deploy**: veja os logs do serviço no Render; o passo
  `alembic upgrade head` roda no início do CMD e o log mostra o erro exato
  (quase sempre `DATABASE_URL` mal formado ou sem `sslmode=require`).
- **Trocar para pago depois**: se quiser matar o cold start, o plano Starter do
  web service (US$7/mês) remove a hibernação; o Neon pode seguir no free.
