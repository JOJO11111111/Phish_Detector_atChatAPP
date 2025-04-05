from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def static_crp_locator(html_content, base_url=None):
    """
    HTML-only CRP detector. Attempts to find password fields and redirects
    based only on HTML content.

    :param html_content: Raw HTML content (str)
    :param base_url: Base URL of the page (for resolving relative links)
    :return: is_crp (bool), redirect_url (str or None)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    is_crp = False
    redirect_url = None

    # === 1. Look for password fields in <form>
    for form in soup.find_all('form'):
        input_types = [inp.get('type', '').lower() for inp in form.find_all('input')]
        if 'password' in input_types:
            is_crp = True
            redirect_url = form.get('action')
            break

    # === 2. Look for any input[type=password]
    if not is_crp and soup.find('input', {'type': 'password'}):
        is_crp = True

    # === 3. Check if page contains login-related keywords
    if not is_crp:
        text = soup.get_text(separator=' ').lower()
        keywords = ["login", "sign in", "signin", "log in", "log on", "sign up", "signup", "register", "registration", "create.*account", "open an account", "get free.*now", "join now", "new user", "my account", "come in", "become a member", "customer centre", "登入","登錄", "登録", "注册", "Anmeldung", "iniciar sesión", "identifier", "ログインする", "サインアップ", "ログイン", "로그인", "가입하기", "시작하기", "регистрация", "войти", "вход", "accedered", "gabung", "daftar", "masuk", "girişi", "Giriş", "สมัครสม", "وارد", "regístrate", "acceso", "acessar", "entrar", "ingresa","new account", "join us", "new", "enter password", "access your account", "create account", "登陆"]
        if any(k in text for k in keywords):
            is_crp = True

    # === 4. Try to find redirect target (meta refresh or JS)
    if not redirect_url:
        # meta refresh
        meta = soup.find('meta', attrs={'http-equiv': re.compile("refresh", re.I)})
        if meta and 'content' in meta.attrs:
            match = re.search(r'url=(.+)', meta['content'], re.IGNORECASE)
            if match:
                redirect_url = match.group(1).strip()

    if not redirect_url:
        # javascript redirects
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                match = re.search(r'window\.location\.href\s*=\s*["]([^\"]+)["]', script.string)
                if match:
                    redirect_url = match.group(1).strip()
                    break

    # === Resolve relative URL
    if base_url and redirect_url and not redirect_url.startswith('http'):
        redirect_url = urljoin(base_url, redirect_url)

    return is_crp, redirect_url
