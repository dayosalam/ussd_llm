from ussd_llm.ussd import app
from ussd_llm.constants import PORT_LLM


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT_LLM, debug=True)