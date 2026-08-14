"""Main entry point for the multi-page Streamlit data integration app."""

import streamlit as st

from utils.connections import check_bigquery_connectivity, check_hubspot_connectivity

st.set_page_config(
    page_title="Data Integration Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Data Integration Hub")
st.markdown(
    """
    Painel central com integrações **HubSpot CRM** e **Google BigQuery**.
    Use a barra lateral para explorar os dashboards de cada fonte de dados.
    """
)

st.subheader("Status das conexões")

bq_ok, bq_message = check_bigquery_connectivity()
hs_ok, hs_message = check_hubspot_connectivity()

status_col1, status_col2 = st.columns(2)

with status_col1:
    st.metric(label="BigQuery", value="Online" if bq_ok else "Offline")
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
    ### Páginas disponíveis

    - **CRM Dashboard** — contatos e negócios do HubSpot
    - **BigQuery Dashboard** — tabelas do dataset configurado
    - **Analytics Dashboard** — visões cruzadas HubSpot × BigQuery
    """
)

if not bq_ok or not hs_ok:
    st.warning(
        "Uma ou mais integrações estão offline. Confira o guia de configuração "
        "no `README.md` e preencha `.streamlit/secrets.toml`."
    )
