"""Abre la demo, ejecuta el consumo de API y captura screenshots."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("reports/figures")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    page.goto("http://localhost:8501", wait_until="networkidle")
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "demo_01_inicial.png"), full_page=True)
    print("inicial OK")

    # Pulsar el botón principal de ejecución
    btn = page.get_by_role("button", name="Consumir la API de datos abiertos")
    btn.click()
    # Esperar a que terminen las llamadas y el render del mapa (pydeck es asíncrono)
    page.wait_for_timeout(14000)
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(OUT / "demo_02_consumo.png"), full_page=True)
    # Captura enfocada al final (mapa / gráfico)
    page.mouse.wheel(0, 30000)
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "demo_03_mapa.png"))
    print("consumo OK")

    body = page.inner_text("body")
    for needle in ["registros descargados", "columnas", "georreferenciados", "ciclo completo"]:
        print(f"  contiene '{needle}':", needle.lower() in body.lower())

    browser.close()
