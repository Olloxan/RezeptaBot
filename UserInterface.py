from typing import List
import gradio as gr
import pandas as pd

from Utils import FileLoader
from Utils import ConfigManager

class UserInterface:
    def __init__(self, chat_fn=None, doc_retrieval_fn=None) -> None:
        self._chat_function = chat_fn        
        self._doc_retrieval_function = doc_retrieval_fn
        self.fileloader = FileLoader()
        self.config = ConfigManager()
        
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
                    # Left column: Week Plan Table
                    with gr.Column(scale=1):
                        gr.Markdown("### Week Plan")
                        
                        saved_data = self.config.read("initial_data")
                        if saved_data:  # Ensure the key exists
                            initial_data = pd.read_json(saved_data, orient="split")
                        else:
                            initial_data = pd.DataFrame({
                            "Tag": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag", "Montag"],
                            "Morgens": ["", "", "", "", "", "", "", ""],  
                            "Mittags": ["", "", "", "", "", "", "", ""],
                            "Abends": ["", "", "", "", "", "", "", ""],
                            "Nachmittags": ["", "", "", "", "", "", "", ""]
                            })
                        
                        # "Tag": ["Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag", "Montag", "Dienstag", "Mittwoch"]
                        # initial_data = pd.DataFrame({
                        # "Tag": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag", "Montag"],
                        # "Morgens": ["Pudding Oats", "Pudding Oats", "Pudding Oats", "Gebratene Haferflocken", "Gebratene Haferflocken", "Waffeln mit Sojajoghurt", "Waffeln mit Sojajoghurt", "Gebratene Haferflocken",],  
                        # "Mittags": ["", "Saitan Braten", "Saitan Braten", "Saitan Braten", "Feta Pasta", "Quinoa Bowl", "", "",],
                        # "Abends": ["Brokkoli Nudeln", "Brokkoli Nudeln", "", "Feta Pasta", "Feta Pasta", "Quinoa Bowl", "", "",],
                        # "Nachmittags": ["Brombeer-Smoothie", "Brombeer-Smoothie", "Brombeer-Smoothie", "Brombeer-Smoothie", "Brombeer-Smoothie", "Brombeer-Smoothie", "Brombeer-Smoothie", "",]
                        # })
                        
                        self.data_frame_weekplan = gr.DataFrame(value=initial_data, headers=["Tag", "Morgens", "Mittags", "Abends", "Nachmittags"], label="Editable Table", interactive=True, show_label=False)
                        self.submit_btn_weekplan = gr.Button("Process Week Plan")
                    
                    # Middle column: Chatbot
                    with gr.Column(scale=1):
                        self.chatbot = gr.Chatbot(value=[[None, "Hello you!"]], max_height=1000, min_height=800)                       
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
                        gr.Markdown("### Document Retrieval")
                        self.retrieval_input = gr.Textbox(
                            label="Enter text for document chain",
                            placeholder="Type your input here...",
                            show_label=False,
                            value=self.config.read("last_retrieval_input")
                        )
                        self.submit_btn_retrieve = gr.Button("Retrieve Recipes")
                        
                        initial_data = pd.DataFrame({
                                        "Nr.": [""],
                                        "Rezept": [""]                                        
                                        })

                        self.data_frame_retrieval = gr.DataFrame(value=initial_data, headers=["Nr.", "Rezept", "Score"], datatype=["number", "str", "number"], wrap=True)
                        
                        self.receipe_selection = gr.Textbox(
                            label="Enter text for document chain",
                            placeholder="Type your input here...",
                            show_label=False,
                            value=self.config.read("last_receipe_selection")
                        )
                        self.submit_btn_receipe_select = gr.Button("Retrieve Recipes")
                
                # Attach button event handlers
                self._attach_button_events()               
            
            # Launch the interface
            blocks.queue()
            blocks.launch(debug=True, show_api=False, inline=False, inbrowser=True)
            
        except Exception as e:
            print(e)
            raise e
    
