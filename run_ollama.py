from flask import Flask, request, jsonify
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

app = Flask(__name__)

template = """

You are a very high IQ Assisatnt assisting you dev boss to examine and introspect what he did at his terminal today. You will be given a set of terminal command logs of his actions he performed over the last 45 mins and you should be
able to understand the intent of his work and develop a mental model of tasks he tried to complete it today. You have to return the following things:
You have to return a summary of the tasks he tried to complete today and give him a self-reflection of his work today.

Boss: {user_message}
Answer:
"""

prompt = ChatPromptTemplate.from_template(template)
model_name = 'gemma3:1b'
model = OllamaLLM(model=model_name, device='mps')
chain = prompt | model

conversations = {}


@app.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint to send messages to the chatbot
    Expects JSON: {"message": "user input"}
    """
    try:
        data = request.get_json()
        print(f'Bytes encoded message: {data["message_b64"]}')
        #data is in be64 encoded string, so we need to decode it
        import base64
        import json
        new_data = base64.b64decode(data['message_b64']).decode('utf-8')
        print(f'New message: {new_data}')
        # if not new_data or 'message' not in new_data:
        #     print('Missing message in request')
        #     return jsonify({'error': 'Missing message in request'}), 400
        
        # new_data = json.loads(new_data)
        user_message = new_data
        print(f'User message: {user_message}')
        
        # Direct invocation without any context
        result = chain.invoke({
            'user_message': user_message
        })

        print(f'Result: {result}')
        
        return jsonify({
            'response': result
        })

        import subprocess,shlex
        subprocess.run(shlex.split(f'ollama stop {model_name}'))
    
    except Exception as e:
        print(f'Error: {e}')
        # return jsonify({'error': str(e)}), 500
        raise e

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """
    Reset a conversation session
    Expects JSON: {"session_id": "session_id"}
    """
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    if session_id in conversations:
        conversations[session_id] = ""
    
    return jsonify({'message': f'Session {session_id} reset successfully'})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'model': 'llama3.2'})

if __name__ == '__main__':
    import sys
    
    # Get port from command line argument or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    print(f"Starting server on port {port}")
    print(f"Chat endpoint: http://0.0.0.0:{port}/chat")
    
    # Run on 0.0.0.0 to allow external connections
    app.run(host='0.0.0.0', port=port, debug=True)
