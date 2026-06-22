"""Verifica el tablero multipágina: carga cada página, captura y detecta errores."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("reports/figures")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:8501"

PAGINAS = [
    ("inicio", "/"),
    ("datos_abiertos", "/Datos_Abiertos"),
    ("demanda_brecha", "/Demanda_y_Brecha"),
    ("simulador", "/Simulador_de_Exhibidor"),
    ("estacionalidad", "/Estacionalidad"),
    ("narrativa", "/Narrativa_IA"),
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    fallos = 0
    for nombre, ruta in PAGINAS:
        page.goto(BASE + ruta, wait_until="domcontentloaded")
        page.wait_for_timeout(7000)  # render de mapas/plotly
        page.screenshot(path=str(OUT / f"app_{nombre}.png"), full_page=True)
        # ¿Hay una excepción de Streamlit en pantalla?
        err = page.locator('[data-testid="stException"]').count()
        body = page.inner_text("body").lower()
        tiene_error = err > 0 or "traceback" in body
        print(f"{'FAIL' if tiene_error else 'OK  '} {nombre:<16} exception_blocks={err}")
        fallos += int(tiene_error)
    browser.close()
    print(f"\nResultado: {len(PAGINAS)-fallos}/{len(PAGINAS)} páginas OK")
