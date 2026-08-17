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
from utils.ui_helpers import apply_presentation_style, presentation_lead

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

apply_presentation_style()

st.title("📈 Analytics — HubSpot × BigQuery")
presentation_lead(
    "Cruza <strong>negócios HubSpot</strong> com <strong>vendedores BigQuery</strong> "
    "via <code>dealname</code> = <code>seller_id</code>. "
    "Contatos associados são resolvidos via API de associações v4."
)

st.divider()

tab_orders, tab_gmv, tab_items, tab_conversion, tab_ltv = st.tabs(
    [
        "📅 Pedidos por Mês",
        "💰 GMV por Negócio",
        "📦 Itens Mais Pedidos",
        "🎯 Taxa de Conversão",
        "⭐ LTV",
    ]
)

with tab_orders:
    st.subheader("Pedidos por Mês")
    try:
        orders_month_df = get_orders_by_month().rename(
            columns={"mes": "Mês", "pedidos": "Pedidos"}
        )
        chart_df = orders_month_df.set_index("Mês")

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Total de pedidos", f"{int(orders_month_df['Pedidos'].sum()):,}")
        metric_col2.metric(
            "Média mensal",
            f"{orders_month_df['Pedidos'].mean():.1f}",
        )

        st.line_chart(chart_df["Pedidos"])
        st.dataframe(
            orders_month_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mês": st.column_config.TextColumn("Mês"),
                "Pedidos": st.column_config.NumberColumn("Pedidos", format="%d"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular pedidos por mês: {exc}")

with tab_gmv:
    st.subheader("GMV por Negócio")
    st.markdown(
        "Cada **negócio HubSpot** é cruzado com um **vendedor BigQuery** "
        "via `dealname` = `seller_id`."
    )
    try:
        gmv_df = get_gmv_by_deal()

        matched = gmv_df[gmv_df["seller_encontrado"]]
        with_gmv = gmv_df[gmv_df["gmv"] > 0]

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Negócios analisados", len(gmv_df))
        metric_col2.metric("Correspondências com BigQuery", len(matched))
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
                "id_negocio": st.column_config.TextColumn("ID do negócio"),
                "nome_do_negocio": st.column_config.TextColumn("Negócio"),
                "nome_do_contato": st.column_config.TextColumn("Contato"),
                "dealname_seller_id": st.column_config.TextColumn(
                    "Deal name → seller_id"
                ),
                "seller_id_bq": st.column_config.TextColumn("Seller ID (BigQuery)"),
                "seller_city": st.column_config.TextColumn("Cidade"),
                "seller_state": st.column_config.TextColumn("Estado"),
                "total_pedidos": st.column_config.NumberColumn("Pedidos"),
                "gmv": st.column_config.NumberColumn("GMV (R$)", format="R$ %.2f"),
                "seller_encontrado": st.column_config.CheckboxColumn("Match BigQuery"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular GMV por negócio: {exc}")

with tab_items:
    st.subheader("Itens com Mais Pedidos")
    try:
        top_n = st.slider("Top N produtos", min_value=5, max_value=50, value=20, step=5)
        items_df = get_top_order_items(limit=top_n)

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Produtos listados", len(items_df))
        metric_col2.metric(
            "Pedidos (1º colocado)",
            int(items_df.iloc[0]["total_pedidos"]) if not items_df.empty else 0,
        )

        st.bar_chart(items_df.set_index("product_id")["total_pedidos"])
        st.dataframe(
            items_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "product_id": st.column_config.TextColumn("ID do produto"),
                "product_category_name": st.column_config.TextColumn("Categoria"),
                "total_pedidos": st.column_config.NumberColumn("Pedidos"),
                "receita": st.column_config.NumberColumn("Receita (R$)", format="R$ %.2f"),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular itens com mais pedidos: {exc}")

with tab_conversion:
    st.subheader("Taxa de Conversão")
    st.markdown("Taxa principal: **negócios ÷ contatos** no HubSpot.")
    try:
        metrics = get_conversion_metrics()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total de contatos", f"{metrics['total_contacts']:,}")
        col2.metric("Total de negócios", f"{metrics['total_deals']:,}")
        col3.metric(
            "Taxa de conversão",
            f"{metrics['conversion_rate']:.2f}%",
            help="Total de negócios ÷ total de contatos × 100",
        )

        col4, col5, col6 = st.columns(3)
        col4.metric("Negócios → BigQuery", f"{metrics['deals_matched']:,}")
        col5.metric("Negócios com pedido", f"{metrics['deals_with_orders']:,}")
        col6.metric("Negócios ganhos", f"{metrics['deals_won']:,}")

        st.markdown("#### Funil Resumido")
        st.write(
            f"1. **{metrics['total_contacts']:,}** contatos no HubSpot  \n"
            f"2. **{metrics['total_deals']:,}** negócios "
            f"(**{metrics['conversion_rate']:.2f}%** de conversão)  \n"
            f"3. **{metrics['deals_matched']:,}** correspondências com BigQuery "
            f"(`dealname` = `seller_id`)  \n"
            f"4. **{metrics['deals_with_orders']:,}** com pedidos  \n"
            f"5. **{metrics['deals_won']:,}** negócios ganhos "
            f"({metrics['won_with_orders']:,} com pedidos)"
        )
        st.progress(min(int(metrics["conversion_rate"]), 100) / 100)
    except Exception as exc:
        st.error(f"Não foi possível calcular taxa de conversão: {exc}")

with tab_ltv:
    st.subheader("LTV — Valor Vitalício do Cliente")
    st.markdown(
        "LTV do **vendedor BigQuery** associado a cada negócio HubSpot "
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
                "seller_id_bq": st.column_config.TextColumn("Seller ID (BigQuery)"),
                "total_pedidos": st.column_config.NumberColumn("Pedidos"),
                "ltv": st.column_config.NumberColumn("LTV (R$)", format="R$ %.2f"),
                "ticket_medio": st.column_config.NumberColumn(
                    "Ticket médio (R$)", format="R$ %.2f"
                ),
            },
        )
    except Exception as exc:
        st.error(f"Não foi possível calcular LTV: {exc}")
