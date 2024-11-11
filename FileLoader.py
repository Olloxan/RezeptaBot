

class FileLoader():
    def __init__(self) -> None:
        self.directory = "Receipes/Prompts/"
        pass
    
    def read_from_file(self, filename:str) -> str:        
        with open(self.directory + filename, "r", encoding="utf-8") as file:
            text = file.read()
        print(f"Text aus {filename} geladen.")
        return text
