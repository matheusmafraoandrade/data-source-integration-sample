"""Cached HubSpot CRM data helpers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import streamlit as st
from hubspot.crm.associations.v4 import (
    BatchInputPublicFetchAssociationsBatchRequest,
    PublicFetchAssociationsBatchRequest,
)
from hubspot.crm.contacts import BatchReadInputSimplePublicObjectId, SimplePublicObjectId
from hubspot.crm.contacts.exceptions import ApiException as ContactsApiException
from hubspot.crm.deals.exceptions import ApiException as DealsApiException

from utils.connections import get_hubspot_client

HUBSPOT_PAGE_SIZE = 100

CONTACT_PROPERTIES = [
    "name",
    "firstname",
    "lastname",
    "email",
    "data_de_inicio",
    "createdate",
    "landing_page_id",
    "origin",
]

DEAL_PROPERTIES = [
    "dealname",
    "contact_name",
    "lead_behavior_profile",
    "lead_type",
    "sales_representative",
    "sdr",
    "won_date",
    "closedate",
    "seller_id",
]


def _safe_str(value: object) -> str:
    """Coerce nullable HubSpot property values to a trimmed string."""
    if value is None:
        return ""
    return str(value).strip()


def _contact_display_name(properties: dict) -> str:
    name = _safe_str(properties.get("name"))
    if name:
        return name

    first = _safe_str(properties.get("firstname"))
    last = _safe_str(properties.get("lastname"))
    full_name = f"{first} {last}".strip()
    return full_name or _safe_str(properties.get("email")) or "—"


def _resolve_deal_contact_name(contact: dict[str, str | None], deal_properties: dict) -> str:
    """Resolve contact name from associated contact or deal property."""
    contact_name = _safe_str(contact.get("nome"))
    if contact_name and contact_name != "—":
        return contact_name

    deal_contact_name = _safe_str(deal_properties.get("contact_name"))
    if deal_contact_name:
        return deal_contact_name

    return "—"


def _format_hubspot_date(value: object) -> str | None:
    """Normalize HubSpot date values to YYYY-MM-DD."""
    if value in (None, ""):
        return None

    text = str(value).strip()
    if text.isdigit():
        timestamp = int(text) / 1000
        return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d")

    try:
        return pd.to_datetime(text, utc=True).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return text or None


def _fetch_paginated(
    fetch_page: Callable[..., Any],
    *,
    properties: list[str],
    max_records: int | None,
    extra_kwargs: dict[str, Any] | None = None,
) -> list[Any]:
    """Fetch HubSpot records across all API pages (100 records per page)."""
    results: list[Any] = []
    after: str | None = None
    extra_kwargs = extra_kwargs or {}

    while True:
        page_limit = HUBSPOT_PAGE_SIZE
        if max_records is not None:
            remaining = max_records - len(results)
            if remaining <= 0:
                break
            page_limit = min(HUBSPOT_PAGE_SIZE, remaining)

        response = fetch_page(
            limit=page_limit,
            archived=False,
            properties=properties,
            after=after,
            **extra_kwargs,
        )
        results.extend(response.results)

        paging = getattr(response, "paging", None)
        next_page = getattr(paging, "next", None) if paging else None
        after = getattr(next_page, "after", None) if next_page else None

        if not after:
            break

    return results


def _fetch_deal_to_contact_map(client: Any, deal_ids: list[str]) -> dict[str, str]:
    """Batch-fetch associated contact ids for each deal."""
    mapping: dict[str, str] = {}

    for start in range(0, len(deal_ids), HUBSPOT_PAGE_SIZE):
        chunk = deal_ids[start : start + HUBSPOT_PAGE_SIZE]
        batch_input = BatchInputPublicFetchAssociationsBatchRequest(
            inputs=[PublicFetchAssociationsBatchRequest(id=deal_id) for deal_id in chunk]
        )
        response = client.crm.associations.v4.batch_api.get_page(
            from_object_type="deals",
            to_object_type="contacts",
            batch_input_public_fetch_associations_batch_request=batch_input,
        )

        for result in response.results or []:
            deal_id = result._from.id
            associated_contacts = result.to or []
            if associated_contacts:
                mapping[deal_id] = associated_contacts[0].to_object_id

    return mapping


def _fetch_contact_details(client: Any, contact_ids: set[str]) -> dict[str, dict[str, str | None]]:
    """Batch-resolve contact ids to display name and email."""
    if not contact_ids:
        return {}

    details: dict[str, dict[str, str | None]] = {}
    ids_list = sorted(contact_ids)

    for start in range(0, len(ids_list), HUBSPOT_PAGE_SIZE):
        chunk = ids_list[start : start + HUBSPOT_PAGE_SIZE]
        batch_input = BatchReadInputSimplePublicObjectId(
            properties=["name", "firstname", "lastname", "email"],
            inputs=[SimplePublicObjectId(id=contact_id) for contact_id in chunk],
        )
        response = client.crm.contacts.batch_api.read(
            batch_read_input_simple_public_object_id=batch_input
        )

        for contact in response.results:
            properties = contact.properties or {}
            email = _safe_str(properties.get("email")).lower() or None
            details[contact.id] = {
                "nome": _contact_display_name(properties),
                "email": email,
            }

    return details


def _load_deals_dataframe(max_records: int | None) -> pd.DataFrame:
    """Load deals with associated contact names resolved from associations v4."""
    client = get_hubspot_client()
    deals = _fetch_paginated(
        client.crm.deals.basic_api.get_page,
        properties=DEAL_PROPERTIES,
        max_records=max_records,
    )

    deal_ids = [deal.id for deal in deals]
    deal_to_contact = _fetch_deal_to_contact_map(client, deal_ids)
    contact_details = _fetch_contact_details(client, set(deal_to_contact.values()))

    rows = []
    for deal in deals:
        properties = deal.properties or {}
        contact_id = deal_to_contact.get(deal.id)
        contact = contact_details.get(contact_id, {}) if contact_id else {}

        rows.append(
            {
                "id_negocio": deal.id,
                "nome_do_negocio": properties.get("dealname"),
                "nome_do_contato": _resolve_deal_contact_name(contact, properties),
                "email_contato": contact.get("email"),
                "seller_id": _safe_str(properties.get("seller_id")) or None,
                "won_date": _format_hubspot_date(
                    properties.get("won_date") or properties.get("closedate")
                ),
                "lead_type": properties.get("lead_type"),
                "lead_behavior_profile": properties.get("lead_behavior_profile"),
                "sales_representative": properties.get("sales_representative"),
                "sdr": properties.get("sdr"),
            }
        )

    return pd.DataFrame(rows)


@st.cache_data(ttl=300, show_spinner="Carregando contatos do HubSpot...")
def get_hubspot_contacts(max_records: int | None = 100) -> pd.DataFrame:
    """Fetch HubSpot contacts with automatic pagination."""
    try:
        client = get_hubspot_client()
        contacts = _fetch_paginated(
            client.crm.contacts.basic_api.get_page,
            properties=CONTACT_PROPERTIES,
            max_records=max_records,
        )

        rows = []
        for contact in contacts:
            properties = contact.properties or {}
            rows.append(
                {
                    "nome": _contact_display_name(properties),
                    "data_de_inicio": _format_hubspot_date(
                        properties.get("data_de_inicio") or properties.get("createdate")
                    ),
                    "landing_page_id": properties.get("landing_page_id"),
                    "origin": properties.get("origin"),
                    "id_do_registro": contact.id,
                }
            )

        return pd.DataFrame(
            rows,
            columns=[
                "nome",
                "data_de_inicio",
                "landing_page_id",
                "origin",
                "id_do_registro",
            ],
        )
    except ContactsApiException as exc:
        raise RuntimeError(f"HubSpot Contacts API error: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch HubSpot contacts: {exc}") from exc


@st.cache_data(ttl=300, show_spinner="Carregando negócios do HubSpot...")
def get_hubspot_deals(max_records: int | None = 100) -> pd.DataFrame:
    """Fetch HubSpot deals with associated contact names."""
    try:
        deals_df = _load_deals_dataframe(max_records)
        return deals_df[
            [
                "nome_do_negocio",
                "lead_behavior_profile",
                "lead_type",
                "sales_representative",
                "sdr",
                "won_date",
                "nome_do_contato",
            ]
        ]
    except DealsApiException as exc:
        raise RuntimeError(f"HubSpot Deals API error: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch HubSpot deals: {exc}") from exc


@st.cache_data(ttl=300, show_spinner="Carregando negócios para análise...")
def get_hubspot_deals_for_analytics(max_records: int | None = None) -> pd.DataFrame:
    """Fetch HubSpot deals with seller linkage fields for BigQuery joins."""
    try:
        return _load_deals_dataframe(max_records)
    except DealsApiException as exc:
        raise RuntimeError(f"HubSpot Deals API error: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch HubSpot deals for analytics: {exc}") from exc
