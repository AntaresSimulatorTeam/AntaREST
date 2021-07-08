class DenormalizationException(Exception):
    def __init__(self, msg: str):
        super(DenormalizationException, self).__init__(msg)
