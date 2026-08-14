"""BigQuery dashboard for e-commerce tables."""

import streamlit as st

from utils.bigquery_helpers import BIGQUERY_TABLES, get_table_row_count, query_bigquery_table
from utils.connections import get_bigquery_dataset, get_bigquery_project_id

st.set_page_config(page_title="BigQuery Dashboard", page_icon="🗄️", layout="wide")

st.title("BigQuery Dashboard")

try:
    project_id = get_bigquery_project_id()
    dataset_id = get_bigquery_dataset()
    st.caption(f"Dataset: `{project_id}.{dataset_id}`")
except Exception as exc:
    st.error(f"Configuração BigQuery incompleta: {exc}")
    st.stop()

limit = st.sidebar.slider("Linhas por tabela", min_value=10, max_value=500, value=100, step=10)

tabs = st.tabs([table.replace("_", " ").title() for table in BIGQUERY_TABLES])

for tab, table_name in zip(tabs, BIGQUERY_TABLES):
    with tab:
        try:
            with st.spinner(f"Carregando `{table_name}`..."):
                row_count = get_table_row_count(table_name)
                df = query_bigquery_table(table_name, limit=limit)

            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric("Total de linhas", f"{row_count:,}")
            metric_col2.metric("Exibindo", len(df))

            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Não foi possível carregar `{table_name}`: {exc}")
