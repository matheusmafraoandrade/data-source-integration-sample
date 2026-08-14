# Data Source Integration Sample

Template modular multi-página em Streamlit para integrar **HubSpot CRM** e **Google BigQuery**.

## O que o app faz

- **HubSpot:** lista contatos e negócios (Contacts + Deals)
- **BigQuery:** consulta as tabelas:
  - `customers`
  - `order_items`
  - `order_payments`
  - `order_reviews`
  - `orders`
  - `sellers`

## Estrutura do projeto

```text
.
├── app.py                        # Página inicial + status das conexões
├── pages/
│   ├── 01_crm_dashboard.py       # HubSpot Contacts / Deals
│   └── 02_bigquery_dashboard.py  # Tabelas BigQuery
├── utils/
│   ├── connections.py            # Conexões cacheadas
│   ├── hubspot_helpers.py        # Fetch HubSpot
│   └── bigquery_helpers.py       # Queries BigQuery
├── .streamlit/secrets.toml       # Credenciais (não commitar)
└── requirements.txt
```

---

## Passo a passo — Google Cloud (BigQuery)

### 1. Criar ou escolher um projeto GCP

1. Acesse [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto ou selecione um existente.
3. Anote o **Project ID** (ex.: `meu-projeto-analytics`).

### 2. Ativar a BigQuery API

1. Vá em **APIs & Services → Library**.
2. Busque **BigQuery API**.
3. Clique em **Enable**.

### 3. Garantir que suas tabelas existem

No [BigQuery Studio](https://console.cloud.google.com/bigquery), confirme que o dataset contém:

```text
<project_id>.<dataset_id>.customers
<project_id>.<dataset_id>.order_items
<project_id>.<dataset_id>.order_payments
<project_id>.<dataset_id>.order_reviews
<project_id>.<dataset_id>.orders
<project_id>.<dataset_id>.sellers
```

Anote o **dataset_id** (ex.: `ecommerce`, `raw`, `olist`).

### 4. Criar uma Service Account

1. Vá em **IAM & Admin → Service Accounts**.
2. Clique em **Create Service Account**.
3. Nome sugerido: `streamlit-bigquery-reader`.
4. Conceda estas roles:
   - `BigQuery Data Viewer` — ler tabelas
   - `BigQuery Job User` — executar queries
5. Finalize a criação.

### 5. Gerar a chave JSON

1. Abra a service account criada.
2. Aba **Keys → Add Key → Create new key → JSON**.
3. Baixe o arquivo `.json`.

### 6. Mapear no `secrets.toml`

Abra o JSON e copie os campos para `.streamlit/secrets.toml`:

```toml
[connections.bigquery]
type = "sql"
dialect = "bigquery"
location = "US"   # ajuste se seu dataset estiver em outra região (ex.: "southamerica-east1")

project_id = "meu-projeto-analytics"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "streamlit-bigquery-reader@meu-projeto-analytics.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

[bigquery]
dataset_id = "seu-dataset-id"
```

> **Dica:** no JSON, o `private_key` vem com `\n`. No TOML, mantenha as quebras de linha como `\n` dentro das aspas.

### 7. Testar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Na página inicial, **BigQuery** deve aparecer como **Online**. Depois abra **BigQuery Dashboard** e confira as tabelas.

---

## Passo a passo — HubSpot

### 1. Acessar Private Apps

1. Entre no [HubSpot](https://app.hubspot.com/).
2. Vá em **Settings (⚙️) → Integrations → Private Apps**.

> Se não vir a opção, sua conta pode precisar de permissão de super admin.

### 2. Criar um Private App

1. Clique em **Create a private app**.
2. Nome sugerido: `Streamlit CRM Reader`.
3. Na aba **Scopes**, marque pelo menos:
   - `crm.objects.contacts.read`
   - `crm.objects.deals.read`
4. Salve e **Create app**.

### 3. Copiar o token

1. Após criar, copie o **Access token** (formato `pat-...`).
2. Cole em `.streamlit/secrets.toml`:

```toml
[hubspot]
private_app_token = "pat-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 4. Validar

Reinicie o app. Na página inicial, **HubSpot CRM** deve ficar **Online**. Abra **CRM Dashboard** para ver contatos e negócios.

---

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy no Streamlit Community Cloud

1. Suba o código para o GitHub (sem o `secrets.toml` real).
2. Crie o app em [share.streamlit.io](https://share.streamlit.io/) apontando para `app.py`.
3. Em **Settings → Secrets**, cole o conteúdo completo do seu `secrets.toml`.
4. Salve e aguarde o redeploy.

---

## Checklist rápido

**Google Cloud**
- [ ] Projeto GCP criado
- [ ] BigQuery API ativada
- [ ] Dataset com as 6 tabelas disponível
- [ ] Service account com `BigQuery Data Viewer` + `BigQuery Job User`
- [ ] Chave JSON mapeada em `[connections.bigquery]`
- [ ] `dataset_id` preenchido em `[bigquery]`

**HubSpot**
- [ ] Private App criado
- [ ] Scopes de leitura de contacts e deals
- [ ] Token `pat-...` em `[hubspot]`

**App**
- [ ] `pip install -r requirements.txt`
- [ ] `streamlit run app.py`
- [ ] Status Online na home
- [ ] Dados visíveis nos dashboards

---

## Segurança

- Nunca commite `.streamlit/secrets.toml`.
- Use tokens HubSpot somente com escopo de leitura.
- Restrinja a service account ao dataset necessário.
- Revogue e recrie chaves/tokens se forem expostos acidentalmente.
