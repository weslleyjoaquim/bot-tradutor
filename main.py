import telebot
from PIL import Image
import pytesseract
import cv2
import os
import speech_recognition as sr
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
os.environ['TESSDATA_PREFIX'] = os.getenv("TESSDATA_PREFIX")

recognizer = sr.Recognizer()
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
def translation_response(text):
    response = model.generate_content(
        "Olá, eu quero realizar a tradução do texto a seguir, no qual pode ser um texto todo em inglês, ou apenas palavras, se não for em inglês responda que está esperando "
        "um texto em inglês, além disso quero que sempre responda começando com o texto 'Está aqui a sua tradução, conforme foi solicitado: ', segue o texto a ser traduzido para o português do Brasil"
        ": "
        + text)

    return response.text


@bot.message_handler(func=lambda message:True)
def handle_text(message):
    bot.send_message(message.chat.id, "Aguarde um instante enquanto o texto é traduzida ...")
    text = message.text

    response = translation_response(text)
    bot.reply_to(message, response)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.send_message(message.chat.id, "Aguarde um instante enquanto a imagem é traduzida ...")

    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path

    downloaded_file = bot.download_file(file_path)

    with open("photo.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)

    img = cv2.imread("photo.jpg")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    cv2.imwrite("temp_gray.jpg", gray)

    text = pytesseract.image_to_string(Image.open("temp_gray.jpg"))

    os.remove("photo.jpg")
    os.remove("temp_gray.jpg")

    response = translation_response(text)
    bot.reply_to(message, response)

@bot.message_handler(content_types=['voice'])
def handle_audio(message):
    bot.send_message(message.chat.id, "Aguarde um instante enquanto o áudio é traduzida ...")
    file_id = message.voice.file_id
    file = bot.get_file(file_id)
    file_path = file.file_path

    downloaded_file = bot.download_file(file_path)

    with open("audio.ogg", 'wb') as new_file:
        new_file.write(downloaded_file)

    subprocess.call(['ffmpeg', '-i', "audio.ogg", 'audio.wav'])

    with sr.AudioFile('audio.wav') as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language='en-US')

        response = translation_response(text)

        bot.reply_to(message, response)
    except sr.UnknownValueError:
        bot.reply_to(message, "Não foi possível reconhecer o áudio.")
    except sr.RequestError as e:
        bot.reply_to(message, "Ocorreu um erro durante a requisição ao serviço de reconhecimento de fala")

    os.remove("audio.ogg")
    os.remove("audio.wav")


bot.infinity_polling()