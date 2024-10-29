from winreg import EnumValue
import gradio as gr
import webbrowser
import time
import pandas as pd



class UserInterface:
    def __init__(self, chat_fn=None, documentretrieval_fn=None) -> None:
        self._chatfunction = chat_fn
        self._documentfunction = documentretrieval_fn
        
    def process_chain(self, text):
        if self._chain_function:
            documents = self._chain_function(text)
            formatted_output = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])
            return formatted_output
        return "Chain function not configured"
        
    def render(self):
        try:
            port = 7860
            
            with gr.Blocks(fill_width=True, fill_height=True) as blocks:
                with gr.Row():
                    # Left column: Chat interface
                    with gr.Column(scale=1):
                        gr.Markdown("### Shopping list")
                        
                        initial_data = pd.DataFrame({
                                        "Column 1": ["", "", ""],
                                        "Column 2": ["", "", ""],
                                        "Column 3": ["", "", ""],
})
                        
                        self.data_frame_shoppingList = gr.DataFrame(value=initial_data, headers=["Column 1", "Column 2", "Column 3"], label="Editable Table", interactive=True)
                        self.submit_btn_shoppingList = gr.Button("Process Chain")

                    with gr.Column(scale=1):
                        self.chatbot = gr.Chatbot(value=[[None, "Hello you!"]])                       
                        self.msg = gr.Textbox(
                            label="Chat message",
                            placeholder="Type your message here...",
                            show_label=False
                        )
                        with gr.Row():
                            self.submit = gr.Button("Submit")
                            self.clear = gr.Button("Clear")
                    
                    # Right column: Chain input and document display
                    with gr.Column(scale=1):
                        gr.Markdown("### Document Chain")
                        self.text_input = gr.Textbox(
                            label="Enter text for document chain",
                            placeholder="Type your input here...",
                            show_label=False
                        )
                        self.submit_btn = gr.Button("Process Chain")
                        
                        self.data_frame = gr.DataFrame(headers=["Nr.", "Rezept"], datatype=["number", "str"], wrap=True)
                        
                        
                
                # Attach button event handlers
                self._attach_button_events()               
            
            # Launch the interface
            blocks.queue()
            blocks.launch(debug=True, show_api=False, inline=False, server_port=port, inbrowser=True)
            
        except Exception as e:
            print(e)
            raise e
    
    def _attach_button_events(self):
        """Attach event handlers to buttons."""
    
        # Chat submit and clear buttons
        self.submit.click(self._handle_chat_submit, [self.msg, self.chatbot], [self.msg, self.chatbot])
        self.msg.submit(self._handle_chat_submit, [self.msg, self.chatbot], [self.msg, self.chatbot])
        self.clear.click(self._handle_chat_clear, None, self.chatbot, queue=False)
    
        # Document chain process button
        self.submit_btn.click(fn=self._handle_process_chain, inputs=[self.text_input], outputs=[self.data_frame])


    def _handle_chat_submit(self, message, chat_history):
        """Handle chat submit event."""
        
        chat_history.append((message, ""))
       
        bot_message = self._chatfunction(message, chat_history)
                        
        for bot_message_part in bot_message:
            # Append each part of the bot's response to the history
            chat_history[-1] = (message, bot_message_part)        
            yield None, chat_history  # Yield updated history after each part
                        

    def _handle_chat_clear(self):
        """Handle chat clear button event."""
        return None


    def _handle_process_chain(self, text_input):
        """Handle the document chain processing."""
        # Your chain processing logic here
        listdata = self._documentfunction(text_input)
                
        data = [(i, receipe) for i, receipe in enumerate(listdata)]
        return data
            
        