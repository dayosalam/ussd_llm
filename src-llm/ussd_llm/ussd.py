from flask import Flask, request, Request
import requests
from llm import stream_graph_updates
from typing import Literal, TypedDict
from ussd_llm.constants import DEV_PAY, PORT_RUST, QR_PAY, DOMAIN
from solders.signature import Signature
import json
import re

SANDBOX_API_KEY = (
    "atsk_b1b293e92ed2fc4b5b843ea5a4ed6fabfbb7c0c6605c6047efe9799878b38e3c36e72479"
)
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


@app.route("/", methods=["POST", "GET"])
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
                response = (
                    f"CON {ai_response}"
                    if ai_response
                    else "END Sorry, no response available."
                )
            except Exception as e:
                print(f"Error: {e}")  # Debugging
                response = "END Sorry, something went wrong."

    print(f"Sending Response: {response}")  # Debugging
    return response  # Ensure a valid response is always returned


@app.route("/sms_callback", methods=["POST"])
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
            messages = (
                f"{ai_response}" if ai_response else "END Sorry, no response available."
            )
            transaction_type, amount, wallet_address = transaction(ai_response)
        except Exception as e:
            print(f"Error: {e}")  # Debugging
            messages = "END Sorry, something went wrong."

    response_sms(request.form["from"], messages)
    return "Success", 201

def transaction(text):
    # Extract transaction type
    transaction_type_match = re.search(r'Transaction Type:\s*(.+)', text)
    transaction_type = transaction_type_match.group(1) if transaction_type_match else None

    # Extract amount
    amount_match = re.search(r'Transaction Amount:\s*([\d.]+)', text)
    amount = float(amount_match.group(1)) if amount_match else None

    # Extract wallet address
    wallet_match = re.search(r'Recipient Wallet Address:\s*([A-Za-z0-9]+)', text)
    wallet_address = wallet_match.group(1) if wallet_match else None

    # Print results
    print("Transaction Type:", transaction_type)
    print("Amount:", amount)
    print("Wallet Address:", wallet_address)
    
    return transaction_type, amount, wallet_address

def response_sms(recipient_phone_number, message):
    requests.post(
        "https://api.sandbox.africastalking.com/version1/messaging",
        data={
            "username": "sandbox",
            "to": recipient_phone_number,
            "message": message,
            "from": "47532",
        },
        headers={
            "apiKey": SANDBOX_API_KEY,
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )


class ServerResponse(TypedDict):
    status: Literal["success", "failure"]
    message: str
    code: int
    json: dict


def build_fail_response(parameter: str) -> ServerResponse:
    return ServerResponse(
        status="failure",
        message=f"Bad Request. Parameter {parameter} is required yet missing.",
        code=400,
        json={},
    )


def build_fail_response_with_msg(msg: str, code: int) -> ServerResponse:
    return ServerResponse(status="failure", message=msg, code=code, json={})


def multi_pay(payment_endpoint: str, amount: float | None = None, wallet_address: str | None = None) -> ServerResponse:
    if amount is None:
        json_params = request.get_json()
        amount = json_params.get("amount")
        if amount is None:
            return build_fail_response("amount")
    
    if wallet_address is None:
        json_params = request.get_json()
        recipient = json_params.get("recipient")
        if recipient is None:
            return build_fail_response("recipient")
        wallet_address = recipient

    body = {
        "recipient": wallet_address,
        "amount": amount,
    }
    response = requests.post(payment_endpoint, json=body)
    try:
        response.raise_for_status()
    except requests.RequestException as e:
        return build_fail_response_with_msg(
            f"Internal server error occurred. Failed to complete payment due to error {e}",
            code=500,
        )

    try:
        response_body = response.json()
    except json.JSONDecodeError as e:
        return build_fail_response_with_msg(
            msg=f"Internal server error occurred. Failed to decode response body due to error {e}",
            code=500,
        )

    return ServerResponse(status="success", message="", code=200, json=response_body)


@app.route(DEV_PAY, methods=["POST"])
def dev_pay_callback() -> ServerResponse:
    payment_endpoint: str = f"{DOMAIN}:{PORT_RUST}{DEV_PAY}"
    server_response = multi_pay(payment_endpoint)
    if server_response["status"] == "failure":
        return server_response

    json_body = server_response["json"]
    signature_arr = json_body.get("signature")
    if signature_arr is None:
        return build_fail_response_with_msg("Internal Server error occurred. Unable to retrieve signature from the json response from the payment backend.", code=500)
    signature_bytes: bytes = bytes(signature_arr)
    signature: Signature = Signature.from_bytes(signature_bytes)
    return ServerResponse(
        status="success",
        message="Payment completed successfully",
        code=200,
        json={"signature": str(signature)},
    )

def dev_pay(amount: float, wallet_address: str) -> ServerResponse:
    payment_endpoint: str = f"{DOMAIN}:{PORT_RUST}{DEV_PAY}"
    server_response = multi_pay(payment_endpoint, amount, wallet_address)
    if server_response["status"] == "failure":
        return server_response

    json_body = server_response["json"]
    signature_arr = json_body.get("signature")
    if signature_arr is None:
        return build_fail_response_with_msg(
            "Internal Server error occurred. Unable to retrieve signature from the json response from the payment backend.",
            code=500,
        )
    signature_bytes: bytes = bytes(signature_arr)
    signature: Signature = Signature.from_bytes(signature_bytes)
    return ServerResponse(
        status="success",
        message="Payment completed successfully",
        code=200,
        json={"signature": str(signature)},
    )

@app.route(QR_PAY, methods=["POST"])
def qr_pay_callback() -> ServerResponse:
    payment_endpoint: str = f"{DOMAIN}:{PORT_RUST}{QR_PAY}"
    server_response = multi_pay(payment_endpoint)
    if server_response["status"] == "failure":
        return server_response

    json_body = server_response["json"]
    
    return ServerResponse(status="success", message="Generated Payment QR Code successfully. Decode the QR Code from base64 into bytes and render an image from those bytes. The resulting image can be scanned by any wallet provider to finalize the payment.", json=json_body)

def qr_pay(amount: float, wallet_address: str) -> ServerResponse:
    payment_endpoint: str = f"{DOMAIN}:{PORT_RUST}{QR_PAY}"
    server_response = multi_pay(payment_endpoint, amount, wallet_address)
    if server_response["status"] == "failure":
        return server_response

    json_body = server_response["json"]

    return ServerResponse(
        status="success",
        message="Generated Payment QR Code successfully. Decode the QR Code from base64 into bytes and render an image from those bytes. The resulting image can be scanned by any wallet provider to finalize the payment.",
        json=json_body,
    )

# if __name__ == '__main__':
#     app.run(host="0.0.0.0", port=5000, debug=True)  # `host="0.0.0.0"` allows external access
