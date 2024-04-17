from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import ollama

app = Flask(__name__)
app.config['SECRET_KEY'] = 'our_secret_llm_persuasion_key'
socketio = SocketIO(app)

@app.route('/')
def index():

    return render_template('chat.html')  

@socketio.on('message_from_client')
def handle_message_from_client(json):
    # json has two keys: 'text' and 'sender'
    # pull out 'text' from it, and pass it into the LLM
    # and pass the sid so it knows which socket to emit to
    get_next_response(json['text'], request.sid)

# for scalability, this should run on redis when we run this on gunicorn
def get_next_response(user_message, sid):
    messages = session['messages'].copy()
    messages.append({'role' : 'user', 'content' : user_message})
    response = ollama.chat(
        model='llama2:7b-chat-q2_K',
        messages=messages
    )
    text_response = response['message']['content']
    messages.append({'role' : 'assistant', 'content' : text_response})
    session['messages'] = messages
    mess = {}
    mess['sender'] = "other_player"
    mess['text'] = text_response
    emit('message_from_server', mess, to=sid)  

@socketio.on('connect')
def test_connect():
    # set custom instruction
    llm_instructions = {"role" : "assistant", "content" : "You are an expert on chatbot development. Your preferred tools are flask, postgres and redis, running dockerized. Answer user's questions to the best of your knowledge."}
    # add it to the messages stored in cookie for now
    session['messages'] = [llm_instructions]
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
