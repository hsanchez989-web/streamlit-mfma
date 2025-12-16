"""Helpers for reading and writing Microsoft Lists data hosted in SharePoint.

This module centralizes SharePoint connectivity so the Streamlit UI can remain
focused on presentation. Authentication is handled via Azure AD app
credentials provided through environment variables.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import os
import logging

import pandas as pd
from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.listitems.caml.caml_query import CamlQuery


logger = logging.getLogger(__name__)


@dataclass
class SharePointConfig:
    tenant: str
    site_url: str
    client_id: str
    client_secret: str
    mfmea_list_name: str = "MFMEA"
    access_list_name: str = "ProjectAccess"

    @classmethod
    def from_env(cls) -> "SharePointConfig":
        return cls(
            tenant=os.getenv("SHAREPOINT_TENANT", ""),
            site_url=os.getenv("SHAREPOINT_SITE_URL", ""),
            client_id=os.getenv("SHAREPOINT_CLIENT_ID", ""),
            client_secret=os.getenv("SHAREPOINT_CLIENT_SECRET", ""),
            mfmea_list_name=os.getenv("MFMEA_LIST_NAME", "MFMEA"),
            access_list_name=os.getenv("ACCESS_LIST_NAME", "ProjectAccess"),
        )

    def is_configured(self) -> bool:
        return all(
            [self.tenant, self.site_url, self.client_id, self.client_secret]
        )


def _create_client(cfg: SharePointConfig) -> Optional[ClientContext]:
    """Build an authenticated SharePoint client context if configuration exists."""
    if not cfg.is_configured():
        logger.warning("SharePoint configuration missing; running in local-only mode")
        return None

    credentials = ClientCredential(cfg.client_id, cfg.client_secret)
    ctx = ClientContext(cfg.site_url).with_credentials(credentials)
    return ctx


def fetch_mfmea_rows(cfg: SharePointConfig) -> pd.DataFrame:
    """Load MFMEA entries from SharePoint list.

    Returns a dataframe with normalized column names to simplify the UI layer.
    If configuration is incomplete or the request fails, an empty frame is returned.
    """

    ctx = _create_client(cfg)
    if ctx is None:
        return pd.DataFrame()

    try:
        sp_list = ctx.web.lists.get_by_title(cfg.mfmea_list_name)
        caml = CamlQuery()
        items = sp_list.get_items(caml)
        ctx.load(items)
        ctx.execute_query()
    except Exception as exc:  # pragma: no cover - network interactions
        logger.error("Failed to load SharePoint list: %s", exc)
        return pd.DataFrame()

    records: List[Dict[str, Any]] = []
    for item in items:  # pragma: no cover - requires live list
        data = item.properties
        records.append(
            {
                "Machine": data.get("Machine", ""),
                "Project": data.get("Project", ""),
                "Customer": data.get("Customer", ""),
                "Analyst": data.get("Analyst", ""),
                "Function": data.get("Function", ""),
                "FailureMode": data.get("FailureMode", ""),
                "FailureEffect": data.get("FailureEffect", ""),
                "Cause": data.get("Cause", ""),
                "Severity": int(data.get("Severity", 0)),
                "Occurrence": int(data.get("Occurrence", 0)),
                "Detection": int(data.get("Detection", 0)),
                "Prevention": data.get("Prevention", ""),
                "DetectionControls": data.get("DetectionControls", ""),
                "RPNGoal": int(data.get("RPNGoal", 180)),
                "ID": data.get("ID"),
            }
        )

    return pd.DataFrame.from_records(records)


def user_project_access(cfg: SharePointConfig, user_email: str) -> List[str]:
    """Return project names the user can edit.

    This reads from a ProjectAccess list expected to contain `User` and `Project`
    fields. Empty configuration yields an empty list, meaning read-only mode.
    """

    ctx = _create_client(cfg)
    if ctx is None:
        return []

    try:
        sp_list = ctx.web.lists.get_by_title(cfg.access_list_name)
        caml = CamlQuery()
        items = sp_list.get_items(caml)
        ctx.load(items)
        ctx.execute_query()
    except Exception as exc:  # pragma: no cover - network interactions
        logger.error("Failed to load access list: %s", exc)
        return []

    projects = set()
    for item in items:  # pragma: no cover - requires live list
        props = item.properties
        user_value = props.get("User", "").lower()
        project_value = props.get("Project", "")
        if user_email.lower() == user_value and project_value:
            projects.add(project_value)

    return sorted(projects)


def save_record(cfg: SharePointConfig, payload: Dict[str, Any]) -> bool:
    """Persist a new MFMEA record to SharePoint.

    Returns True on success. Silent failure returns False to allow the UI to
    show a helpful error without raising.
    """

    ctx = _create_client(cfg)
    if ctx is None:
        logger.warning("Skipping persistence because SharePoint is not configured")
        return False

    try:
        sp_list = ctx.web.lists.get_by_title(cfg.mfmea_list_name)
        item = sp_list.add_item(payload)
        item.update()
        ctx.execute_query()
    except Exception as exc:  # pragma: no cover - network interactions
        logger.error("Failed to save SharePoint item: %s", exc)
        return False

    return True


__all__ = [
    "SharePointConfig",
    "fetch_mfmea_rows",
    "user_project_access",
    "save_record",
]
