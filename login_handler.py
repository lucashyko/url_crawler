from playwright.sync_api import Page
import os

def attempt_login(page: Page, username: str, password: str):
    """Tenta realizar login clicando no botão correto e preenchendo os campos."""
    selectors = [
        ".btn-danger.login-toggle",
    ]

    clicked = False
    for selector in selectors:
        try:
            elements = page.locator(selector).all()
            if elements:
                print(f"🔎 Encontrados {len(elements)} elementos com {selector}")
                print(elements)
                for el in elements:
                    if el.is_visible():
                        el.scroll_into_view_if_needed()
                        el.hover()
                        el.click(force=True, timeout=3000)
                        clicked = True
                        print(f"✅ Botão clicado com {selector}")
                        print (el)
                        break
        except Exception as e:
            print(f"⚠️ Falha ao clicar com {selector}: {str(e)}")
        
        if clicked:
            break

    if not clicked:
        raise Exception("❌ Nenhum botão de login clicável encontrado.")

    # Preenche os campos de login
    page.fill("input[name='name']", username)
    page.fill("input[name='pass']", password)
    page.click("input[name='submit']")
