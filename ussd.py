from flask import Flask, request
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import requests

app = Flask(__name__)

response = ""



# Replace with your OpenAI or local LLM API key

GROQ_API_KEY = "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"
llm_groq = ChatGroq(temperature=0, model="llama-3.1-8b-instant",
               groq_api_key=GROQ_API_KEY)



def query_llm():
    template = """Based on the context below, write a simple response that would answer the user's question. 
            Use the following pieces of retrieved-context to answer the question. 
            If you don't know the answer, say that you don't know.
            Use three sentences maximum and keep the answer concise.
            In your response, go straight to answering.

    Question: {question}
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system",  """

    You are A Super Intelligent chatbot with Advanced Capabilities. You are a chatbot that can answer any question with a super hero joke.\
        You are limited to 150 characters of response
   
        "\n\n"
    """),
    MessagesPlaceholder(variable_name="history"),
            ("human", template),
        ]
    )
    # {"context": retriever | format_docs, "question": RunnablePassthrough()}
        
    memory = ConversationBufferMemory(return_messages=True)
     # Chain
    rag_chain = (
        RunnablePassthrough.assign(
            history=RunnableLambda(
                lambda x: memory.load_memory_variables(x)["history"])
        )
        | prompt
        | llm_groq
        | StrOutputParser()
    )
    
    return rag_chain

@app.route('/', methods=['POST', 'GET'])
def ussd_callback():
  global response
  session_id = request.values.get("sessionId", None)
  service_code = request.values.get("serviceCode", None)
  phone_number = request.values.get("phoneNumber", None)
  text = request.values.get("text", "default")
  rag_chain = query_llm()
  
  
  if text == "":
    response = "CON Welcome to AI Chatbot.\nEnter your query:"
  else:
    llm_response = rag_chain.invoke({"question": text})
    response = f"END {llm_response[:160]}"  # USSD messages are limited to ~160 chars

    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)