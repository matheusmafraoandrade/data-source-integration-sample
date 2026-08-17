"""Main entry point for the multi-page Streamlit data integration app."""

import streamlit as st

from utils.connections import check_bigquery_connectivity, check_hubspot_connectivity
from utils.ui_helpers import apply_presentation_style, presentation_lead

st.set_page_config(
    page_title="Hub de Integração de Dados",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_presentation_style()

st.title("📊 Hub de Integração de Dados")
presentation_lead(
    "Painel central com integrações <strong>HubSpot CRM</strong> e "
    "<strong>Google BigQuery</strong>. "
    "Use a barra lateral para explorar os dashboards de cada fonte de dados."
)

st.divider()

st.subheader("Status das Conexões")

bq_ok, bq_message = check_bigquery_connectivity()
hs_ok, hs_message = check_hubspot_connectivity()

status_col1, status_col2 = st.columns(2)

with status_col1:
    st.metric(label="Google BigQuery", value="Online" if bq_ok else "Offline")
    if bq_ok:
        st.caption(bq_message)
    else:
        st.error(bq_message)

with status_col2:
    st.metric(label="HubSpot CRM", value="Online" if hs_ok else "Offline")
    if hs_ok:
        st.caption(hs_message)
    else:
        st.error(hs_message)

st.divider()

st.markdown(
    """
    ### Páginas Disponíveis

    | Dashboard | Descrição |
    |---|---|
    | **HubSpot CRM** | Contatos e negócios do HubSpot |
    | **BigQuery** | Tabelas do dataset configurado |
    | **Analytics** | Visões cruzadas HubSpot × BigQuery |
    """
)

if not bq_ok or not hs_ok:
    st.warning(
        "Uma ou mais integrações estão offline. Confira o guia de configuração "
        "no `README.md` e preencha `.streamlit/secrets.toml`."
    )