###################### attach events ######################
    def _attach_button_events(self):
        """Attach event handlers to buttons."""
    
        # Weekly plan dataframe
        self.submit_btn_weekplan.click(fn=self._handle_dataframe_contents, inputs=[self.data_frame_weekplan, self.chatbot], outputs=self.chatbot)

        # Chat submit and clear buttons
        self.submit.click(fn=self._handle_chat_submit, inputs=[self.msg, self.chatbot], outputs=[self.msg, self.chatbot])
        self.msg.submit(fn=self._handle_chat_submit, inputs=[self.msg, self.chatbot], outputs=[self.msg, self.chatbot])
        self.clear.click(fn=self._handle_chat_clear, inputs=None, outputs=self.chatbot, queue=False)
    
        # Document retrieval button
        self.retrieval_input.submit(fn=self._retrieve_from_vectorstore, inputs=self.retrieval_input, outputs=self.data_frame_retrieval)
        self.submit_btn_retrieve.click(fn=self._retrieve_from_vectorstore, inputs=self.retrieval_input, outputs=self.data_frame_retrieval)        
        
        self.receipe_selection.submit(fn=self._handle_receipe_choice, inputs=[self.receipe_selection, self.chatbot], outputs=[self.receipe_selection, self.chatbot])
        self.submit_btn_receipe_select.click(fn=self._handle_receipe_choice, inputs=[self.receipe_selection, self.chatbot],outputs=[self.receipe_selection, self.chatbot])

###################### left side: Week plan ######################
    def _handle_dataframe_contents(self, dataframe:pd.DataFrame, chat_history:List[tuple]):
        """Return the DataFrame (Pandas Dataframe)."""        
        # soll an das Netzwerk gesendet werden, um die Einkaufsliste zu erstellen
        self.config.write("initial_data", dataframe.to_json(orient="split", force_ascii=False))
        
        self.fileloader.store_object_on_disk(dataframe, "logs/temp/weekplan.json")
        dataframe.to_csv("logs/weekplan.csv", index=False)
        json_data = dataframe.to_json(orient="split")
        message = f"shoppinglist:{json_data}"
        
        chat_history.append(("None", ""))
        # call zum chatbot mit dem serialisierten json
        bot_message = self._chat_function(message, chat_history)
        
        for bot_message_part in bot_message:
            # Append each part of the bot's response to the history
            chat_history[-1] = ("test", bot_message_part)        
            yield chat_history    
                

###################### center: Chatbot ######################
    def _handle_chat_submit(self, message:str, chat_history:List[tuple]):
        """Handle chat submit event.
        message: str
        history: [[(user) None, (agent) "Hello you!"]] (List of Lists)
        """        
       
       
        chat_history.append((message, ""))
       
        bot_message = self._chat_function(message, chat_history)
                        
        for bot_message_part in bot_message:
            # Append each part of the bot's response to the history
            chat_history[-1] = (message, bot_message_part)        
            yield None, chat_history                          

    def _handle_chat_clear(self):
        """Handle chat clear button event."""
        return None

###################### right side: Document retrieval ######################
    def _retrieve_from_vectorstore(self, text_input: str) -> List[tuple]: 
        """Document retrieval: Input any ingredient and get corresponding recipes"""       
        self.config.write("last_retrieval_input", text_input)
        listdata : list[tuple[str, float]] = self._doc_retrieval_function(text_input)                
        data = [(index, receipe, score) for index, (receipe, score) in enumerate(listdata)]
        return data
    
    def _handle_receipe_choice(self, index:str, chat_history:List[tuple]):
        """Select any index of displayed recipes and return the whole week including the name of the source document.
        Uses a branch of the chatbot"""
        self.config.write("last_receipe_selection", index)
        message = f"retrieval:{index}"
        selection = f"Auswahl: {index}"
        chat_history.append((selection, ""))
        
        bot_message = self._chat_function(message, chat_history)
        
        for bot_message_part in bot_message:
            # Append each part of the bot's response to the history
            chat_history[-1] = (selection, bot_message_part)        
            yield None, chat_history   
        
        
    def _build_initial_data(self):
        pass
        