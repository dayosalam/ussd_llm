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

app = Flask(__name__)

response = ""



# Replace with your OpenAI or local LLM API key

GROQ_API_KEY = "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"
# Initialize LLM
llm_groq = ChatGroq(temperature=0, model="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY)

def query_llm():
    """Builds the LangChain pipeline."""
    template = """Based on the context below, write a simple response that would answer the user's question. 
    Use the following pieces of retrieved-context to answer the question. 
    If you don't know the answer, say that you don't know.
    Use three sentences maximum and keep the answer concise.
    In your response, go straight to answering.

    Question: {question}
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """
                You are a Super Intelligent chatbot with Advanced Capabilities. 
                You are a chatbot that can answer any question with a superhero joke.
                You are limited to 150 characters of response.
            """),
            MessagesPlaceholder(variable_name="history"),
            ("human", template),
        ]
    )

    memory = ConversationBufferMemory(return_messages=True)

    # LangChain pipeline
    rag_chain = (
        RunnablePassthrough.assign(
            history=RunnableLambda(lambda x: memory.load_memory_variables(x)["history"])
        )
        | prompt
        | llm_groq
        | StrOutputParser()
    )

    return rag_chain

def capture_output(user_input):
    # Capture the printed output from stream_graph_updates
    output = io.StringIO()
    with redirect_stdout(output):
        stream_graph_updates(user_input)
    return output.getvalue().strip().replace('Assistant: ', '')

@app.route('/')
def home():
    return render_template('ok.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        response = capture_output(user_message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
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
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")

            response = stream_graph_updates(user_input)
        except:
            # Fallback if input() is not available
            user_input = "What do you know about LangGraph?"
            print("User: " + user_input)
            response = stream_graph_updates(user_input)
  
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)  # `host="0.0.0.0"` allows external access