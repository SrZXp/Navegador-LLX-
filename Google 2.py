from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
from stem import Signal
from stem.control import Controller
import socks
import socket
import sys
import os
import json
from cryptography.fernet import Fernet

# Gerar e salvar uma chave de criptografia (faça isso uma vez e mantenha a chave segura)
def generate_key():
    return Fernet.generate_key()

# Carregar a chave de criptografia
def load_key():
    return open("secret.key", "rb").read()

# Salvar a chave de criptografia
def save_key(key):
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

# Armazenar e recuperar dados criptografados
def encrypt_data(data, key):
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return encrypted_data

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data).decode()
    return decrypted_data

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser = QTabWidget()
        self.browser.setTabsClosable(True)
        self.browser.tabCloseRequested.connect(self.close_current_tab)
        self.browser.setDocumentMode(True)
        self.browser.setMovable(True)
        self.browser.tabBarDoubleClicked.connect(self.open_new_tab)

        self.setCentralWidget(self.browser)
        self.showMaximized()

        self.default_home_url = QUrl.fromLocalFile(os.path.abspath('search_page.html'))
        self.add_new_tab(self.default_home_url, "LLX")

        self.key = self.load_or_generate_key()

        # Barra de navegação
        navbar = QToolBar()
        self.addToolBar(navbar)

        back_btn = QAction('Back', self)
        back_btn.triggered.connect(lambda: self.current_browser().back())
        navbar.addAction(back_btn)

        forward_btn = QAction('Forward', self)
        forward_btn.triggered.connect(lambda: self.current_browser().forward())
        navbar.addAction(forward_btn)

        reload_btn = QAction('Reload', self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload())
        navbar.addAction(reload_btn)

        home_btn = QAction('Home', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        self.current_browser().urlChanged.connect(lambda qurl: self.update_url(qurl))

        # Atalhos para navegação
        self.shortcut_new_tab = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_new_tab.activated.connect(self.open_new_tab)

        self.shortcut_close_tab = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut_close_tab.activated.connect(self.close_current_tab)

        self.shortcut_back = QShortcut(QKeySequence("Alt+Left"), self)
        self.shortcut_back.activated.connect(lambda: self.current_browser().back())

        self.shortcut_forward = QShortcut(QKeySequence("Alt+Right"), self)
        self.shortcut_forward.activated.connect(lambda: self.current_browser().forward())

        self.apply_dark_theme()
        self.setup_tor()

    def load_or_generate_key(self):
        if not os.path.exists("secret.key"):
            key = generate_key()
            save_key(key)
        else:
            key = load_key()
        return key

    def save_credentials(self, site, username, password):
        credentials = {}
        if os.path.exists("credentials.json"):
            with open("credentials.json", "r") as file:
                credentials = json.load(file)
        
        encrypted_password = encrypt_data(password, self.key)
        credentials[site] = {"username": username, "password": encrypted_password.decode()}

        with open("credentials.json", "w") as file:
            json.dump(credentials, file, indent=4)

    def load_credentials(self, site):
        if not os.path.exists("credentials.json"):
            return None
        
        with open("credentials.json", "r") as file:
            credentials = json.load(file)
        
        if site in credentials:
            encrypted_password = credentials[site]["password"].encode()
            username = credentials[site]["username"]
            password = decrypt_data(encrypted_password, self.key)
            return username, password
        return None

    def setup_tor(self):
        # Configura o proxy SOCKS5 para usar o Tor
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket

        # Testa a conexão com o Tor
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()  # Use a senha se necessário
                controller.signal(Signal.NEWNYM)
                print("Conexão ao Tor estabelecida com sucesso.")
        except Exception as e:
            print("Erro ao conectar ao Tor:", e)

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None:
            qurl = self.default_home_url

        browser = QWebEngineView()
        browser.setUrl(qurl)

        i = self.browser.addTab(browser, label)
        self.browser.setCurrentIndex(i)

        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_url(qurl, browser))
        browser.loadFinished.connect(self.apply_dark_mode)

    def current_browser(self):
        return self.browser.currentWidget()

    def navigate_home(self):
        self.current_browser().setUrl(self.default_home_url)

    def navigate_to_url(self):
        url = self.url_bar.text().strip()
        if not url:
            return

        # Verifica se o URL é específico
        if url.startswith("youtube") or url == "youtube.com":
            self.current_browser().setUrl(QUrl("https://www.youtube.com"))
        elif url.startswith("example") or url == "example.com":
            self.current_browser().setUrl(QUrl("https://www.example.com"))
        elif url.startswith("http://") or url.startswith("https://"):
            self.current_browser().setUrl(QUrl(url))
        else:
            search_url = f"https://www.google.com/search?q={url}"
            self.current_browser().setUrl(QUrl(search_url))

    def update_url(self, qurl, browser=None):
        if browser != self.current_browser():
            return
        self.url_bar.setText(qurl.toString())

    def open_new_tab(self):
        self.add_new_tab(self.default_home_url, "New Tab")

    def close_current_tab(self):
        i = self.browser.currentIndex()
        if self.browser.count() < 2:
            return
        self.browser.removeTab(i)

    def apply_dark_theme(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(18, 18, 18))
        dark_palette.setColor(QPalette.WindowText, QColor(208, 208, 208))
        dark_palette.setColor(QPalette.Base, QColor(18, 18, 18))
        dark_palette.setColor(QPalette.AlternateBase, QColor(18, 18, 18))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(208, 208, 208))
        dark_palette.setColor(QPalette.ToolTipText, QColor(208, 208, 208))
        dark_palette.setColor(QPalette.Text, QColor(208, 208, 208))
        dark_palette.setColor(QPalette.Button, QColor(28, 28, 28))
        dark_palette.setColor(QPalette.ButtonText, QColor(208, 208, 208))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(187, 134, 252))
        dark_palette.setColor(QPalette.Highlight, QColor(187, 134, 252))
        dark_palette.setColor(QPalette.HighlightedText, QColor(18, 18, 18))

        QApplication.setPalette(dark_palette)
        self.setStyleSheet("QToolBar { background-color: #121212; border-bottom: 1px solid #333; }")
        self.browser.setStyleSheet("QTabWidget::pane { border-top: 2px solid #333; }")

    def apply_dark_mode(self):
        dark_mode_css = """
            * {
                background-color: #121212 !important;
                color: #e0e0e0 !important;
            }
            a {
                color: #bb86fc !important;
            }
            input, textarea {
                background-color: #333333 !important;
                color: #e0e0e0 !important;
                border: 1px solid #555555 !important;
            }
        """
        self.current_browser().page().runJavaScript(f"""
            (function() {{
                var style = document.createElement('style');
                style.type = 'text/css';
                style.appendChild(document.createTextNode("{dark_mode_css.replace('"', '\\"') }"));
                document.head.appendChild(style);
            }})();
        """)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            self.current_browser().back()
        super().keyPressEvent(event)

app = QApplication(sys.argv)
QApplication.setApplicationName("Navegador LLX")
window = Browser()
app.exec_()
