def __init__(self):
    self.token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not self.token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
    
    proxy_url = os.getenv("PROXY_URL", "")  
    if proxy_url:
        request = HTTPXRequest(proxy=proxy_url)
        self.application = Application.builder().token(self.token).request(request).build()
    else:
        self.application = Application.builder().token(self.token).build()
    # -------------------------
    
    self.yandex = YandexAssistant()
    self.max = MAXIntegration()