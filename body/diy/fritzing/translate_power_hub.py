#!/usr/bin/env python3
"""Localize the English FZZ and export Fritzing Breadboard SVGs using an offline catalog."""

import argparse
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


HERE = Path(__file__).resolve().parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("", "http://www.w3.org/2000/svg")


def language_code(value):
    code = re.split(r"[-_]", value.lower())[0]
    if not re.fullmatch(r"[a-z]{2,3}", code):
        raise ValueError(f"Invalid language: {value}")
    return code


def discover_languages(repo):
    """Include documentation, Android resources and iOS localization folders."""
    try:
        result = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"],
                                check=True, capture_output=True)
        paths = result.stdout.decode("utf-8").split("\0")
    except (OSError, subprocess.CalledProcessError):
        paths = []
        ignored = {".git", ".worktrees", "node_modules", ".venv", "venv", "build", "Pods"}
        for folder, dirs, files in os.walk(repo):
            dirs[:] = [name for name in dirs if name not in ignored]
            paths.extend((Path(folder)/name).relative_to(repo).as_posix() for name in files)
    found = {"en", "ru"}
    patterns = [r"(?:^|/)README(?:\.[^.]+)*\.([a-z]{2,3}(?:-[A-Za-z]+)?)\.md$",
                r"/res/values-([^/]+)/strings\.xml$", r"/([^/]+)\.lproj/[^/]+\.strings$"]
    for path in paths:
        for pattern in patterns:
            match = re.search(pattern, path)
            if match and match[1].lower() != "base":
                found.add(language_code(match[1]))
    return sorted(found)


def load_fzz(path):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Invalid FZZ archive: {path}")
        return {name: archive.read(name) for name in archive.namelist()}


def xml_files(files):
    return {name: ET.fromstring(data) for name, data in files.items()
            if name.endswith((".fz", ".fzp", ".svg"))}


def rendered_label(node, text):
    return node.get("data-i18n-prefix", "") + text + node.get("data-i18n-suffix", "")


def label_text(node, catalog, language):
    entry = catalog.get("labels", {}).get(node.get("data-i18n"), {})
    for candidate in [language, "en"]:
        text = entry.get(candidate)
        if isinstance(text, str) and text.strip():
            return rendered_label(node, text)
    return node.text or ""  # The original FZZ is the English source of truth.


def check_catalog(files, catalog, languages):
    labels = catalog.get("labels", {})
    unknown = set(languages) - set(catalog.get("languages", {}))
    for language in sorted(unknown):
        print(f"Warning: {language} is absent from the catalog; missing labels will use English", file=sys.stderr)
    fallbacks = {}
    used = set()
    for name, root in xml_files(files).items():
        for node in root.iter():
            key = node.get("data-i18n")
            if key:
                used.add(key)
                entry = labels.get(key, {})
                for language in {"en", *languages}:
                    if not isinstance(entry.get(language), str) or not entry[language].strip():
                        pair = language, key
                        if pair not in fallbacks:
                            fallbacks[pair] = {"language": language, "key": key, "fallback": "en"}
                            if language not in unknown:
                                print(f"Warning: missing translation {key}/{language}; using English", file=sys.stderr)
                if isinstance(entry.get("en"), str) and entry["en"].strip() and node.text != rendered_label(node, entry["en"]):
                    raise ValueError(f"English label/catalog mismatch: {name}/{key}; update both")
            if name.endswith(".svg") and node.tag.endswith("text"):
                if re.search(r"[А-Яа-яЁё]", "".join(node.itertext())):
                    raise ValueError(f"Source SVG must have English labels: {name}")
    if not used:
        raise ValueError("No data-i18n bindings in the source FZZ")
    return [fallbacks[pair] for pair in sorted(fallbacks)]


def masked(root):
    """Only localized text, language metadata and module cache IDs may differ."""
    root = deepcopy(root)
    for node in root.iter():
        if node.get("data-i18n"):
            node.text = "@" + node.get("data-i18n")
        node.attrib.pop(XML_LANG, None)
        for attribute in ["moduleId", "moduleIdRef"]:
            if node.get(attribute) and node.get(attribute) != "WireModuleID":
                node.set(attribute, "@module")
    return ET.tostring(root, encoding="utf-8")


