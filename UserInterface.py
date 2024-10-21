import gradio as gr
from ui.configuration import Configuration
import webbrowser
import threading

import time
    

class UserInterface:
    def __init__(self, chatfunction=None) -> None:
        self._interface = None
        self._chatfunction = chatfunction           
        self.chatbot = gr.Chatbot(value = [[None, "Hello you!"]])
        self.demo = gr.ChatInterface(fn=self._chatfunction, chatbot=self.chatbot).queue()
        pass
    
    def _open_browser(self, port):
        # Wait a bit to ensure the server has started
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')
                      
    def render(self):
        try:
            port = 7860                        
            self.demo.launch(debug=True, show_api=False, inline=False, server_port=port, inbrowser=True )
            # demo.close()
        except Exception as e:
            self.demo.close()
            print(e)
            raise e
     
    