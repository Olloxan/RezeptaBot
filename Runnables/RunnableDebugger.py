from langchain_core.runnables import RunnableLambda
from functools import partial
from rich.style import Style
from rich.console import Console
import pickle

from Utils import Logger

console = Console()
base_style = Style(color="#76B900", bold=True)
prettyPrint = partial(console.print, style=base_style)

class RunnableDebugger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = Logger()
        return cls._instance

    def Runnable_PrintTextWithLabel(self, label="State: ", module=None):
        def print_and_return(x, label="", module=None):
            if module:
                self.logger.LogMessage(f"{label}{x}", instance=module)
            else:
                self.logger.LogMessage(f"{label}{x}")
            return x
        return RunnableLambda(partial(print_and_return, label=label, module=module))

    def Runnable_PrintStructureWithLabel(self, label="State: "):
        def print_and_return(x, label=""):
            prettyPrint(label, x)
            self.logger.LogMessage(f"{label}{x}")
            return x
        return RunnableLambda(partial(print_and_return, label=label))

    ### Data specific debuggers
   

