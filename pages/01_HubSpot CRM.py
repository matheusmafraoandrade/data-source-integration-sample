"""HubSpot CRM dashboard with Contacts and Deals."""

import streamlit as st

from utils.hubspot_helpers import get_hubspot_contacts, get_hubspot_deals
from utils.ui_helpers import apply_presentation_style, presentation_lead

st.set_page_config(page_title="HubSpot CRM", page_icon="🏢", layout="wide")

apply_presentation_style()

st.title("🏢 HubSpot CRM")
presentation_lead(
    "Dados de <strong>contatos</strong> e <strong>negócios</strong> "
    "sincronizados do HubSpot CRM."
)

st.sidebar.markdown("### ⚙️ Carregamento")
fetch_mode = st.sidebar.radio(
    "Quantidade de registros",
    ["Prévia (100)", "Personalizado", "Todos"],
    help=(
        "A API do HubSpot retorna no máximo 100 registros por requisição. "
        "O app pagina automaticamente para buscar mais."
    ),
)

if fetch_mode == "Prévia (100)":
    max_records: int | None = 100
elif fetch_mode == "Personalizado":
    max_records = st.sidebar.number_input(
        "Máximo de registros",
        min_value=100,
        max_value=20000,
        value=500,
        step=100,
    )
else:
    max_records = None
    st.sidebar.info("Buscando todos os registros. A primeira carga pode demorar.")

st.divider()

contacts_tab, deals_tab = st.tabs(["👤 Contatos", "💼 Negócios"])

with contacts_tab:
    try:
        contacts_df = get_hubspot_contacts(max_records=max_records)

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Contatos carregados", len(contacts_df))
        metric_col2.metric(
            "Com origem",
            int(contacts_df["origin"].notna().sum()) if not contacts_df.empty else 0,
        )
        metric_col3.metric(
            "Com ID de landing page",
            int(contacts_df["landing_page_id"].notna().sum())
            if not contacts_df.empty
            else 0,
        )

        st.dataframe(
            contacts_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "nome": st.column_config.TextColumn("Nome"),
                "data_de_inicio": st.column_config.TextColumn("Data de início"),
                "landing_page_id": st.column_config.TextColumn("ID da landing page"),
                "origin": st.column_config.TextColumn("Origem"),
                "id_do_registro": st.column_config.TextColumn("ID do registro"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar contatos do HubSpot: {exc}")

with deals_tab:
    try:
        deals_df = get_hubspot_deals(max_records=max_records)

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Negócios carregados", len(deals_df))
        metric_col2.metric(
            "Com contato associado",
            int(deals_df["nome_do_contato"].notna().sum()) if not deals_df.empty else 0,
        )
        metric_col3.metric(
            "Com data de fechamento",
            int(deals_df["won_date"].notna().sum()) if not deals_df.empty else 0,
        )

        st.dataframe(
            deals_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "nome_do_negocio": st.column_config.TextColumn("Nome do negócio"),
                "lead_behavior_profile": st.column_config.TextColumn(
                    "Perfil de comportamento"
                ),
                "lead_type": st.column_config.TextColumn("Tipo de lead"),
                "sales_representative": st.column_config.TextColumn(
                    "Representante comercial"
                ),
                "sdr": st.column_config.TextColumn("SDR"),
                "won_date": st.column_config.TextColumn("Data de fechamento"),
                "nome_do_contato": st.column_config.TextColumn("Nome do contato"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível carregar negócios do HubSpot: {exc}")
