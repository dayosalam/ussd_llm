from flask import Flask, request
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import requests
from llm import stream_graph_updates
from flask import Flask, render_template, request, jsonify
from functools import partial
from contextlib import redirect_stdout
import io

SANDBOX_API_KEY = "atsk_b1b293e92ed2fc4b5b843ea5a4ed6fabfbb7c0c6605c6047efe9799878b38e3c36e72479"
app = Flask(__name__)

response = ""



# Replace with your OpenAI or local LLM API key

# GROQ_API_KEY = "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"
# # Initialize LLM
# llm_groq = ChatGroq(temperature=0, model="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY)

# def query_llm():
#     """Builds the LangChain pipeline."""
#     template = """Based on the context below, write a simple response that would answer the user's question. 
#     Use the following pieces of retrieved-context to answer the question. 
#     If you don't know the answer, say that you don't know.
#     Use three sentences maximum and keep the answer concise.
#     In your response, go straight to answering.

#     Question: {question}
#     """

#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", """
#                 You are a Super Intelligent chatbot with Advanced Capabilities. 
#                 You are a chatbot that can answer any question with a superhero joke.
#                 You are limited to 150 characters of response.
#             """),
#             MessagesPlaceholder(variable_name="history"),
#             ("human", template),
#         ]
#     )

#     memory = ConversationBufferMemory(return_messages=True)

#     # LangChain pipeline
#     rag_chain = (
#         RunnablePassthrough.assign(
#             history=RunnableLambda(lambda x: memory.load_memory_variables(x)["history"])
#         )
#         | prompt
#         | llm_groq
#         | StrOutputParser()
#     )

#     return rag_chain

# def capture_output(user_input):
#     # Capture the printed output from stream_graph_updates
#     output = io.StringIO()
#     with redirect_stdout(output):
#         stream_graph_updates(user_input)
#     return output.getvalue().strip().replace('Assistant: ', '')

# @app.route('/')
# def home():
#     return render_template('ok.html')

# @app.route('/chat', methods=['POST'])
# def chat():
#     data = request.json
#     user_message = data.get('message', '')
    
#     if not user_message:
#         return jsonify({'error': 'No message provided'}), 400

#     try:
#         response = capture_output(user_message)
#         return jsonify({'response': response})
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
@app.route('/', methods=['POST', 'GET'])
def ussd_callback():
    """Handles USSD interactions."""
    session_id = request.values.get("sessionId")
    service_code = request.values.get("serviceCode")
    phone_number = request.values.get("phoneNumber")
    text = request.values.get("text", "").strip()

    if not text:
        response = "CON Welcome to AI Chatbot.\nEnter your query:"
    else:
        if text.lower() in ["quit", "exit", "q"]:
            response = "END Goodbye! Thanks for using AI Chatbot."
        else:
            try:
                ai_response = stream_graph_updates(text)
                response = f"CON {ai_response}" if ai_response else "END Sorry, no response available."
            except Exception as e:
                print(f"Error: {e}")  # Debugging
                response = "END Sorry, something went wrong."

    print(f"Sending Response: {response}")  # Debugging
    return response  # Ensure a valid response is always returned


@app.route('/sms_callback', methods=['POST'])
def sms_callback():
    print(request.method)
    print(request.form)
    print(request.form["from"])
    text = request.form["text"]
    phone_number = request.form["from"]
    print(text)
    if text.lower() in ["quit", "exit", "q"]:
            messages = "END Goodbye! Thanks for using AI Chatbot."
    else:
        try:
            ai_response = stream_graph_updates(text, phone_number)
            messages = f"{ai_response}" if ai_response else "END Sorry, no response available."
        except Exception as e:
            print(f"Error: {e}")  # Debugging
            messages = "END Sorry, something went wrong."
    
    response_sms(request.form["from"], messages)
    return "Success", 201

def response_sms(recipient_phone_number, message):
    requests.post(
        "https://api.sandbox.africastalking.com/version1/messaging",
        data = {
            "username": "sandbox",
            "to": recipient_phone_number,
            "message": message,
            "from": "47532"
            
        },
        headers = {
            "apiKey": SANDBOX_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
            
}
    )
    



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)  # `host="0.0.0.0"` allows external access