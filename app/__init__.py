def __init__(self):
    self.token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not self.token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
    
    proxy_url = os.getenv("PROXY_URL", "")  
    if proxy_url:
        request = HTTPXRequest(proxy=proxy_url)
        self.application = Application.builder().token(self.token).request(request).build()
    else:
     try:
      self.application = Application.builder().token(self.token).connect_timeout(60).read_timeout(60).build()
     except Exception as e:
      logging.warning(f"Ошибка подключения: {e}")
    # Пробуем с прокси (если есть)
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        request = HTTPXRequest(proxy=proxy_url)
        self.application = Application.builder().token(self.token).request(request).build()
    else:
        raise
    # -------------------------
    
    self.yandex = YandexAssistant()
    self.max = MAXIntegration()