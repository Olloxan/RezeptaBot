import gradio as gr
import webbrowser
import time

class UserInterface:
    def __init__(self, chatfunction=None, chain_function=None) -> None:
        self._chatfunction = chatfunction
        self._chain_function = chain_function
        
    def process_chain(self, text):
        if self._chain_function:
            documents = self._chain_function(text)
            formatted_output = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])
            return formatted_output
        return "Chain function not configured"
        
    def render(self):
        try:
            port = 7860
            
            with gr.Blocks() as blocks:
                with gr.Row():
                    # Left column: Chat interface
                    with gr.Column(scale=1):
                        chatbot = gr.Chatbot(value=[[None, "Hello you!"]], height=600)
                        msg = gr.Textbox(
                            label="Chat message",
                            placeholder="Type your message here...",
                            show_label=False
                        )
                        with gr.Row():
                            submit = gr.Button("Submit")
                            clear = gr.Button("Clear")
                    
                    # Right column: Chain input and document display
                    with gr.Column(scale=1):
                        gr.Markdown("### Document Chain")
                        text_input = gr.Textbox(
                            label="Enter text for document chain",
                            placeholder="Type your input here...",
                            lines=3
                        )
                        submit_btn = gr.Button("Process Chain")
                        doc_output = gr.Textbox(
                            label="Documents",
                            lines=20,
                            max_lines=30,
                            show_copy_button=True
                        )
                
                # Chat functions
                def respond(message, chat_history):
                    bot_message = self._chatfunction(message, chat_history)
                    chat_history.append((message, bot_message))
                    return "", chat_history
                
                submit.click(
                    respond, 
                    [msg, chatbot], 
                    [msg, chatbot]
                )
                
                msg.submit(
                    respond, 
                    [msg, chatbot], 
                    [msg, chatbot]
                )
                
                clear.click(lambda: None, None, chatbot, queue=False)
                
                # Chain functions
                submit_btn.click(
                    fn=self.process_chain,
                    inputs=[text_input],
                    outputs=[doc_output]
                )
            
            # Launch the interface
            blocks.queue()
            blocks.launch(debug=True, show_api=False, inline=False, server_port=port, inbrowser=True)
            
        except Exception as e:
            print(e)
            raise e
    
    def open_browser(self, port):
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')