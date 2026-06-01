"""Inspeciona o player no /e/787696/learn e o estado da marca d'água na admin."""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
BASE = os.environ["BASE_URL"].rstrip("/") + "/"
EMAIL = os.environ["ADMIN_EMAIL"]
PWD = os.environ["ADMIN_PASSWORD"]
EVENTO = os.environ["EVENTO_ID"]
ATIV = os.environ["ATIVIDADE_VIDEO_MARCA_DAGUA_ID"]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # ---- 1) Aluno: inspeciona DOM em volta do <video>
        ctx_aluno = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx_aluno.new_page()
        page.goto(BASE + "login", wait_until="domcontentloaded")
        page.locator("#user_email").fill(EMAIL)
        page.locator("#user_password").fill(PWD)
        page.locator("#user_submit").click()
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        page.wait_for_timeout(3000)

        page.goto(f"{BASE}e/{EVENTO}/learn?learn_origin=my-contents", wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        # clica em algo que sugira vídeo (mesma heurística do teste)
        try:
            page.get_by_text("vídeo", exact=False).first.click(timeout=3000)
            page.wait_for_timeout(4000)
        except Exception:
            pass

        # tenta dar play
        videos = page.locator("video").element_handles()
        if videos:
            videos[0].evaluate("v => v.play()")
            page.wait_for_timeout(2000)

        # Inspeciona o pai/avô do <video>: irmãos posicionados (absolute/fixed) podem ser a marca
        info = page.evaluate("""() => {
            const v = document.querySelector('video');
            if (!v) return {video: null};
            const parent = v.parentElement;
            const grand = parent ? parent.parentElement : null;
            const irmaos = parent ? Array.from(parent.children).filter(c => c !== v).map(c => ({
                tag: c.tagName,
                cls: c.className && c.className.toString ? c.className.toString().slice(0, 200) : c.className,
                id: c.id,
                outer: c.outerHTML.substring(0, 400),
                rect: (() => { const r = c.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; })(),
            })) : [];
            const tios = grand ? Array.from(grand.children).filter(c => c !== parent).map(c => ({
                tag: c.tagName,
                cls: c.className && c.className.toString ? c.className.toString().slice(0, 200) : c.className,
                outer: c.outerHTML.substring(0, 300),
            })) : [];
            return {video: {src: v.src, currentTime: v.currentTime, duration: v.duration}, irmaos, tios};
        }""")
        print("=== Inspeção do player (aluno) ===")
        import json
        print(json.dumps(info, indent=2, ensure_ascii=False, default=str)[:4000])

        # ---- 2) Admin: estado atual do checkbox de marca d'água na atividade
        ctx_admin = browser.new_context(viewport={"width": 1366, "height": 768})
        page2 = ctx_admin.new_page()
        page2.goto(BASE + "login", wait_until="domcontentloaded")
        page2.locator("#user_email").fill(EMAIL)
        page2.locator("#user_password").fill(PWD)
        page2.locator("#user_submit").click()
        page2.wait_for_load_state("domcontentloaded", timeout=20000)
        page2.wait_for_timeout(3000)
        page2.goto(f"{BASE}e/{EVENTO}/contents/{ATIV}/edit", wait_until="domcontentloaded", timeout=30000)
        page2.wait_for_timeout(6000)

        estado = page2.evaluate("""() => {
            const lbl = Array.from(document.querySelectorAll('label.chakra-checkbox'))
                .find(l => /Habilitar marca d.água no vídeo/i.test(l.innerText || ''));
            if (!lbl) return {found: false};
            const input = lbl.querySelector('input');
            return {
                found: true,
                data_checked: lbl.getAttribute('data-checked'),
                input_checked: input ? input.checked : null,
                input_value: input ? input.value : null,
            };
        }""")
        print("\n=== Estado do checkbox 'Habilitar marca d'água no vídeo' (admin) ===")
        print(estado)

        # Procura também o radio/option "Em movimento" / "Fixa" do tipo de exibição
        tipos = page2.evaluate("""() => {
            // Busca por radios ou selects com palavras-chave
            const candidatos = Array.from(document.querySelectorAll('input[type="radio"], select, [role="radio"]'));
            return candidatos.map(el => ({
                tag: el.tagName,
                type: el.type,
                name: el.name,
                value: el.value,
                checked: el.checked,
                label: (() => {
                    const id = el.id;
                    if (!id) return null;
                    const l = document.querySelector(`label[for='${id}']`);
                    return l ? (l.innerText||'').trim().slice(0, 80) : null;
                })(),
                outer: el.outerHTML.substring(0, 200),
            })).filter(x => x.label || /movimento|fixa|posic/i.test(x.outer));
        }""")
        print("\n=== Radios/Selects relevantes na edição ===")
        for t in tipos[:15]:
            print(f"  {t}")

        browser.close()


if __name__ == "__main__":
    main()
