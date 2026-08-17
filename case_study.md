# HubSpot + BigQuery Integration — Live CRM & Warehouse Dashboard (Case Study)

**The problem**

A growing SaaS or ecommerce team often has customer and deal data sitting in a CRM (HubSpot) and transactional data sitting in a data warehouse (BigQuery) — two systems, two logins, no shared view. Sales sees pipeline. Ops sees orders. Nobody sees both without exporting each to a spreadsheet and lining them up by hand.

**What this project does**

A modular Streamlit app connects directly to both systems live — no CSV exports, no manual refresh. One page pulls Contacts and Deals straight from HubSpot; another queries core ecommerce tables (customers, orders, order items, payments, reviews, sellers) straight from BigQuery. Connections are cached for performance, credentials are kept out of the codebase, and the setup is documented step-by-step so the client's team can reconnect it to their own accounts in under 30 minutes.

**What this demonstrates**

- Live API integration (not just static file cleaning)
- Secure credential handling, kept out of the codebase
- Multi-source architecture — CRM and data warehouse in one interface
- Documentation clear enough for a non-author to deploy it

**Stack**

Python, Streamlit, HubSpot API, Google BigQuery

---

*See `README.md` in this repo for setup instructions and technical details.*