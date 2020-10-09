class HtmlException(Exception):
    def __init__(self, message: str, html_code_error: int):
        self.message = message
        self.html_code_error = html_code_error
