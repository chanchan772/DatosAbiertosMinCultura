"""Verifica la página Datos Abiertos: icono del botón + consumo sin traceback crudo."""

from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("reports/figures"); OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1500, "height": 1050})
    pg.goto("http://localhost:8501/Datos_Abiertos", wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)

    # ¿El botón muestra el glifo del icono o el texto "bolt"?
    btn = pg.get_by_role("button", name="Consumir la API de datos abiertos")
    btn_txt = btn.inner_text()
    print("Texto del botón:", repr(btn_txt))
    print("  -> icono OK (no aparece 'bolt' como texto):", "bolt" not in btn_txt.lower())

    btn.click()
    pg.wait_for_timeout(14000)  # reintentos de API + posible fallback
    pg.screenshot(path=str(OUT / "consumo_final.png"), full_page=True)

    exc = pg.locator('[data-testid="stException"]').count()
    body = pg.inner_text("body").lower()
    print("  -> bloques de excepción cruda:", exc)
    print("  -> contiene 'traceback':", "traceback" in body)
    print("  -> consumo en vivo:", "descargados en vivo" in body)
    print("  -> respaldo local activado:", "copia descargada" in body or "copia local" in body)
    print("  -> mapa/municipios:", "georreferenciados" in body)
    b.close()
