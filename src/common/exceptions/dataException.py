class DataException(Exception):
    #def __init__(self, *args: object) -> None:
    #    super().__init__(*args)

    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return self.message
