import logging
from collections import defaultdict

from pyzabbix.api import ZabbixAPI
import urllib3

urllib3.disable_warnings()

_LOGGER = logging.getLogger(__name__)


class ZbxEvent:
    """ZbcEvent Class."""

    def __init__(self, eid, host, name, severity):
        """Initialize the class."""
        self.eid = eid
        self.host = host
        self.name = name
        self.severity = severity

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
        return f"<ZbxEvent: {self.eid},{self.host},{self.name},{self.severity}>"


class Zbx:
    """Zbx Class."""

    def __init__(self, host, api_token, path="", port=443, ssl=True):
        """Initialize the class."""
        protocol = "https" if ssl else "http"
        self.url = f"{protocol}://{host}:{port}/{path}"
        self.zapi = ZabbixAPI(self.url)
        self.zapi.session.verify = False
        self.zapi.login(api_token=api_token)
        self.version = self.zapi.version.public

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

    def _get_problems(self):
        """Get current problems grouped by tag."""
        problems = defaultdict(list)
        raw_problems = self.zapi.problem.get(
            output=["eventid", "severity", "name"],
            selectTags=["tag", "value"]
        )

        eids = [p["eventid"] for p in raw_problems]
        eidmap = self._get_eidmap(eids)

        for p in raw_problems:
            eventid = p["eventid"]
            host = eidmap.get(eventid, "N/A")
            tags = p.get("tags", [])
            for tag_key in self._get_taglist(tags):
                problems[tag_key].append(
                    (p["severity"], host, p["name"])
                )

        return dict(problems)

    def _get_svcs(self):
        """Get Zabbix service status."""
        svcs = defaultdict(list)
        raw_svcs = self.zapi.service.get(
            output=["serviceid", "status", "description"],
            selectParents="count",
            selectTags="extend"
        )
        for service in raw_svcs:
            if service["parents"] == "0":
                tags = service.get("tags", [])
                for tag_key in self._get_taglist(tags):
                    svcs[tag_key].append(
                        (service["status"], "N/A", service["description"])
                )
        return dict(svcs)

    def problems(self):
        """Output zabbix problems."""
        return self._get_problems()

    def services(self):
        """Output zabbix services."""
        return self._get_svcs()


if __name__ == "__main__":
    # host = input("Zabbix Host: ")
    host = "zabbix.rexkramer.de"
    # api_token = input("Zabbix API Token: ")
    api_token = "3aad14ab5bd5bac434e6f16e5d44e0e4d8c9761fcf96b4071e062a8e89c7a564"
    z = Zbx(host, api_token)
    print(z.problems())
    print(z.services())
