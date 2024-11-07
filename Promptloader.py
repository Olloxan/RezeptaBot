

class Promploader():
    def __init__(self) -> None:
        self.directory = "Receipes/Prompts/"
        pass
    def read_from_file(self, filename:str) -> str:
        """Liest den Text aus einer Textdatei und gibt ihn zurück."""
        with open(filename, "r", encoding="utf-8") as file:
            text = file.read()
        print(f"Text aus {filename} geladen.")
        return text
