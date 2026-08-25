#!/usr/bin/env python3
"""Generate static Portuguese and Spanish help pages from help-en.html."""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from bs4 import BeautifulSoup, Comment, Doctype, NavigableString


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "help-en.html"
CACHE_PATH = Path("/tmp/argiope-help-translation-cache.json")
SKIP_TAGS = {"script", "style", "code", "kbd"}
TRANSLATABLE_ATTRIBUTES = ("alt", "aria-label", "placeholder", "title")
PROTECTED_TERMS = (
    "Argiope", "ColorChecker", "Roboflow", "Gemini", "ImageJ", "LibRaw",
    "zero-shot", "Zero-shot", "RGB", "RAW", "TIFF", "ENVI", "GeoTIFF",
    "JPEG", "PNG", "JSON", "COCO", "CWL", "FWHM", "PCA", "K-Means",
    "GMM", "KDE", "BIC", "SAM", "API", "URL", "Python", "Excel",
)

LOCALES = {
    "pt": {
        "output": "ajuda.html",
        "html_lang": "pt-BR",
        "landing": "index-pt.html",
        "active": "PT",
    },
    "es": {
        "output": "ayuda.html",
        "html_lang": "es",
        "landing": "index-es.html",
        "active": "ES",
    },
}

OVERRIDES = {
    "pt": {
        "Support": "Suporte",
        "Support on GitHub ↗": "Suporte no GitHub ↗",
        "Help Center · University of Brasília": "Central de Ajuda · Universidade de Brasília",
        "User Defined Formulas": "Fórmulas definidas pelo usuário",
        "AI Models & Feature Generation": "Modelos de IA e geração de objetos",
        "Mask pair policy — Valid endpoints": "Política de pares da máscara — Extremidades válidas",
        "Mask pair policy — Same connected component": "Política de pares da máscara — Mesmo componente conectado",
    },
    "es": {
        "Support": "Soporte",
        "Support on GitHub ↗": "Soporte en GitHub ↗",
        "Help Center · University of Brasília": "Centro de Ayuda · Universidad de Brasilia",
        "User Defined Formulas": "Fórmulas definidas por el usuario",
        "AI Models & Feature Generation": "Modelos de IA y generación de objetos",
        "Mask pair policy — Valid endpoints": "Política de pares de la máscara — Extremos válidos",
        "Mask pair policy — Same connected component": "Política de pares de la máscara — Mismo componente conectado",
    },
}


def load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def protect_terms(text: str) -> tuple[str, dict[str, str]]:
    protected: dict[str, str] = {}
    result = text
    for identifier in sorted(set(re.findall(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_{}]+\b", result)), key=len, reverse=True):
        token = f"ZXI{len(protected)}IXZ"
        result = result.replace(identifier, token)
        protected[token] = identifier
    for term in sorted(PROTECTED_TERMS, key=len, reverse=True):
        token = f"ZXQ{len(protected)}QXZ"
        if term in result:
            result = result.replace(term, token)
            protected[token] = term
    return result, protected


def translate_text(text: str, locale: str, cache: dict[str, str]) -> str:
    cache_key = f"v3\0{locale}\0{text}"
    if cache_key in cache:
        return cache[cache_key]

    legacy_key = f"{locale}\0{text}"
    if legacy_key in cache:
        return cache[legacy_key]

    prepared, protected = protect_terms(text)
    payload = urllib.parse.urlencode({
        "client": "gtx",
        "sl": "en",
        "tl": locale,
        "dt": "t",
        "q": prepared,
    }).encode("utf-8")

    for attempt in range(4):
        try:
            request = urllib.request.Request(
                "https://translate.googleapis.com/translate_a/single",
                data=payload,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            translated = "".join(part[0] for part in data[0] if part[0])
            for token, term in protected.items():
                translated = translated.replace(token, term)
                translated = translated.replace(token.lower(), term)
            cache[cache_key] = translated
            return translated
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("Translation failed")


def should_translate(text: str) -> bool:
    stripped = text.strip()
    return bool(
        stripped
        and re.search(r"[A-Za-z]", stripped)
        and not re.fullmatch(r"https?://\S+", stripped)
        and not re.fullmatch(r"[A-Z0-9_.{}()+*/<>=!-]+", stripped)
        and not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_{}]+", stripped)
    )


def collect_strings(soup: BeautifulSoup) -> list[NavigableString]:
    strings: list[NavigableString] = []
    for node in soup.find_all(string=True):
        if not isinstance(node, NavigableString):
            continue
        if isinstance(node, (Comment, Doctype)):
            continue
        if node.parent and node.parent.name in SKIP_TAGS:
            continue
        if should_translate(str(node)):
            strings.append(node)
    return strings


def translate_page(locale: str, config: dict[str, str], cache: dict[str, str]) -> None:
    soup = BeautifulSoup(SOURCE.read_text(encoding="utf-8"), "lxml")
    nodes = collect_strings(soup)
    attributes: list[tuple[object, str, str]] = []
    for element in soup.find_all(True):
        for attribute in TRANSLATABLE_ATTRIBUTES:
            value = element.get(attribute)
            if isinstance(value, str) and should_translate(value):
                attributes.append((element, attribute, value))

    unique_texts = {str(node).strip() for node in nodes}
    unique_texts.update(value for _, _, value in attributes)
    translated: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(translate_text, text, locale, cache): text
            for text in unique_texts
        }
        for future in as_completed(futures):
            source_text = futures[future]
            translated[source_text] = future.result()
    translated.update(OVERRIDES[locale])

    for node in nodes:
        original = str(node)
        core = original.strip()
        prefix = original[: len(original) - len(original.lstrip())]
        suffix = original[len(original.rstrip()):]
        node.replace_with(f"{prefix}{translated[core]}{suffix}")

    for element, attribute, value in attributes:
        element[attribute] = translated[value]

    soup.html["lang"] = config["html_lang"]
    for link in soup.select('.help-language-switcher a'):
        if link.get_text(strip=True) == config["active"]:
            link["aria-current"] = "page"
        else:
            link.attrs.pop("aria-current", None)

    for link in soup.select('a[href="index-en.html"]'):
        link["href"] = config["landing"]

    output = str(soup)
    if locale == "pt":
        output = output.replace(
            'Use um <strong>Assistido por IA</strong> detector.',
            'Use um detector <strong>assistido por IA</strong>.',
        )
        output = output.replace('eixo_maior', 'major_axis').replace('eixo_menor', 'minor_axis')
        output = output.replace('Centralize o comprimento de onda e a largura total na metade do máximo', 'comprimento de onda central e largura total na metade do máximo')
        output = output.replace('coordenadas xey', 'coordenadas x e y')
        output = output.replace('<strong>Proporção</strong>', '<strong>Razão de aspecto</strong>')
        output = output.replace('<strong>Redondeza</strong>', '<strong>Arredondamento</strong>')
    else:
        output = output.replace(
            'Utilice un <strong>asistido por IA</strong> detector.',
            'Utilice un detector <strong>asistido por IA</strong>.',
        )
        output = output.replace('eje_mayor', 'major_axis').replace('eje_menor', 'minor_axis')
        output = output.replace('Hacer clic', 'Haga clic')
        output = output.replace('Coordenadas xey', 'Coordenadas x e y').replace('coordenadas xey', 'coordenadas x e y')
        output = output.replace('Estimación de la densidad del grano', 'Estimación de densidad del kernel')
    (ROOT / config["output"]).write_text(output, encoding="utf-8")


def main() -> None:
    cache = load_cache()
    for locale, config in LOCALES.items():
        translate_page(locale, config, cache)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
