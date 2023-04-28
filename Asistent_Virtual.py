import tkinter as tk
from tkinter import ttk
from threading import Thread
import openai
import speech_recognition as sr
from gtts import gTTS
import os
from playsound import playsound
from bs4 import BeautifulSoup
import requests
from urllib import request
import urllib.parse
import wikipediaapi
from googletrans import Translator
import random
import vlc
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube
from google_images_search import GoogleImagesSearch
from PIL import Image
import re
from tkinter import PhotoImage
from datetime import datetime


class Assistant:
    def __init__(self, google_api_key, google_cx, openai_api_key):
        self.gis = GoogleImagesSearch(google_api_key, google_cx)
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        openai.api_key = openai_api_key
        self.model_id = 'gpt-3.5-turbo'
        self.uncertainty_phrases = [
            "nu sunt sigur",
            "nu pot să",
            "nu cunosc",
            "Nu am putut găsi informații despre o persoană numită",
            "Nu sunt în măsură să furnizez informații",
            "Îmi pare rău, dar nu am putut găsi informații relevante",
            "nu am informații relevante",
            "nu am informații suficiente",
            "nu am informatii",
            "nu am informații",
            "Nu am putut găsi informații despre o persoană numită",
            "te rog să oferi mai multe informații sau detalii",
            "Îmi pare rău, dar nu am informații",
            "Nu pot oferi informații ",
            "Nu există informații",
            "nu am găsit",
            "nu reușesc să găsesc nicio informație verificabilă",
            "nu am acces la",
            "nu pot confirma",
            "Nu am putut găsi informații despre",
            "nu pot verifica",
            "I'm sorry, but I don't have any specific information about",
            "Nu am suficiente informații pentru a răspunde la această întrebare",
            "Nu am suficiente informații",
            "Nu exista un termen definit",
            "Nu există informații clare despre ce ar putea fi",
            "Nu există",
            "Nu am cunoștințe despre",
            "Nu am nicio idee despre",
            "Nu există o definiție a termenului",
            "Nu pot furniza informații",
            "Îmi pare rău"
        ]


    def google_search_api(self, query):
        api_key = self.google_api_key
        cx = self.google_cx
        url = f"https://www.googleapis.com/customsearch/v1?key={self.google_api_key}&cx={self.google_cx}&q={query}"
        response = requests.get(url)
        if response.status_code == 200:
            results = response.json()
            return results
        else:
            print(f"Error: {response.status_code}")
            return None

    def roman_to_int(self, s):
        roman_to_int = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        total = 0
        prev_value = 0
        for c in s:
            value = roman_to_int.get(c)
            if not value:
                return s  # Dacă nu este un număr roman valid, returnăm stringul original
            if value > prev_value:
                total += value - 2 * prev_value
            else:
                total += value
            prev_value = value
        return str(total)

    def speak(self, text):
        if text.strip():
            # Înlocuiește cifrele romane cu numerale arabe
            text = re.sub(r'\b([MDCLXVI]+)\b', lambda x: self.roman_to_int(x.group(1)), text)

            # Înlocuim semnul minus cu cuvântul "până la" atunci când este între două grupuri de numere sau secole
            modified_text = re.sub(r'(\d+|[IVXLC]+)(\s*-\s*)(\d+|[IVXLC]+)', r' din \1 până în \3', text)

            tts = gTTS(text=modified_text, lang='ro', slow=False)
            tts.save("response.mp3")
            playsound("response.mp3")
            os.remove("response.mp3")
        else:
            print("Error: No text to speak")

    def get_summary(self, text):
        messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
        messages.append({'role': 'user', 'content': f"Vreau un rezumat în română, corect gramatical, de maxim 300 de cuvinte al următorului text: {text}"})

        response = openai.ChatCompletion.create(
            model=self.model_id,
            messages=messages
        )
        summary = response.choices[0].message.content.strip()

        return summary

    def translate_text(self, text, target_language='ro'):
        translator = Translator()
        translated = translator.translate(text, dest=target_language)
        return translated.text

    def listen(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Aștept întrebarea...")
            self.speak("Aștept întrebarea...")
            audio = r.listen(source, timeout=7)

        try:
            print("Recunosc...")
            question = r.recognize_google(audio, language="ro-RO")
            print(f"Întrebare: {question}")

            # Lista cu diverse răspunsuri
            random_responses = [
                "Întrebarea ta a fost: {question}. Am să mă gândesc câteva secunde și îți răspund.",
                "Ai întrebat: {question}. Lasă-mă să mă gândesc un pic și îți voi oferi un răspuns.",
                "Întrebarea ta este: {question}. Am să caut răspunsul și revin imediat.",
                "Așadar, întrebarea ta este: {question}. Lasă-mă să mă gândesc și îți voi răspunde."
            ]

            # Alege un răspuns aleatoriu din listă
            response = random.choice(random_responses)
            response = response.format(question=question)

            self.speak(response)
            return question
        except sr.WaitTimeoutError:
            print("Așteptarea a expirat. Vă rog să repetați întrebarea.")
            self.speak("Așteptarea a expirat. Vă rog să repetați întrebarea.")
            return None
        except Exception as e:
            print("Scuze, nu am înțeles.")
            self.speak("Aștept întrebarea...")
            return None

    def show_image(self, query):
        search_params = {
            'q': query,
            'num': 1,
            'imgSize': 'large',
            'fileType': 'jpg|png',
            'safe': 'off'
        }

        self.gis.search(search_params)
        results = self.gis.results()

        if results:
            image_url = results[0].url
            image_path = 'temp_image.jpg'
            urllib.request.urlretrieve(image_url, image_path)

            img = Image.open(image_path)
            img.show()
        else:
            print(f"Nu am putut găsi o imagine pentru {query}.")
            return None

    def is_unresolved(self, answer):
        lower_answer = answer.lower()
        for phrase in self.uncertainty_phrases:
            if phrase in lower_answer:
                return True
        return False

    def extract_information_from_webpage(self, url):
        try:
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            content_text = soup.find("body")
            if not content_text:
                return None

            paragraphs = content_text.find_all("p")

            summary = ""
            for p in paragraphs:
                summary += p.text

            return summary
        except Exception as e:
            print(f"Error while extracting information from {url}: {e}")
            return None

    def youtube_search(self, query, max_results=1, order="relevance", token=None, location=None, location_radius=None):
        youtube = build("youtube", "v3", developerKey=self.google_api_key)

        search_response = youtube.search().list(
            q=query,
            type="video",
            pageToken=token,
            order=order,
            part="id,snippet",
            maxResults=max_results,
            location=location,
            locationRadius=location_radius
        ).execute()

        return search_response

    def play_song(self, song_name):
        try:
            search_response = self.youtube_search(song_name)
            video_id = search_response["items"][0]["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return
        except Exception as e:
            print(f"Excepție în timpul căutării YouTube: {e}")
            return

        if not video_url:
            print("Nu am găsit melodia.")
            return

        try:
            yt = YouTube(video_url)
            stream = yt.streams.filter(only_audio=True).first()
            play_url = stream.url
        except Exception as e:
            print(f"Excepție în timpul extragerii URL-ului de redare: {e}")
            return

        player = vlc.MediaPlayer(play_url)
        player.play()

        return player

    def google_search(self, query):
        api_key = self.google_api_key
        cx = self.google_cx

        results = self.google_search_api(query)
        if results:
            valid_results = []
            for item in results.get("items", []):
                if "wikipedia" in item["link"]:
                    return item["link"]
                elif not any(exclude_domain in item["link"] for exclude_domain in ["facebook.com", "twitter.com"]):
                    valid_results.append(item["link"])
            return valid_results
        return None

    def get_wikipedia_summary(self, url, lang="ro"):
        if not url:
            return "Nu am putut găsi informații relevante in wikipedia."

        parsed_url = urllib.parse.urlparse(url)
        title = urllib.parse.unquote(parsed_url.path.split("/")[-1])

        wiki = wikipediaapi.Wikipedia(lang)
        page = wiki.page(title)

        if page.exists():
            return page.summary
        else:
            return "Pagina nu există."

    def search_other_sources(self, query):
        global answer
        google_search_query = query
        search_result_urls = self.google_search(google_search_query)
        if search_result_urls:
            for url in search_result_urls:
                answer = self.extract_information_from_webpage(url)
                if answer:
                    break
        else:
            answer = "Nu am putut găsi informații relevante."

        return answer

    def get_answer(self, prompt):
        search_wikipedia_first = False
        if "ora actuală" in prompt.lower():
            ora_actuala = datetime.now()
            answer = ora_actuala.strftime("%H:%M:%S")
            self.speak(f"{answer}")
            #print(f"Răspuns: {answer}")
            #self.get_answer = self.listen()
        elif "arată fotografia lui" in prompt.lower():
            query = prompt.lower().replace("arată fotografia lui", "").strip()
            if query:
                answer = "Ti-am aratat fotografia"
                #self.speak("Aceasta este fotografia")
                self.show_image(query)
            else:
                self.speak("Te rog să specifici numele persoanei a cărei fotografie dorești să o vezi.")

        elif "redă melodia" in prompt.lower() or "melodia" in prompt.lower():
            song_name = prompt.lower().replace("redă melodia", "").strip()
            player = self.play_song(song_name)
            if player:
                self.speak(f"Încerc să redau melodia {song_name} pe YouTube.")
                while player.get_state() != vlc.State.Ended:
                    time.sleep(1)
                    answer = "Am reprodus melodia ceruta"
            else:
                return f"Îmi pare rău, nu am putut găsi melodia {song_name} pe YouTube."
        elif "informații actualizate" in prompt.lower():
            search_wikipedia_first = True
            prompt = prompt.lower().replace("informații actualizate", "").strip()

            if search_wikipedia_first:
                self.speak("Caut în Wikipedia")
                print("Caut în Wikipedia")
                google_search_query = f"{prompt} site:wikipedia.org"
                wikipedia_answer = self.google_search(google_search_query)
                if wikipedia_answer:
                    self.speak("Fac un rezumat al informațiilor găsite")
                    wiki_summary = self.get_wikipedia_summary(wikipedia_answer)
                    if wiki_summary != "Pagina nu există.":
                        answer = wiki_summary
                    else:
                        print("Caut în Google")
                        answer = self.search_other_sources(prompt)
                else:
                    print("Caut în Google")
                    self.speak("Caut în Google")
                    answer = self.search_other_sources(prompt)
                    if google_search_query:
                        self.speak("Fac un rezumat al informațiilor găsite")
                        answer = self.get_summary(answer)
        else:
            messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
            messages.append({'role': 'user', 'content': prompt})

            response = openai.ChatCompletion.create(
                model=self.model_id,
                messages=messages
            )
            answer = response.choices[0].message.content.strip()

            if self.is_unresolved(answer):
                print("Caut în Wikipedia")
                self.speak("Caut în Wikipedia")
                google_search_query = f"{prompt} site:wikipedia.org"
                wikipedia_answer = self.google_search(google_search_query)
                if wikipedia_answer:
                    self.speak("Fac un rezumat al informațiilor găsite")
                    wiki_summary = self.get_wikipedia_summary(wikipedia_answer)
                    if wiki_summary != "Pagina nu există.":
                        answer = wiki_summary
                    else:
                        print("Caut în Google")
                        self.speak("Caut în Google")
                        answer = self.search_other_sources(prompt)
                else:
                    print("Caut în Google")
                    self.speak("Caut în Google")
                    answer = self.search_other_sources(prompt)
                if google_search_query or wikipedia_answer:
                    self.speak("Fac un rezumat al informațiilor găsite")
                    answer = self.get_summary(answer)

            # Verificați dacă răspunsul conține cuvinte englezești
        english_words = ["the", "and", "is", "in", "of", "I", "I'm"]
        if any(word in answer for word in english_words):
            answer = self.translate_text(answer)

        return answer


class SettingsWindow(tk.Toplevel):
    def __init__(self, master=None, callback=None):
        super().__init__(master)
        self.title("Settings")
        self.geometry("300x200")
        self.callback = callback

        self.create_widgets()

    def create_widgets(self):
        # API key
        self.api_key_label = ttk.Label(self, text="Google API Key:")
        self.api_key_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.api_key_entry = ttk.Entry(self, width=30)
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=10)

        # CX ID
        self.cx_label = ttk.Label(self, text="Google CX ID:")
        self.cx_label.grid(row=1, column=0, sticky="w", padx=10, pady=10)
        self.cx_entry = ttk.Entry(self, width=30)
        self.cx_entry.grid(row=1, column=1, padx=10, pady=10)

        # OpenAI API key
        self.openai_api_key_label = ttk.Label(self, text="OpenAI API Key:")
        self.openai_api_key_label.grid(row=2, column=0, sticky="w", padx=10, pady=10)
        self.openai_api_key_entry = ttk.Entry(self, width=30)
        self.openai_api_key_entry.grid(row=2, column=1, padx=10, pady=10)

        # Save button
        self.save_button = ttk.Button(self, text="Save", command=self.save)
        self.save_button.grid(row=3, column=1, sticky="e", padx=10, pady=10)

    def save(self):
        api_key = self.api_key_entry.get()
        cx = self.cx_entry.get()
        openai_api_key = self.openai_api_key_entry.get()

        if self.callback:
            self.callback(api_key, cx, openai_api_key)

        self.destroy()


class AssistantGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.assistant = None
        self.title("Assistant")
        self.geometry("800x600")
        self.configure(bg="white")

        self.create_widgets()
        self.create_bindings()
        self.print = self.print_to_textbox

        self.open_settings()

    def update_api_keys(self, google_api_key, google_cx, openai_api_key):
        self.assistant = Assistant(google_api_key, google_cx, openai_api_key)
    def open_settings(self):
        settings_window = SettingsWindow(self, self.update_api_keys)
    def create_widgets(self):
        # Crearea unui obiect Canvas
        self.canvas = tk.Canvas(self, width=600, height=800)
        self.canvas.pack(fill="both", expand=True)

        # Încărcarea imaginii
        self.background_image = PhotoImage(file="Robot.png")  # Înlocuiți cu numele fișierului dvs. de imagine

        # Adăugarea imaginii pe Canvas
        image_x = (self.canvas.winfo_width() + 2) // 2  # Ajustați dimensiunile imaginii (lățimea aici) în funcție de nevoi
        image_y = 60  # Ajustați coordonatele în funcție de nevoi
        self.canvas.create_image(image_x, image_y, image=self.background_image, anchor="nw")
        self.ask_button = ttk.Button(self, text="Întreabă", command=self.ask_question)
        self.ask_button.place(x=120, y=500)
        self.message_box = tk.Text(self, wrap="word", height=35, width=55, bg="white", state="disabled")
        self.message_box.place(x=300, y=10)  # Ajustați coordonatele în funcție de nevoi
    def create_bindings(self):
        self.bind("<Return>", lambda event: self.ask_question())
        self.bind("<Control-c>", self.copy_text)
    def ask_question(self):
        self.ask_button.config(state="disabled")
        question_thread = Thread(target=self.handle_question)
        question_thread.start()

    def handle_question(self):
        question = self.assistant.listen()
        if not question:
            self.print_to_textbox("Nu s-a recunoscut o întrebare")
            self.assistant.speak("Nu am înțeles întrebarea. Vă rog să încercați din nou.")
            self.ask_button.config(state="normal")
        else:
            answer = self.assistant.get_answer(question)
            self.print_to_textbox(f"Răspuns: {answer}")
            if answer.strip():
                self.assistant.speak(answer)
            else:
                self.assistant.speak("Îmi pare rău, dar nu am putut găsi nicio informație.")
                self.ask_button.config(state="normal")
        self.ask_button.config(state="normal")

    def copy_text(self, event=None):
        try:
            selected_text = self.message_box.get("sel.first", "sel.last")
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except tk.TclError:
            # Dacă nu există text selectat, nu se întâmplă nimic
            pass

    def print_to_textbox(self, *args, **kwargs):
        message = " ".join(map(str, args)) + "\n"
        self.message_box.config(state="normal")
        self.message_box.insert("end", message)
        self.message_box.config(state="disabled")
        self.message_box.see("end")


if __name__ == "__main__":
    gui = AssistantGUI()
    gui.mainloop()