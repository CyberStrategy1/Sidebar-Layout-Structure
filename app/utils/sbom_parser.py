import json
import xml.etree.ElementTree as ET
import logging


def parse_cyclonedx_json(data: dict) -> list[dict]:
    components = []
    for component in data.get("components", []):
        components.append(
            {"name": component.get("name"), "version": component.get("version")}
        )
    return components


def parse_spdx_json(data: dict) -> list[dict]:
    components = []
    for package in data.get("packages", []):
        components.append(
            {"name": package.get("name"), "version": package.get("versionInfo")}
        )
    return components


def parse_cyclonedx_xml(root: ET.Element) -> list[dict]:
    components = []
    ns = {"bom": "http://cyclonedx.org/schema/bom/1.4"}
    for component in root.findall("bom:components/bom:component", ns):
        name = component.find("bom:name", ns)
        version = component.find("bom:version", ns)
        if name is not None and version is not None:
            components.append({"name": name.text, "version": version.text})
    return components


def parse_sbom(file_content: bytes, filename: str) -> list[dict]:
    try:
        content_str = file_content.decode("utf-8")
        if filename.endswith(".json"):
            data = json.loads(content_str)
            if data.get("bomFormat") == "CycloneDX":
                return parse_cyclonedx_json(data)
            elif data.get("spdxVersion"):
                return parse_spdx_json(data)
        elif filename.endswith(".xml"):
            root = ET.fromstring(content_str)
            if "cyclonedx" in root.tag.lower():
                return parse_cyclonedx_xml(root)
        raise ValueError("Unsupported SBOM format or file type")
    except Exception as e:
        logging.exception(f"Failed to parse SBOM file {filename}: {e}")
        raise