import logging
from typing import Optional
from app.utils import supabase_client
from app.inference_engine.cpe_dictionary import cpe_matcher

logger = logging.getLogger(__name__)


class SBOMMatcher:
    """Matches SBOM components to known vulnerabilities via CPE inference."""

    async def match_sbom_to_vulnerabilities(
        self, org_id: str, sbom_components: list[dict]
    ) -> list[dict]:
        """
        Match SBOM components to vulnerabilities in the database.
        """
        matches = []
        if not cpe_matcher.loaded:
            await cpe_matcher.load_cpe_dictionary()
        for component in sbom_components:
            component_name = component.get("name", "")
            component_version = component.get("version", "")
            if not component_name:
                continue
            inferred_cpes = cpe_matcher.infer_cpe_from_description(
                f"{component_name} version {component_version}",
                {component_name: component_version},
            )
            if not inferred_cpes:
                logger.debug(f"No CPE matches for {component_name}")
                continue
            for cpe_data in inferred_cpes[:3]:
                cpe_uri = cpe_data["cpe_uri"]
                vulns = await self._query_vulns_by_cpe(
                    org_id, cpe_uri, component_version
                )
                for vuln in vulns:
                    matches.append(
                        {
                            "component": {
                                "name": component_name,
                                "version": component_version,
                            },
                            "vulnerability": vuln,
                            "confidence": cpe_data["confidence"],
                            "match_type": cpe_data["match_type"],
                            "matched_cpe": cpe_uri,
                        }
                    )

        def get_confidence(item):
            return item["confidence"]

        matches.sort(key=get_confidence, reverse=True)
        logger.info(
            f"Matched {len(matches)} vulnerabilities to {len(sbom_components)} SBOM components"
        )
        return matches

    async def _query_vulns_by_cpe(
        self, org_id: str, cpe_uri: str, version: str
    ) -> list[dict]:
        """Query vulnerabilities by CPE URI."""
        try:
            response = (
                await supabase_client.supabase_client.table("inference_findings")
                .select("*")
                .eq("organization_id", org_id)
                .contains("inferred_cpes", [{"cpe_uri": cpe_uri}])
                .execute()
            )
            vulnerabilities = response.data if response.data else []
            if version and version != "*":
                filtered = []
                for vuln in vulnerabilities:
                    for cpe in vuln.get("inferred_cpes", []):
                        if cpe.get("cpe_uri") == cpe_uri:
                            cpe_version = cpe.get("version", "*")
                            if cpe_version == version or cpe_version == "*":
                                filtered.append(vuln)
                                break
                return filtered
            return vulnerabilities
        except Exception as e:
            logger.exception(f"Error querying vulnerabilities by CPE: {e}")
            return []


sbom_matcher = SBOMMatcher()