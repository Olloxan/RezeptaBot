import gradio as gr
from Rezeptabot import chat_gen
    

chatbot = gr.Chatbot(value = [[None, "Hello you!"]])
demo = gr.ChatInterface(fn=chat_gen, chatbot=chatbot).queue()

try:
    demo.launch(debug=True, show_api=False, inline=False)
    # demo.close()
except Exception as e:
    demo.close()
    print(e)
    raise e
