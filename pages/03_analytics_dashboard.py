"""Cross-source analytics dashboard for HubSpot + BigQuery."""

import streamlit as st

from utils.analytics_helpers import (
    get_conversion_metrics,
    get_gmv_by_deal,
    get_ltv_by_deal,
    get_ltv_summary,
    get_orders_by_month,
    get_top_order_items,
)

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("Analytics — HubSpot × BigQuery")
st.caption(
    "Cruza **negócios HubSpot** com **sellers BigQuery** via `dealname` = `seller_id`. "
    "Contatos associados são resolvidos via API de associações v4."
)

tab_orders, tab_gmv, tab_items, tab_conversion, tab_ltv = st.tabs(
    [
        "Pedidos por mês",
        "GMV por negócio",
        "Itens com mais pedidos",
        "Taxa de conversão",
        "LTV",
    ]
)

with tab_orders:
    st.subheader("Pedidos por mês")
    try:
        orders_month_df = get_orders_by_month()
        chart_df = orders_month_df.set_index("mes")

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Total de pedidos", f"{int(orders_month_df['pedidos'].sum()):,}")
        metric_col2.metric(
            "Média mensal",
            f"{orders_month_df['pedidos'].mean():.1f}",
        )

        st.line_chart(chart_df["pedidos"])
        st.dataframe(orders_month_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"Não foi possível calcular pedidos por mês: {exc}")

with tab_gmv:
    st.subheader("GMV por negócio")
    st.markdown(
        "Cada **negócio HubSpot** é cruzado com um **seller BigQuery** "
        "via `dealname` = `seller_id`."
    )
    try:
        gmv_df = get_gmv_by_deal()

        matched = gmv_df[gmv_df["seller_encontrado"]]
        with_gmv = gmv_df[gmv_df["gmv"] > 0]

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Negócios analisados", len(gmv_df))
        metric_col2.metric("Matches com seller BQ", len(matched))
        metric_col3.metric("GMV total", f"R$ {with_gmv['gmv'].sum():,.2f}")

        if not with_gmv.empty:
            st.bar_chart(
                with_gmv.set_index("nome_do_negocio")["gmv"].head(20)
            )

        st.dataframe(
            gmv_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "nome_do_negocio": st.column_config.TextColumn("Negócio"),
                "nome_do_contato": st.column_config.TextColumn("Contato"),
                "dealname_seller_id": st.column_config.TextColumn("Deal name → seller_id"),
                "seller_id_bq": st.column_config.TextColumn("Seller ID (BQ)"),
                "seller_city": st.column_config.TextColumn("Cidade"),
                "seller_state": st.column_config.TextColumn("Estado"),
                "total_pedidos": st.column_config.NumberColumn("Pedidos"),
                "gmv": st.column_config.NumberColumn("GMV (R$)", format="R$ %.2f"),
                "seller_encontrado": st.column_config.CheckboxColumn("Match BQ"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular GMV por negócio: {exc}")

with tab_items:
    st.subheader("Itens com mais pedidos")
    try:
        top_n = st.slider("Top N produtos", min_value=5, max_value=50, value=20, step=5)
        items_df = get_top_order_items(limit=top_n)

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Produtos listados", len(items_df))
        metric_col2.metric(
            "Pedidos (top 1)",
            int(items_df.iloc[0]["total_pedidos"]) if not items_df.empty else 0,
        )

        st.bar_chart(items_df.set_index("product_id")["total_pedidos"])
        st.dataframe(
            items_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_id": st.column_config.TextColumn("Product ID"),
                "product_category_name": st.column_config.TextColumn("Categoria"),
                "total_pedidos": st.column_config.NumberColumn("Pedidos"),
                "receita": st.column_config.NumberColumn("Receita (R$)", format="R$ %.2f"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular itens com mais pedidos: {exc}")

with tab_conversion:
    st.subheader("Taxa de conversão")
    st.markdown("Taxa principal: **negócios / contatos** no HubSpot.")
    try:
        metrics = get_conversion_metrics()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de contatos", f"{metrics['total_contacts']:,}")
        col2.metric("Total de negócios", f"{metrics['total_deals']:,}")
        col3.metric(
            "Conversão (deals / contacts)",
            f"{metrics['conversion_rate']:.2f}%",
            help="Total de negócios ÷ total de contatos × 100",
        )

        col4, col5, col6 = st.columns(3)
        col4.metric("Deals → Seller BQ", f"{metrics['deals_matched']:,}")
        col5.metric("Deals com pedido", f"{metrics['deals_with_orders']:,}")
        col6.metric("Negócios ganhos", f"{metrics['deals_won']:,}")

        st.markdown("#### Funil resumido")
        st.write(
            f"1. **{metrics['total_contacts']:,}** contatos no HubSpot  \n"
            f"2. **{metrics['total_deals']:,}** negócios (**{metrics['conversion_rate']:.2f}%** conversão)  \n"
            f"3. **{metrics['deals_matched']:,}** matched com seller BQ (`dealname` = `seller_id`)  \n"
            f"4. **{metrics['deals_with_orders']:,}** com pedidos  \n"
            f"5. **{metrics['deals_won']:,}** negócios ganhos "
            f"({metrics['won_with_orders']:,} com pedidos)"
        )
        st.progress(min(int(metrics["conversion_rate"]), 100) / 100)
    except Exception as exc:
        st.error(f"Não foi possível calcular taxa de conversão: {exc}")

with tab_ltv:
    st.subheader("LTV — Lifetime Value")
    st.markdown(
        "LTV do **seller BigQuery** associado a cada negócio HubSpot "
        "(soma de receita em `order_items`)."
    )
    try:
        ltv_df = get_ltv_by_deal()
        summary = get_ltv_summary()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("LTV médio", f"R$ {summary['ltv_medio']:,.2f}")
        col2.metric("LTV mediano", f"R$ {summary['ltv_mediano']:,.2f}")
        col3.metric("LTV máximo", f"R$ {summary['ltv_maximo']:,.2f}")
        col4.metric("Negócios pagantes", f"{summary['negocios_pagantes']:,}")

        paying = ltv_df[ltv_df["ltv"] > 0]
        if not paying.empty:
            st.bar_chart(paying.set_index("nome_do_negocio")["ltv"].head(20))

        st.dataframe(
            ltv_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "nome_do_negocio": st.column_config.TextColumn("Negócio"),
                "nome_do_contato": st.column_config.TextColumn("Contato"),
                "seller_id_bq": st.column_config.TextColumn("Seller ID (BQ)"),
                "total_pedidos": st.column_config.NumberColumn("Pedidos"),
                "ltv": st.column_config.NumberColumn("LTV (R$)", format="R$ %.2f"),
                "ticket_medio": st.column_config.NumberColumn(
                    "Ticket médio (R$)", format="R$ %.2f"
                ),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular LTV: {exc}")
