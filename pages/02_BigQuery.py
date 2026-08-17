"""BigQuery dashboard for e-commerce tables."""

import streamlit as st

from utils.bigquery_helpers import BIGQUERY_TABLES, get_table_row_count, query_bigquery_table
from utils.connections import get_bigquery_dataset, get_bigquery_project_id
from utils.ui_helpers import apply_presentation_style, presentation_lead, table_tab_label

st.set_page_config(page_title="BigQuery", page_icon="🗄️", layout="wide")

apply_presentation_style()

st.title("🗄️ BigQuery")

try:
    project_id = get_bigquery_project_id()
    dataset_id = get_bigquery_dataset()
    presentation_lead(
        f"Exploração das tabelas do dataset "
        f"<code>{project_id}.{dataset_id}</code>."
    )
except Exception as exc:
    st.error(f"Configuração BigQuery incompleta: {exc}")
    st.stop()

st.sidebar.markdown("### ⚙️ Visualização")
limit = st.sidebar.slider("Linhas por tabela", min_value=10, max_value=500, value=100, step=10)

st.divider()

tabs = st.tabs([table_tab_label(table) for table in BIGQUERY_TABLES])

for tab, table_name in zip(tabs, BIGQUERY_TABLES):
    with tab:
        try:
            label = table_tab_label(table_name)
            with st.spinner(f"Carregando {label}..."):
                row_count = get_table_row_count(table_name)
                df = query_bigquery_table(table_name, limit=limit)

            metric_col1, metric_col2 = st.columns(2)
            metric_col1.metric("Total de linhas", f"{row_count:,}")
            metric_col2.metric("Linhas exibidas", len(df))

            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Não foi possível carregar {table_tab_label(table_name)}: {exc}")
