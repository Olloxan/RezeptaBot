from langchain_core.runnables import Runnable


class RunnableBase(Runnable):
    def __init__(self, name):
        self.name = name

    def run(self):
        raise NotImplementedError("run() method must be implemented in subclass")

    def invoke(self, state: dict):
        pass

    def __str__(self):
        return self.name
    
    def LogMessage(self, message:str):
        self.logger.LogMessage(message, self)
        
    def LogException(self, exception:Exception, message:str):
        self.logger.LogException(exception, message, self)
