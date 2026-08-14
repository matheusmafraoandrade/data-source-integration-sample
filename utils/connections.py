"""Cached connection helpers for BigQuery and HubSpot."""

from __future__ import annotations

import streamlit as st
from hubspot import HubSpot

# Service account fields stored flat under [connections.bigquery] in secrets.toml.
_SERVICE_ACCOUNT_FIELDS = (
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
)


def _build_service_account_info(section: dict) -> dict:
    """Build a Google service account payload from flat secrets fields."""
    credentials = {"type": "service_account"}
    for field in _SERVICE_ACCOUNT_FIELDS:
        value = section.get(field)
        if value:
            credentials[field] = value

    if not credentials.get("project_id"):
        raise ValueError("Missing BigQuery service account field: project_id")

    return credentials


@st.cache_resource(show_spinner=False)
def get_bigquery_connection():
    """Initialize and cache the native Streamlit BigQuery SQL connection."""
    try:
        if "connections" not in st.secrets or "bigquery" not in st.secrets.connections:
            raise KeyError("Missing [connections.bigquery] section in secrets.toml")

        bq_secrets = dict(st.secrets.connections.bigquery)
        credentials_info = _build_service_account_info(bq_secrets)
        project_id = credentials_info["project_id"]
        location = bq_secrets.get("location", "US")

        return st.connection(
            "bigquery",
            type="sql",
            url=f"bigquery://{project_id}",
            credentials_info=credentials_info,
            location=location,
        )
    except Exception as exc:
        st.cache_resource.clear()
        raise ConnectionError(f"Failed to initialize BigQuery connection: {exc}") from exc


@st.cache_resource(show_spinner=False)
def get_hubspot_client() -> HubSpot:
    """Initialize and cache an authenticated HubSpot CRM client."""
    try:
        if "hubspot" not in st.secrets:
            raise KeyError("Missing [hubspot] section in secrets.toml")

        token = st.secrets.hubspot.get("private_app_token")
        if not token or token.startswith("REPLACE_"):
            raise ValueError("HubSpot private_app_token is missing or still a placeholder")

        return HubSpot(access_token=token)
    except Exception as exc:
        st.cache_resource.clear()
        raise ConnectionError(f"Failed to initialize HubSpot client: {exc}") from exc


def get_bigquery_dataset() -> str:
    """Return the configured BigQuery dataset id."""
    if "bigquery" not in st.secrets:
        raise KeyError("Missing [bigquery] section in secrets.toml")

    dataset_id = st.secrets.bigquery.get("dataset_id")
    if not dataset_id or dataset_id.startswith("your-"):
        raise ValueError("bigquery.dataset_id is missing or still a placeholder")

    return dataset_id


def get_bigquery_project_id() -> str:
    """Return the GCP project id from the BigQuery connection secrets."""
    return st.secrets.connections.bigquery["project_id"]


def check_bigquery_connectivity() -> tuple[bool, str]:
    """Run a lightweight query to verify BigQuery connectivity."""
    try:
        conn = get_bigquery_connection()
        conn.query("SELECT 1 AS connectivity_check", ttl=60)
        return True, "Conectado"
    except Exception as exc:
        return False, str(exc)


def check_hubspot_connectivity() -> tuple[bool, str]:
    """Verify HubSpot credentials by fetching a single contact page."""
    try:
        client = get_hubspot_client()
        client.crm.contacts.basic_api.get_page(limit=1, properties=["email"])
        return True, "Conectado"
    except Exception as exc:
        return False, str(exc)
