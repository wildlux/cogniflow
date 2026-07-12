"""Strumenti per documenti: OCR locale, lettura PDF, traduzione offline e calcolo.

Tutte le funzioni sono "best-effort": se una libreria/modello non è disponibile
sollevano un'eccezione con un messaggio chiaro, così l'interfaccia può mostrarlo
all'utente senza bloccarsi.
"""

from __future__ import annotations

import ast
import operator
import os


# ---------------------------------------------------------------------------
# OCR locale (Tesseract)
# ---------------------------------------------------------------------------
def ocr_image(path: str, langs: str = "ita+eng") -> str:
    """Estrae il testo da un'immagine usando il modello OCR locale Tesseract."""
    import pytesseract
    from PIL import Image

    with Image.open(path) as img:
        return pytesseract.image_to_string(img, lang=langs).strip()


# ---------------------------------------------------------------------------
# PDF: estrazione testo (con fallback OCR per i PDF scansionati)
# ---------------------------------------------------------------------------
def extract_pdf_text(path: str, ocr_fallback: bool = True, max_pages: int = 20) -> str:
    """Estrae il testo da un PDF. Se una pagina non ha testo (scansione),
    usa l'OCR locale sul rendering della pagina."""
    import fitz  # PyMuPDF

    parti: list[str] = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            if i >= max_pages:
                parti.append(f"[... troncato a {max_pages} pagine ...]")
                break
            testo = page.get_text().strip()
            if not testo and ocr_fallback:
                testo = _ocr_pdf_page(page)
            if testo:
                parti.append(testo)
    return "\n\n".join(parti).strip()


def _ocr_pdf_page(page, langs: str = "ita+eng") -> str:
    """Renderizza una pagina PDF e le applica l'OCR locale."""
    try:
        import io

        import pytesseract
        from PIL import Image

        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang=langs).strip()
    except Exception:
        return ""


def render_pdf_first_page_png(path: str, dpi: int = 120) -> bytes:
    """Restituisce la prima pagina del PDF come PNG (bytes) per l'anteprima."""
    import fitz

    with fitz.open(path) as doc:
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")


# ---------------------------------------------------------------------------
# Traduzione offline (Argos Translate, modelli locali)
# ---------------------------------------------------------------------------
def translate_text(text: str, from_code: str = "en", to_code: str = "it") -> str:
    """Traduce il testo con i modelli locali di Argos Translate."""
    import argostranslate.translate as translate

    return translate.translate(text, from_code, to_code)


def available_translations() -> list[tuple[str, str]]:
    """Coppie (from, to) di traduzione installate localmente."""
    try:
        import argostranslate.translate as translate

        coppie = []
        for lang in translate.get_installed_languages():
            for t in lang.translations_from:
                coppie.append((t.from_lang.code, t.to_lang.code))
        return coppie
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Calcolatrice sicura (solo espressioni aritmetiche)
# ---------------------------------------------------------------------------
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

import math as _math

_ALLOWED_NAMES = {
    "pi": _math.pi,
    "e": _math.e,
    "sqrt": _math.sqrt,
    "sin": _math.sin,
    "cos": _math.cos,
    "tan": _math.tan,
    "log": _math.log,
    "log10": _math.log10,
    "exp": _math.exp,
    "abs": abs,
    "round": round,
    "radians": _math.radians,
    "degrees": _math.degrees,
    "factorial": _math.factorial,
}


def calculate(expression: str):
    """Valuta un'espressione aritmetica in modo sicuro (niente codice arbitrario).

    Supporta + - * / // % **, parentesi e funzioni comuni (sqrt, sin, log, ...).
    """
    expr = expression.strip().lstrip("=").strip()
    if not expr:
        raise ValueError("Espressione vuota")

    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Valore non ammesso")
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        if isinstance(node, ast.Name):
            if node.id in _ALLOWED_NAMES and not callable(_ALLOWED_NAMES[node.id]):
                return _ALLOWED_NAMES[node.id]
            raise ValueError(f"Nome non ammesso: {node.id}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fn = _ALLOWED_NAMES.get(node.func.id)
            if callable(fn):
                return fn(*[_eval(a) for a in node.args])
            raise ValueError(f"Funzione non ammessa: {node.func.id}")
        raise ValueError("Espressione non ammessa")

    tree = ast.parse(expr, mode="eval")
    result = _eval(tree.body)
    # Presenta gli interi senza decimali
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return result


def looks_like_math(text: str) -> bool:
    """True se il testo sembra un'espressione da calcolare (inizia con '=')."""
    return text.strip().startswith("=") and len(text.strip()) > 1