def localize(files, catalog, language):
    roots = xml_files(files)
    digest = sha256(b"".join(files[name] for name in sorted(files)) +
                    json.dumps(catalog, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    identifiers = {root.get("moduleId"): f"{root.get('moduleId')}__i18n_{language}_{digest}"
                   for name, root in roots.items() if name.endswith(".fzp")}
    translated = dict(files)
    for name, root in roots.items():
        before = masked(root)
        for node in root.iter():
            key = node.get("data-i18n")
            if key:
                node.text = label_text(node, catalog, language)
            for attribute in ["moduleId", "moduleIdRef"]:
                value = node.get(attribute)
                if value in identifiers:
                    node.set(attribute, identifiers[value])
        if name.endswith(".svg"):
            root.set(XML_LANG, language)
        if masked(root) != before:
            raise ValueError(f"Localization changed geometry or electrical data: {name}")
        translated[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return translated


def pack_fzz(files):
    stream = BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, files[name])
    return stream.getvalue()


def fritzing_binary(argument):
    candidates = [argument, os.environ.get("FRITZING_BIN"), shutil.which("Fritzing"),
                  shutil.which("fritzing"),
                  "/Applications/Fritzing.app/Contents/MacOS/Fritzing",
                  str(Path.home()/"Applications/Fritzing.app/Contents/MacOS/Fritzing")]
    for candidate in candidates:
        if candidate:
            path = Path(candidate).expanduser().resolve()
            if path.is_file() and os.access(path, os.X_OK):
                return path
    raise ValueError("Fritzing executable not found; pass --fritzing PATH or set FRITZING_BIN")


def export_language(binary, work, stem, files, language, timeout):
    folder = work/language
    folder.mkdir()
    document = folder/(stem+".fzz")
    document.write_bytes(pack_fzz(files))
    environment = dict(os.environ)
    environment.setdefault("QT_QPA_PLATFORM", "offscreen")
    result = subprocess.run([str(binary), "-svg", str(folder), "-d", str(folder/"log")],
                            env=environment, capture_output=True, timeout=timeout)
    if result.returncode:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace")[-2000:]
        raise ValueError(f"Fritzing export failed for {language}: {detail}")
    exported = {}
    for view in ["breadboard"]:
        path = folder/(stem+"_"+view+".svg")
        if not path.is_file():
            raise ValueError(f"Fritzing did not generate {language}/{view}")
        svg = ET.fromstring(path.read_bytes())
        svg.set(XML_LANG, language)
        if not any(node.tag.endswith("text") for node in svg.iter()):
            raise ValueError(f"Empty SVG export: {language}/{view}")
        exported[view] = ET.tostring(svg, encoding="utf-8", xml_declaration=True)
    return document.read_bytes(), exported


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE/"openbot-diy-power-hub.fzz")
    parser.add_argument("--catalog", type=Path, default=HERE/"power_hub_i18n.json")
    parser.add_argument("--repo", type=Path, default=HERE.parents[2])
    parser.add_argument("--output", type=Path, default=HERE/"power-hub-locales")
    parser.add_argument("--languages", nargs="+", default=["all"], help="all, or e.g. en ru de")
    parser.add_argument("--fritzing", help="path to the Fritzing executable")
    parser.add_argument("--timeout", type=int, default=120, help="export timeout per language, seconds")
    parser.add_argument("--keep-fzz", action="store_true", help="also save localized editable FZZ files")
    parser.add_argument("--check", action="store_true", help="validate translations and invariants without Fritzing")
    parser.add_argument("--list-languages", action="store_true")
    args = parser.parse_args()
    try:
        catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
        discovered = discover_languages(args.repo.resolve())
        if "all" in args.languages and args.languages != ["all"]:
            raise ValueError("Use --languages all alone, or specify language codes")
        languages = discovered if args.languages == ["all"] else sorted({language_code(v) for v in args.languages})
        if args.list_languages:
            for language in languages:
                print(f"{language}: {catalog.get('languages', {}).get(language, 'English fallback')}")
            return 0
        source = args.source.resolve()
        files = load_fzz(source)
        fallbacks = check_catalog(files, catalog, languages)
        variants = {language: localize(files, catalog, language) for language in languages}
        if args.check:
            print(f"PASS: {', '.join(languages)}; pins, values, wires and geometry unchanged; {len(fallbacks)} English fallbacks")
            return 0
        binary = fritzing_binary(args.fritzing)
        output = args.output.resolve()
        generated = {}
        with tempfile.TemporaryDirectory(prefix="openbot-power-hub-i18n-") as directory:
            work = Path(directory)
            for language in languages:
                generated[language] = export_language(binary, work, source.stem, variants[language], language, args.timeout)
                print(f"Exported {language}: Breadboard", flush=True)
            manifest = {"source": source.name, "source_sha256": sha256(source.read_bytes()).hexdigest(),
                        "catalog_sha256": sha256(args.catalog.read_bytes()).hexdigest(),
                        "generator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                        "discovered_languages": discovered, "languages": languages,
                        "fallbacks": fallbacks, "files": []}
            for language, (fzz, views) in generated.items():
                obsolete = output/language/(source.stem+"-schematic.svg")
                if obsolete.exists():
                    obsolete.unlink()
                artifacts = {f"{source.stem}-{view}.svg": data for view, data in views.items()}
                if args.keep_fzz:
                    artifacts[source.name] = fzz
                for name, data in artifacts.items():
                    relative = Path(language)/name
                    atomic_write(output/relative, data)
                    manifest["files"].append({"path": relative.as_posix(), "sha256": sha256(data).hexdigest()})
            atomic_write(output/"manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2)+"\n").encode("utf-8"))
        print(f"Saved {len(manifest['files'])} files in {output}")
        return 0
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.TimeoutExpired) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
