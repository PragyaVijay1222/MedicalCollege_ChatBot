from flask import Flask, request, jsonify, render_template
import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model

app = Flask(__name__)

lemmatizer = WordNetLemmatizer()

with open('intents.json', encoding='utf-8') as file:
    intents = json.load(file)

words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = load_model('chatbot_model.h5')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.10
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def get_response(intents_list, intents_json):
    if len(intents_list) == 0:
        return "Maaf kijiye, mujhe samajh nahi aaya. Kya aap apna prashn dobara poochhna chahenge?"
    tag = intents_list[0]['intent']
    for i in intents_json['intents']:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    return result

def handle_special_responses(user_message):
    positive_responses = ["haan", "yes", "tell me more", "kya hai", "batao"]
    negative_responses = ["no", "nahi"]

    msg_lower = user_message.lower().strip()

    if any(phrase in msg_lower for phrase in positive_responses):
        return "Thik hai! Aage ka batati hoon."

    elif any(phrase in msg_lower for phrase in negative_responses):
        return "Koi baat nahi! Jab aapko zarurat ho, puchh lijiyega. Dhanyawaad!"

    else:
        return None  


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def get_bot_response():
    user_message = request.json.get("message")

    special_reply = handle_special_responses(user_message)
    if special_reply:
        return jsonify({"response": special_reply})

    ints = predict_class(user_message)
    response = get_response(ints, intents)
    return jsonify({"response": response})

if __name__ == "__main__":
    mode = input("Enter 'api' for web mode, or 'cli' for console mode: ").lower()

    if mode == "cli":
        print("Console chatbot mode. Type 'exit' or 'quit' to stop.\n")
        while True:
            message = input("You: ")
            if message.lower() in ["exit", "quit", "stop", "band karo"]:
                print("Bot: Dhanyavaad! Aapka din shubh ho.")
                break
            ints = predict_class(message)
            res = get_response(ints, intents)
            print("Bot:", res)
        print("done")
    else:
        print("Starting API server...")
        app.run(debug=True)
