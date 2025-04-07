"""Integration for Zabbix monitoring system.

This module provides classes and utilities to interact with Zabbix,
including event handling and API integration.
"""
from collections import defaultdict
import logging

from pyzabbix.api import ZabbixAPI
import urllib3

urllib3.disable_warnings()

_LOGGER = logging.getLogger(__name__)


class ZbxEvent:
    """ZbcEvent Class."""

    def __init__(self, eid, name, severity, tags, host=None) -> None:
        """Initialize the class."""
        self.eid = eid
        self.name = name
        self.severity = severity
        self.tags = tags
        self.host = host or 'service'

    def __eq__(self, other):
        """Check for equality."""
        return (
            (self.eid == other.eid)
            and (self.host == other.host)
            and (self.name == other.name)
            and (self.severity == other.severity)
        )

    def __str__(self):
        """Represent string."""
        return f"{self.host}: {self.name} ({self.severity})"

    def __repr__(self):
        """Representation."""
        return f"<ZbxEvent: {self.eid}, {self.host}, {self.name}, {self.severity}>"


class Zbx:
    """Zbx Class."""

    def __init__(self, host, api_token, path="", port=443, ssl=True) -> None:
        """Initialize the class."""
        self.host = host
        self.api_token = api_token
        self.path = path
        self.port = port
        self.ssl = ssl
        protocol = "https" if ssl else "http"
        self.url = f"{protocol}://{self.host}:{self.port}/{self.path}"
        self.zapi = ZabbixAPI(self.url)
        self.zapi.session.verify = False
        self.zapi.login(api_token=self.api_token)
        self.version = self.zapi.version.public
        self._problems_by_tag = defaultdict(list)
        self._services_by_tag = defaultdict(list)

    def _get_taglist(self, tags):
        return [f'{tag["tag"]}:{tag["value"]}' for tag in tags]

    def _get_eidmap(self, eids):
        """Map event IDs to host names."""
        events = self.zapi.event.get(
            eventids=eids,
            output=["eventid"],
            selectHosts=["name"]
        )
        return {e["eventid"]: e["hosts"][0]["name"] for e in events}

    def _update_problems(self):
        """Get current problems grouped by tag."""
        self._problems_by_tag.clear()
        raw_problems = self.zapi.problem.get(
            output=["eventid", "severity", "name"],
            selectTags=["tag", "value"]
        )
        eids = [p["eventid"] for p in raw_problems]
        eidmap = self._get_eidmap(eids)

        for p in raw_problems:
            eid = p["eventid"]
            host = eidmap.get(eid, "N/A")
            info = p["name"]
            severity = p["severity"]
            tags = p.get("tags", [])
            zbx_event = ZbxEvent(eid, info, severity, tags, host=host)
            for tag_key in self._get_taglist(tags):
                self._problems_by_tag[tag_key].append(zbx_event)

    def _update_svcs(self):
        """Get Zabbix service status."""
        self._services_by_tag.clear()
        raw_svcs = self.zapi.service.get(
            output=["serviceid", "status", "description"],
            selectParents="count",
            selectTags="extend"
        )
        for service in raw_svcs:
            if service["parents"] == "0":
                eid = service["serviceid"]
                tags = service.get("tags", [])
                severity = service["status"]
                info = service["description"]
                zbx_event = ZbxEvent(eid, info, severity, tags)
                for tag_key in self._get_taglist(tags):
                    self._services_by_tag[tag_key].append(zbx_event)

    def problems(self):
        """Output zabbix problems."""
        self._update_problems()
        return self._problems_by_tag

    def services(self):
        """Output zabbix services."""
        self._update_svcs()
        return self._services_by_tag
