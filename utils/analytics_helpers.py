"""Cross-source analytics combining HubSpot CRM and BigQuery e-commerce data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.bigquery_helpers import run_bigquery_sql, table_fqn
from utils.hubspot_helpers import get_hubspot_contacts, get_hubspot_deals_for_analytics


def _safe_str(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_lookup(df: pd.DataFrame, key: str) -> dict:
    """Build a lookup dict from a dataframe keyed by a column."""
    if key not in df.columns or df.empty:
        return {}
    normalized = df.drop_duplicates(subset=[key], keep="first").copy()
    normalized[key] = normalized[key].astype(str)
    return normalized.set_index(key).to_dict("index")


def _resolve_seller_id(deal: pd.Series) -> str | None:
    """Map HubSpot dealname to BigQuery seller_id."""
    deal_name = _safe_str(deal.get("nome_do_negocio"))
    return deal_name or None


@st.cache_data(ttl=600, show_spinner="Calculando pedidos por mês...")
def get_orders_by_month() -> pd.DataFrame:
    """Return monthly order counts from BigQuery."""
    orders = table_fqn("orders")
    sql = f"""
        SELECT
            FORMAT_DATE('%Y-%m', DATE(order_purchase_timestamp)) AS mes,
            COUNT(DISTINCT order_id) AS pedidos
        FROM {orders}
        WHERE order_purchase_timestamp IS NOT NULL
        GROUP BY mes
        ORDER BY mes
    """
    return run_bigquery_sql(sql)


@st.cache_data(ttl=600, show_spinner="Carregando sellers do BigQuery...")
def get_bigquery_sellers() -> pd.DataFrame:
    """Return BigQuery sellers."""
    sellers = table_fqn("sellers")
    return run_bigquery_sql(f"SELECT * FROM {sellers}")


@st.cache_data(ttl=600, show_spinner="Calculando GMV por seller...")
def get_seller_gmv() -> pd.DataFrame:
    """Return GMV and order counts per BigQuery seller."""
    order_items = table_fqn("order_items")
    sellers = table_fqn("sellers")

    sql = f"""
        SELECT
            oi.seller_id,
            s.seller_city,
            s.seller_state,
            COUNT(DISTINCT oi.order_id) AS total_pedidos,
            SUM(oi.price + oi.freight_value) AS gmv
        FROM {order_items} AS oi
        INNER JOIN {sellers} AS s
            ON oi.seller_id = s.seller_id
        GROUP BY oi.seller_id, s.seller_city, s.seller_state
    """
    return run_bigquery_sql(sql)


@st.cache_data(ttl=600, show_spinner="Cruzando negócios HubSpot com sellers...")
def cross_deals_with_sellers() -> pd.DataFrame:
    """Join HubSpot deals with BigQuery sellers and seller GMV."""
    deals = get_hubspot_deals_for_analytics(max_records=None)
    seller_gmv = get_seller_gmv()
    by_seller_id = _as_lookup(seller_gmv, "seller_id")

    rows = []
    for _, deal in deals.iterrows():
        resolved_seller_id = _resolve_seller_id(deal)
        seller_match = by_seller_id.get(resolved_seller_id) if resolved_seller_id else None

        row = deal.to_dict()
        row["dealname_seller_id"] = resolved_seller_id
        if seller_match:
            row.update(
                {
                    "seller_id_bq": seller_match.get("seller_id"),
                    "seller_city": seller_match.get("seller_city"),
                    "seller_state": seller_match.get("seller_state"),
                    "total_pedidos": int(seller_match.get("total_pedidos", 0) or 0),
                    "gmv": float(seller_match.get("gmv", 0) or 0),
                    "seller_encontrado": True,
                }
            )
        else:
            row.update(
                {
                    "seller_id_bq": None,
                    "seller_city": None,
                    "seller_state": None,
                    "total_pedidos": 0,
                    "gmv": 0.0,
                    "seller_encontrado": False,
                }
            )
        rows.append(row)

    return pd.DataFrame(rows)


@st.cache_data(ttl=600, show_spinner="Calculando GMV por negócio...")
def get_gmv_by_deal() -> pd.DataFrame:
    """Return GMV per HubSpot deal matched to a BigQuery seller."""
    crossed = cross_deals_with_sellers()
    return crossed[
        [
            "id_negocio",
            "nome_do_negocio",
            "nome_do_contato",
            "dealname_seller_id",
            "seller_id_bq",
            "seller_city",
            "seller_state",
            "total_pedidos",
            "gmv",
            "seller_encontrado",
        ]
    ].sort_values("gmv", ascending=False)


@st.cache_data(ttl=600, show_spinner="Calculando itens mais pedidos...")
def get_top_order_items(limit: int = 20) -> pd.DataFrame:
    """Return products ranked by distinct order count."""
    order_items = table_fqn("order_items")
    products = table_fqn("products")

    sql = f"""
        SELECT
            oi.product_id,
            p.product_category_name,
            COUNT(DISTINCT oi.order_id) AS total_pedidos,
            SUM(oi.price + oi.freight_value) AS receita
        FROM {order_items} AS oi
        LEFT JOIN {products} AS p
            ON oi.product_id = p.product_id
        GROUP BY oi.product_id, p.product_category_name
        ORDER BY total_pedidos DESC
        LIMIT {int(limit)}
    """
    return run_bigquery_sql(sql)


@st.cache_data(ttl=600, show_spinner="Calculando taxa de conversão...")
def get_conversion_metrics() -> dict[str, float | int]:
    """Compute conversion rate as deals / contacts."""
    crossed = cross_deals_with_sellers()
    total_contacts = len(get_hubspot_contacts(max_records=None))
    total_deals = len(crossed)

    deals_matched = int(crossed["seller_encontrado"].sum())
    deals_with_orders = int((crossed["total_pedidos"] > 0).sum())
    deals_won = int(crossed["won_date"].notna().sum()) if not crossed.empty else 0
    won_with_orders = int(
        ((crossed["won_date"].notna()) & (crossed["total_pedidos"] > 0)).sum()
    )
    contacts_with_deal = int(
        ((crossed["nome_do_contato"].notna()) & (crossed["nome_do_contato"] != "—")).sum()
    )

    conversion_rate = (total_deals / total_contacts) * 100 if total_contacts else 0.0
    deal_to_seller_rate = (deals_matched / total_deals) * 100 if total_deals else 0.0

    return {
        "total_contacts": total_contacts,
        "total_deals": total_deals,
        "conversion_rate": conversion_rate,
        "deals_matched": deals_matched,
        "deals_with_orders": deals_with_orders,
        "deals_won": deals_won,
        "won_with_orders": won_with_orders,
        "contacts_with_deal": contacts_with_deal,
        "deal_to_seller_rate": deal_to_seller_rate,
    }


@st.cache_data(ttl=600, show_spinner="Calculando LTV...")
def get_ltv_by_deal() -> pd.DataFrame:
    """Return LTV (seller GMV) per HubSpot deal."""
    crossed = cross_deals_with_sellers()
    ltv = crossed[crossed["seller_encontrado"]].copy()
    ltv = ltv.rename(columns={"gmv": "ltv"})
    ltv["ticket_medio"] = ltv.apply(
        lambda row: row["ltv"] / row["total_pedidos"] if row["total_pedidos"] else 0.0,
        axis=1,
    )
    return ltv.sort_values("ltv", ascending=False)


@st.cache_data(ttl=600, show_spinner=False)
def get_ltv_summary() -> dict[str, float | int]:
    """Return aggregate LTV statistics for matched deals."""
    ltv_df = get_ltv_by_deal()
    paying = ltv_df[ltv_df["ltv"] > 0]

    if paying.empty:
        return {
            "ltv_medio": 0.0,
            "ltv_mediano": 0.0,
            "ltv_maximo": 0.0,
            "negocios_pagantes": 0,
        }

    return {
        "ltv_medio": float(paying["ltv"].mean()),
        "ltv_mediano": float(paying["ltv"].median()),
        "ltv_maximo": float(paying["ltv"].max()),
        "negocios_pagantes": int(len(paying)),
    }
