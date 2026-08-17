"""Shared UI helpers for a consistent presentation-style Streamlit experience."""

from __future__ import annotations

import streamlit as st

BIGQUERY_TABLE_LABELS: dict[str, str] = {
    "customers": "Clientes",
    "geolocation": "Geolocalização",
    "order_items": "Itens do Pedido",
    "order_payments": "Pagamentos",
    "order_reviews": "Avaliações",
    "orders": "Pedidos",
    "product_category_name_translation": "Tradução de Categorias",
    "products": "Produtos",
    "sellers": "Vendedores",
}

PRESENTATION_CSS = """
<style>
    div[data-testid="stMetric"] label {
        font-size: 0.95rem;
        font-weight: 500;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 600;
    }
    .presentation-lead {
        font-size: 1.15rem;
        line-height: 1.6;
        color: rgba(49, 51, 63, 0.85);
        margin-bottom: 1.5rem;
    }
    .presentation-card-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
</style>
"""


def apply_presentation_style() -> None:
    """Inject global CSS for presentation-style typography and metrics."""
    st.markdown(PRESENTATION_CSS, unsafe_allow_html=True)


def presentation_lead(text: str) -> None:
    """Render a lead paragraph styled for presentation slides."""
    st.markdown(f'<p class="presentation-lead">{text}</p>', unsafe_allow_html=True)


def table_tab_label(table_name: str) -> str:
    """Return a human-readable Portuguese label for a BigQuery table tab."""
    return BIGQUERY_TABLE_LABELS.get(table_name, table_name.replace("_", " ").title())
