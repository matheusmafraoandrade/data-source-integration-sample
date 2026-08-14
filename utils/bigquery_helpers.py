"""Cached BigQuery query helpers for e-commerce tables."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.connections import (
    get_bigquery_connection,
    get_bigquery_dataset,
    get_bigquery_project_id,
)

BIGQUERY_TABLES = (
    "customers",
    "geolocation",
    "order_items",
    "order_payments",
    "order_reviews",
    "orders",
    "product_category_name_translation",
    "products",
    "sellers",
)


def _table_fqn(table_name: str) -> str:
    """Build a fully qualified BigQuery table reference."""
    if table_name not in BIGQUERY_TABLES:
        raise ValueError(f"Unsupported table: {table_name}")

    project_id = get_bigquery_project_id()
    dataset_id = get_bigquery_dataset()
    return f"`{project_id}.{dataset_id}.{table_name}`"


def table_fqn(table_name: str) -> str:
    """Public helper for fully qualified BigQuery table names."""
    return _table_fqn(table_name)


@st.cache_data(ttl=600, show_spinner=False)
def run_bigquery_sql(sql: str) -> pd.DataFrame:
    """Execute a SQL query against the configured BigQuery connection."""
    conn = get_bigquery_connection()
    return conn.query(sql, ttl=600)


@st.cache_data(ttl=600, show_spinner=False)
def query_bigquery_table(table_name: str, limit: int = 100) -> pd.DataFrame:
    """Run a SELECT * query against a configured BigQuery table."""
    conn = get_bigquery_connection()
    fqn = _table_fqn(table_name)
    sql = f"SELECT * FROM {fqn} LIMIT {int(limit)}"
    return conn.query(sql, ttl=600)


@st.cache_data(ttl=600, show_spinner=False)
def get_table_row_count(table_name: str) -> int:
    """Return the total row count for a BigQuery table."""
    conn = get_bigquery_connection()
    fqn = _table_fqn(table_name)
    sql = f"SELECT COUNT(*) AS total FROM {fqn}"
    result = conn.query(sql, ttl=600)
    return int(result.iloc[0, 0])
