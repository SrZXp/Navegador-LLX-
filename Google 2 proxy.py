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
import random
import time

# Gera um negocio pra salvar uma chave de criptografia
def generate_key():
    return Fernet.generate_key()

# Carregar a chave de criptografia
def load_key():
    return open("secret.key", "rb").read()

# Salvar a chave de criptografia
def save_key(key):
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

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

        # Lista de proxy
        self.proxy_list = [
            ('HTTP', '54.94.208.156', 80),
            ('HTTP', '87.247.188.186', 8080),
            ('HTTP', '15.236.106.236', 3128),
            ('HTTP', '54.67.125.45', 3128),
            ('HTTP', '13.49.78.30', 5836),
            ('HTTP', '43.200.77.128', 3128),
            ('HTTP', '13.36.104.85', 80),
            ('HTTP', '44.219.175.186', 80),
            ('HTTP', '3.126.147.182', 3128),
            ('HTTP', '3.127.62.252', 80),
            ('HTTP', '72.10.160.170', 2657),
            ('HTTP', '15.152.45.72', 3128),
            ('HTTP', '160.86.242.23', 8080),
            ('HTTP', '223.135.156.183', 8080),
            ('HTTP', '43.134.68.153', 3128),
            ('HTTP', '13.37.89.201', 3128),
            ('HTTP', '46.51.249.135', 3128),
            ('HTTP', '18.185.169.150', 3128),
            ('HTTP', '3.123.150.192', 3128),
            ('HTTP', '3.37.125.76', 3128),
            ('HTTP', '3.122.84.99', 80),
            ('HTTP', '67.43.236.20', 10145),
            ('HTTP', '43.134.33.254', 3128),
            ('HTTP', '47.251.70.179', 80),
            ('HTTP', '13.59.156.167', 3128),
            ('HTTP', '52.16.232.164', 3128),
            ('HTTP', '184.169.154.119', 80),
            ('HTTP', '3.212.148.199', 3128)
        ]

        self.current_proxy_index = 0
        self.setup_proxy()

        # Barra di navegasao
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

        # atalhos 
        self.shortcut_new_tab = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_new_tab.activated.connect(self.open_new_tab)

        self.shortcut_close_tab = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut_close_tab.activated.connect(self.close_current_tab)

        self.shortcut_back = QShortcut(QKeySequence("Alt+Left"), self)
        self.shortcut_back.activated.connect(lambda: self.current_browser().back())

        self.shortcut_forward = QShortcut(QKeySequence("Alt+Right"), self)
        self.shortcut_forward.activated.connect(lambda: self.current_browser().forward())

        self.apply_dark_theme()

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

    def setup_proxy(self):
        # Config dos proxy
        proxy_type, host, port = self.proxy_list[self.current_proxy_index]
        if proxy_type == 'SOCKS5':
            socks.set_default_proxy(socks.SOCKS5, host, port)
        elif proxy_type == 'HTTP':
            socks.set_default_proxy(socks.HTTP, host, port)
        socket.socket = socks.socksocket

        # Cria um temporizador para o tempo limite de 20 segundos
        self.proxy_timer = QTimer()
        self.proxy_timer.setSingleShot(True)
        self.proxy_timer.timeout.connect(self.on_proxy_timeout)
        self.proxy_timer.start(20000)  # 20 segundos

        # Teste dos proxy em uma thread separada
        QTimer.singleShot(0, self.test_proxy_connection)

    def test_proxy_connection(self):
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()  
                controller.signal(Signal.NEWNYM)
                self.proxy_timer.stop()  # Para o temporizador se a conexão for bem-sucedida
                return True
        except Exception as e:
            return False

    def on_proxy_timeout(self):
        print(f"Tempo limite para o proxy atingido. Tentando o próximo proxy...")
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        self.setup_proxy()

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

        # deixa isso quieto, pprt
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

    def open_new_tab(self, i=None):
        if i == -1:
            self.add_new_tab()

    def close_current_tab(self, i=None):
        if self.browser.count() < 2:
            return

        if i is None:
            i = self.browser.currentIndex()

        self.browser.widget(i).deleteLater()
        self.browser.removeTab(i)

    def apply_dark_theme(self):
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)

    def apply_dark_mode(self):
        self.current_browser().page().runJavaScript("""
            (function() {
                var style = document.createElement('style');
                style.innerHTML = `
                    body, html {
                        background-color: #121212 !important;
                        color: #ffffff !important;
                    }
                    a {
                        color: #bb86fc !important;
                    }
                    .header, .footer, .nav {
                        background-color: #1f1f1f !important;
                    }
                `;
                document.head.appendChild(style);
            })();
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("LLX Browser")
    window = Browser()
    app.exec_()
