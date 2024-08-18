import random
import csv
import pyttsx3
import speech_recognition as sr
from flask import Flask, request, render_template, session, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'

characters = []

def load_characters(filename):
    global characters
    characters = []
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            characters.append(row)
    return characters

def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return text.lower()
        except sr.UnknownValueError:
            speak("I didn't catch that. Please repeat.")
            return listen()
        except sr.RequestError:
            speak("There seems to be an issue with the speech service.")
            return "I don't know"

def filter_characters(characters, attribute, value):
    if value == 'idk':
        return characters
    elif value == 'yes':
        return [char for char in characters if char[attribute] == session['current_value']]
    elif value == 'no':
        return [char for char in characters if char[attribute] != session['current_value']]

def is_answer_yes(a):
    return a.lower() in ['yes', 'y']

def ask_question(attribute, value):
    question = f"Is your character's {attribute} {value}? (yes, no, or I don't know): "
    speak(question)
    response = listen()
    while response not in ['yes', 'no', "i don't know"]:
        speak("Invalid response. Please answer with 'yes', 'no', or 'I don't know'.")
        response = listen()
    return response

def guess_character(characters):
    if len(characters) == 1:
        speak(f"Your character is {characters[0]['name']}!")
        return
    elif len(characters) == 0:
        speak("Unable to determine your character. Please try again.")
        return

    attributes = ['hair color', 'element', 'weapon', 'region', 'physic', 'height', 'rarity', 'birthday', 'affiliation', 'known as', 'hair model', 'eye color', 'identic with', 'clothing color', 'personalities', 'role']
    random.shuffle(attributes)
    
    # Always ask about hair color first
    hair_color_values = list(set(character['hair color'] for character in characters))
    random.shuffle(hair_color_values)
    for hair_color in hair_color_values:
        response = ask_question('hair color', hair_color)
        if response == 'yes':
            filtered_characters = [char for char in characters if char['hair color'] == hair_color]
            break
        elif response == 'no':
            filtered_characters = [char for char in characters if char['hair color'] != hair_color]
        else:
            filtered_characters = characters  # If user doesn't know, don't filter
    
    # Ask other questions for more specific information
    for attribute in attributes:
        if attribute == 'hair color':
            continue  # Already asked
        values = list(set(character[attribute] for character in filtered_characters))
        random.shuffle(values)
        if len(values) == 1:
            continue
        
        for value in values:
            response = ask_question(attribute, value)
            if response == 'yes':
                filtered_characters = [char for char in filtered_characters if char[attribute] == value]
                guess_character(filtered_characters)
                return
            elif response == 'no':
                filtered_characters = [char for char in filtered_characters if char[attribute] != value]
            else:
                continue  # If user doesn't know, skip to the next value

    # If all values for all attributes are the same, ask the first attribute
    attribute = attributes[0]
    value = filtered_characters[0][attribute]
    response = ask_question(attribute, value)
    if response == 'yes':
        speak(f"Your character is {filtered_characters[0]['name']}!")
    else:
        speak("Unable to determine your character. Please try again.")

@app.route('/')
def username_input():
    return render_template('username.html')

@app.route('/set_username', methods=['POST'])
def set_username():
    session['username'] = request.form.get('username')
    return redirect(url_for('index'))

@app.route('/index')
def index():
    username = session.get('username', 'Guest')
    return render_template('index.html', username=username)

@app.route('/start', methods=['POST'])
def start():
    session['characters'] = load_characters('gichar.csv')
    session['attributes'] = ['hair color', 'element', 'weapon', 'region', 'physic', 'height', 'rarity', 'birthday', 'affiliation', 'known as', 'hair model', 'eye color', 'identic with', 'clothing color', 'personalities', 'role']
    session['asked_questions'] = []
    return redirect(url_for('question'))

@app.route('/question', methods=['GET', 'POST'])
def question():
    if request.method == 'POST':
        answer = request.form.get('answer')
        attribute = session['current_attribute']
        session['characters'] = filter_characters(session['characters'], attribute, answer)

        if len(session['characters']) == 1:
            return redirect(url_for('result'))
        elif len(session['characters']) == 0:
            return render_template('failure.html')

    attributes = session['attributes']
    random.shuffle(attributes)

    # Always ask about hair color first if not already asked
    if 'hair color' not in session['asked_questions']:
        attribute = 'hair color'
    else:
        attribute = attributes[0]
        for attr in attributes:
            if attr not in session['asked_questions']:
                attribute = attr
                break

    values = list(set(character[attribute] for character in session['characters']))
    random.shuffle(values)
    session['current_attribute'] = attribute
    session['current_value'] = values[0]
    session['asked_questions'].append(attribute)
    
    question_text = f"Is your character's {attribute} {values[0]}?"
    return render_template('question.html', question=question_text)

@app.route('/voice_question', methods=['GET', 'POST'])
def voice_question():
    if request.method == 'POST':
        answer = request.form.get('answer')
        attribute = session['current_attribute']
        session['characters'] = filter_characters(session['characters'], attribute, answer)

        if len(session['characters']) == 1:
            return redirect(url_for('result'))
        elif len(session['characters']) == 0:
            return render_template('failure.html')

    attributes = session['attributes']
    random.shuffle(attributes)

    # Always ask about hair color first if not already asked
    if 'hair color' not in session['asked_questions']:
        attribute = 'hair color'
    else:
        attribute = attributes[0]
        for attr in attributes:
            if attr not in session['asked_questions']:
                attribute = attr
                break

    values = list(set(character[attribute] for character in session['characters']))
    random.shuffle(values)
    session['current_attribute'] = attribute
    session['current_value'] = values[0]
    session['asked_questions'].append(attribute)
    
    question_text = f"Is your character's {attribute} {values[0]}?"
    return render_template('voice_question.html', question=question_text)

@app.route('/result')
def result():
    character = session['characters'][0]
    return render_template('result.html', character=character)

@app.route('/voice', methods=['POST'])
def voice():
    speak("Think of a Genshin Impact character.")
    characters = load_characters('gichar.csv')
    guess_character(characters)
    return render_template('voice.html')

@app.route('/character_correct', methods=['POST'])
def character_correct():
    return render_template('thank_you.html')

@app.route('/character_incorrect', methods=['POST'])
def character_incorrect():
    return render_template('continue_question.html')

@app.route('/continue_guessing', methods=['POST'])
def continue_guessing():
    return redirect(url_for('question'))

@app.route('/thank_you', methods=['POST'])
def thank_you():
    return render_template('thank_you.html')

if __name__ == "__main__":
    app.run(debug=True)