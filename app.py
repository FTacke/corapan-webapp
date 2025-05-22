from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, Response, after_this_request, redirect, url_for, flash, make_response
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import threading
import time
import os
import tempfile
import subprocess
import eyed3
import math
from pydub import AudioSegment
import io

from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash

# ----------------------------------------------------------------
# Konfiguration und Authentifizierung
# ----------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "passwords.env"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")

# Schlüssel laden (entweder aus dem lokalen keys-Ordner oder aus den Umgebungsvariablen)
LOCAL_PRIVATE_KEY_PATH = os.path.join(BASE_DIR, "keys", "private.pem")
LOCAL_PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "keys", "public.pem")
PRIVATE_KEY_PATH = LOCAL_PRIVATE_KEY_PATH if os.path.exists(LOCAL_PRIVATE_KEY_PATH) else os.getenv("PRIVATE_KEY_PATH")
PUBLIC_KEY_PATH = LOCAL_PUBLIC_KEY_PATH if os.path.exists(LOCAL_PUBLIC_KEY_PATH) else os.getenv("PUBLIC_KEY_PATH")

try:
    with open(PRIVATE_KEY_PATH, "r") as pf:
        PRIVATE_KEY = pf.read()
    with open(PUBLIC_KEY_PATH, "r") as pf:
        PUBLIC_KEY = pf.read()
except Exception as e:
    raise Exception(f"Schlüsseldateien nicht gefunden: {e}")

# Benutzergruppen und Passwörter (alle mit _PASSWORD in .env)
GROUPS = {}
for key, value in os.environ.items():
    if key.endswith("_PASSWORD"):
        group_name = key[:-9].lower()  # Entfernt '_PASSWORD' und macht Kleinbuchstaben
        GROUPS[group_name] = value

for group, password in GROUPS.items():
    if password is None:
        raise ValueError(f"Passwort für Gruppe '{group}' fehlt in der .env-Datei.")

def validate_jwt():
    """Prüft den JWT-Token aus dem Cookie. Bei Fehlern wird zur Login-Seite umgeleitet."""
    token = request.cookies.get("jwt_token")
    if not token:
        flash("Por favor, inicie sesión.", "error")
        return redirect(url_for("index"))
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return payload["group"]
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        flash("La sesión ha expirado o es inválida. Por favor, vuelva a iniciar sesión.", "error")
        return redirect(url_for("index"))

# ----------------------------------------------------------------
# Pfade und Konstanten
# ----------------------------------------------------------------
GRABACIONES_FOLDER = os.path.join(app.root_path, 'grabaciones')
SPLIT_FOLDER = os.path.join(app.root_path, 'split')
CHUNK_DURATION = 4 * 60  # Dauer eines Split-Files in Sekunden

DB_FOLDER = os.path.join(app.root_path, 'db')
STATS_COUNTRY_DB_PATH = os.path.join(DB_FOLDER, 'stats_country.db')
STATS_FILES_DB_PATH = os.path.join(DB_FOLDER, 'stats_files.db')
TRANSCRIPTION_DB_PATH = os.path.join(DB_FOLDER, 'transcription.db')
DB_PUBLIC_FOLDER = os.path.join(app.root_path, 'db_public')
STATS_ALL_DB_PATH = os.path.join(DB_PUBLIC_FOLDER, 'stats_all.db')

# Hier wird der spezifische Temp-Ordner im Root-Verzeichnis festgelegt:
TEMP_MP3_FOLDER = os.path.join(app.root_path, 'temp-mp3')
if not os.path.exists(TEMP_MP3_FOLDER):
    os.makedirs(TEMP_MP3_FOLDER)

os.makedirs(GRABACIONES_FOLDER, exist_ok=True)
os.makedirs(DB_FOLDER, exist_ok=True)

# ----------------------------------------------------------------
# Counter-Funktion
# ----------------------------------------------------------------

import json

def load_counters():
    if not os.path.exists("counters.json"):
        return {"total": {"overall": 0, "monthly": {}, "days": []}, "groups": {}}
    try:
        with open("counters.json", "r") as f:
            data = json.load(f)
        # Prüfen, ob die Struktur passt
        if not isinstance(data, dict):
            raise ValueError("Ungültige counters.json Struktur")
        if "total" not in data or "groups" not in data:
            raise ValueError("Ungültige counters.json Struktur")
        return data
    except (json.JSONDecodeError, ValueError):
        # Ungültige Datei: neu initialisieren und speichern
        data = {"total": {"overall": 0, "monthly": {}, "days": []}, "groups": {}}
        save_counters(data)
        return data

def save_counters(data):
    with open("counters.json", "w") as f:
        json.dump(data, f, indent=2)

def increment_counters(group: str):
    data = load_counters()
    now   = datetime.utcnow()
    month = f"{now.year}-{now.month:02d}"
    day = now.strftime("%Y-%m-%d")

    data["total"]["overall"] += 1
    data["total"]["monthly"][month] = data["total"]["monthly"].get(month, 0) + 1
    # Gesamt-Tage-Liste
    if "days" not in data["total"]:
        data["total"]["days"] = []
    data["total"]["days"].append(day)

    grp = data["groups"].setdefault(group, {"overall": 0, "monthly": {}})
    if "days" not in grp:
        grp["days"] = []
    grp["overall"] += 1
    grp["monthly"][month] = grp["monthly"].get(month, 0) + 1
    grp["days"].append(day)

    save_counters(data)

# ----------------------------------------------------------------
# Helper-Funktionen
# ----------------------------------------------------------------
def get_audio_context(filename):
    conn = sqlite3.connect(TRANSCRIPTION_DB_PATH)
    cursor = conn.cursor()
    query = "SELECT context_start, context_end FROM tokens WHERE filename = ?"
    cursor.execute(query, (filename,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result
    else:
        return None, None

def get_bitrate(file_path):
    cmd = f"ffprobe -v error -select_streams a:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 \"{file_path}\""
    bitrate = subprocess.check_output(cmd, shell=True).decode().strip()
    return bitrate

def get_audio_properties(file_path):
    audiofile = eyed3.load(file_path)
    bitrate = audiofile.info.bit_rate[1]
    channels = audiofile.info.mode
    if channels.lower() == 'mono':
        channels = 1
    elif channels.lower() == 'stereo':
        channels = 2
    else:
        channels = 2
    return bitrate, channels

def parse_time_to_ms(time_str):
    seconds, hundredths = divmod(float(time_str), 1)
    return int(seconds * 1000 + hundredths * 1000)

# Dictionary für die 4-Minuten-Splits
split_times_dict = {
    '_01': {'Start Time': 0.0, 'End Time': 240.0},
    '_02': {'Start Time': 210.0, 'End Time': 450.0},
    '_03': {'Start Time': 420.0, 'End Time': 660.0},
    '_04': {'Start Time': 630.0, 'End Time': 870.0},
    '_05': {'Start Time': 840.0, 'End Time': 1080.0},
    '_06': {'Start Time': 1050.0, 'End Time': 1290.0},
    '_07': {'Start Time': 1260.0, 'End Time': 1500.0},
    '_08': {'Start Time': 1470.0, 'End Time': 1710.0},
    '_09': {'Start Time': 1680.0, 'End Time': 1920.0},
    '_10': {'Start Time': 1890.0, 'End Time': 2130.0},
    '_11': {'Start Time': 2100.0, 'End Time': 2340.0},
    '_12': {'Start Time': 2310.0, 'End Time': 2550.0},
    '_13': {'Start Time': 2520.0, 'End Time': 2760.0},
    '_14': {'Start Time': 2730.0, 'End Time': 2970.0},
    '_15': {'Start Time': 2940.0, 'End Time': 3180.0},
    '_16': {'Start Time': 3150.0, 'End Time': 3390.0},
    '_17': {'Start Time': 3360.0, 'End Time': 3600.0},
    '_18': {'Start Time': 3570.0, 'End Time': 3810.0},
    '_19': {'Start Time': 3780.0, 'End Time': 4020.0},
    '_20': {'Start Time': 3990.0, 'End Time': 4230.0},
    '_21': {'Start Time': 4200.0, 'End Time': 4440.0},
    '_22': {'Start Time': 4410.0, 'End Time': 4650.0},
    '_23': {'Start Time': 4620.0, 'End Time': 4860.0},
    '_24': {'Start Time': 4830.0, 'End Time': 5070.0},
    '_25': {'Start Time': 5040.0, 'End Time': 5280.0},
    '_26': {'Start Time': 5250.0, 'End Time': 5490.0},
    '_27': {'Start Time': 5460.0, 'End Time': 5700.0},
    '_28': {'Start Time': 5670.0, 'End Time': 5910.0},
    '_29': {'Start Time': 5880.0, 'End Time': 6120.0}
}

current_search_query = None

def generate_mp3s_for_search_results(results, query):
    global current_search_query
    current_search_query = query
    for index, result in enumerate(results[:0]):
        if current_search_query != query:
            print("Suchanfrage wurde geändert. Abbruch der MP3-Generierung.")
            break
        filename = result[6]
        context_start_ms = parse_time_to_ms(result[4])
        context_end_ms = parse_time_to_ms(result[5])
        result_number = index + 1
        relevant_part = next(
            (part for part, times in split_times_dict.items()
             if parse_time_to_ms(str(times['Start Time'])) <= context_start_ms and
                parse_time_to_ms(str(times['End Time'])) >= context_end_ms),
            None
        )
        if relevant_part:
            split_filename = f"{os.path.splitext(filename)[0]}{relevant_part}.mp3"
            split_file_path = os.path.join(SPLIT_FOLDER, split_filename)
            local_start_ms = context_start_ms - parse_time_to_ms(str(split_times_dict[relevant_part]['Start Time']))
            local_end_ms = context_end_ms - parse_time_to_ms(str(split_times_dict[relevant_part]['Start Time']))
            cache_key = f"corapan_{query}_{result_number}_{context_start_ms}"
            cached_file_path = os.path.join(TEMP_MP3_FOLDER, f"{cache_key}.mp3")
            if not os.path.exists(cached_file_path):
                try:
                    audio = AudioSegment.from_mp3(split_file_path)
                    part_audio = audio[local_start_ms:local_end_ms]
                    bitrate, channels = get_audio_properties(split_file_path)
                    part_audio.export(cached_file_path, format='mp3', bitrate=str(bitrate) + 'k', parameters=["-ac", str(channels)])
                    print(f"Exportiert: {cached_file_path}")
                except Exception as e:
                    print(f"Fehler bei der MP3-Generierung: {e}")
        else:
            print(f"Keine passende Split-Datei für den Bereich {context_start_ms} bis {context_end_ms} gefunden.")

@app.route('/spectrogram/<path:filename>')
def spectrogram_route(filename):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import librosa
    import librosa.display
    import numpy as np
    import io
    import os
    from pydub import AudioSegment

    # Parameter einlesen
    start = request.args.get('start', type=float)
    end = request.args.get('end', type=float)
    word = request.args.get('word', default='', type=str)

    if start is None or end is None:
        return "Fehlende Parameter", 400

    end += 0.1  # immer 0.1 Sekunde extra

    context_start_ms = int(start * 1000)
    context_end_ms = int(end * 1000)

    # Finde das passende Split-Segment
    relevant_part = None
    for part, times in split_times_dict.items():
        if times['Start Time'] * 1000 <= context_start_ms and times['End Time'] * 1000 >= context_end_ms:
            relevant_part = part
            break

    if relevant_part is None:
        return "Kein passendes Audiosegment gefunden", 404

    split_file_path = os.path.join(SPLIT_FOLDER, f"{os.path.splitext(filename)[0]}{relevant_part}.mp3")
    if not os.path.exists(split_file_path):
        return "Datei nicht gefunden (Split fehlt)", 404

    cache_key = f"corapan_{filename}_{int(start*1000)}_spectrogram"
    cached_spectro_path = os.path.join(TEMP_MP3_FOLDER, f"{cache_key}.png")

    if not os.path.exists(cached_spectro_path):
        # Audiosegment laden und relevanten Ausschnitt extrahieren
        audio = AudioSegment.from_mp3(split_file_path)
        local_start_ms = int(start * 1000) - int(split_times_dict[relevant_part]['Start Time'] * 1000)
        local_end_ms = int(end * 1000) - int(split_times_dict[relevant_part]['Start Time'] * 1000)
        snippet = audio[local_start_ms:local_end_ms]

        # Exportiere den Ausschnitt als WAV in einen Buffer
        wav_buffer = io.BytesIO()
        snippet.export(wav_buffer, format="wav")
        wav_buffer.seek(0)

        # Audio laden, Pre-Emphasis anwenden und STFT berechnen
        y, sr = librosa.load(wav_buffer, sr=None)
        y = librosa.effects.preemphasis(y, coef=0.97)

        n_fft = 1024
        hop_length = 64
        D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length, window='hann'))
        dB = librosa.amplitude_to_db(D, ref=np.max, top_db=70)

        # Dynamische Anpassung: Berechne vmin als 5. Perzentil der dB-Werte
        vmin = np.percentile(dB, 5)
        vmax = 0  # Maximum entspricht 0 dB

        # Dauer des Audio-Snippets
        duration = len(y) / sr

        # Erstelle die Figur im 4:3-Seitenverhältnis: 12 Zoll breit, 9 Zoll hoch.
        # Die Subplots teilen sich die gleiche Zeitachse (sharex=True).
        # Die Höhe wird mit height_ratios [1, 3] verteilt.
        fig, (ax_wave, ax_spec) = plt.subplots(2, 1, sharex=True, figsize=(12, 9), dpi=300,
                                               gridspec_kw={'height_ratios': [1, 3]})

        # Oszillogramm (oberer Plot)
        librosa.display.waveshow(y, sr=sr, ax=ax_wave, linewidth=0.5, color='black')
        ax_wave.set_ylabel("Amplitude")
        ax_wave.set_title("Oscillogram")

        # Spektrogramm (unterer Plot)
        # Verwende extent basierend auf der Audiodauer und einer Frequenzachse von 0 bis sr/2,
        # schränke später auf 0 bis 5000 Hz ein.
        img = ax_spec.imshow(dB, aspect='auto', origin='lower', cmap='gray_r',
                             interpolation='bilinear', extent=[0, duration, 0, sr/2],
                             vmin=vmin, vmax=vmax)
        ax_spec.set_ylim(0, 5000)
        ax_spec.set_ylabel("Frequency (Hz)")
        ax_spec.set_xlabel("Time (s)")
        ax_spec.set_title("Spectrogram")

        # Das gesuchte Wort (mit doppeltem Abstand zwischen den Buchstaben) unterhalb des Spektrogramms anzeigen.
        spaced_word = '  '.join(list(word))
        ax_spec.text(0.5, -0.20, spaced_word, transform=ax_spec.transAxes,
                     fontsize=22, fontname='Consolas', ha='center', va='top', color='#053c96')

        # Logo hinzufügen, falls vorhanden
        logo_path = os.path.join(app.root_path, 'static', 'img', 'logo_small.png')
        if os.path.exists(logo_path):
            logo_img = plt.imread(logo_path)
            fig.figimage(logo_img, xo=280, yo=75, alpha=1.0, zorder=10)

        fig.tight_layout(pad=1.5)
        fig.subplots_adjust(bottom=0.20)
        fig.savefig(cached_spectro_path, format='png')
        plt.close(fig)

    return send_file(cached_spectro_path, mimetype='image/png', as_attachment=False)




# ----------------------------------------------------------------
# Scheduler zum Löschen alter temporärer MP3/PNG-Dateien
# ----------------------------------------------------------------
def delete_old_files():
    now = time.time()
    for filename in os.listdir(TEMP_MP3_FOLDER):
        # Vorher: if filename.endswith('.mp3'):
        if (filename.endswith('.mp3') or filename.endswith('.png')):
            file_path = os.path.join(TEMP_MP3_FOLDER, filename)
            try:
                if os.stat(file_path).st_mtime < now - 720 and os.path.isfile(file_path):
                    os.remove(file_path)
            except PermissionError:
                print(f"Konnte die Datei nicht löschen: {file_path}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_old_files, trigger="interval", minutes=2)
scheduler.start()

# ----------------------------------------------------------------
# Routen
# ----------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        group = request.form.get("group")
        if group:
            group = group.lower()
        password = request.form.get("password")
        if group not in GROUPS:
            flash("Error: Usuario no reconocido.", "error")
            return render_template("index.html", logged_in=False)
        if not check_password_hash(GROUPS[group], password):
            flash("Error: Contraseña incorrecta.", "error")
            return render_template("index.html", logged_in=False)

        # Zähler inkrementieren
        increment_counters(group)

        token = jwt.encode(
            {"group": group, "exp": datetime.utcnow() + timedelta(hours=3)},
            PRIVATE_KEY,
            algorithm="RS256"
        )
        response = make_response(redirect(url_for("index")))
        response.set_cookie("jwt_token", token, httponly=True, secure=True)
        return response

    token = request.cookies.get("jwt_token")
    logged_in = False
    if token:
        try:
            jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
            logged_in = True
        except jwt.ExpiredSignatureError:
            flash("Sesión expirada. Por favor, inicie sesión nuevamente.", "error")
        except jwt.InvalidTokenError:
            flash("Ungültiges Token. Bitte melden Sie sich erneut an.", "error")
    return render_template("index.html", logged_in=logged_in)

@app.route("/logout")
def logout():
    response = make_response(redirect(url_for("index")))
    response.delete_cookie("jwt_token")
    return response

@app.route("/impressum")
def impressum():
    return render_template("impressum.html")

@app.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")

@app.route('/proyecto')
def proyecto():
    return render_template('proyecto.html')

@app.route('/atlas')
def atlas():
    return render_template('atlas.html')

@app.route('/player')
def player():
    user = validate_jwt()
    if not isinstance(user, str):
        return user
    transcription_file = request.args.get('transcription')
    audio_file = request.args.get('audio')
    return render_template('player.html', transcription=transcription_file, audio=audio_file)

@app.route('/grabaciones/<path:filename>')
def get_file(filename):
    file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else None
    if file_extension in ['json', 'mp3']:
        return send_from_directory(GRABACIONES_FOLDER, filename)
    else:
        return "Ungültiger Dateityp", 400

@app.route('/grabaciones_files')
def grabaciones_files():
    files = os.listdir(GRABACIONES_FOLDER)
    json_files = [file for file in files if file.endswith('.json')]
    mp3_files = [file for file in files if file.endswith('.mp3')]
    return {'json_files': json_files, 'mp3_files': mp3_files}

@app.route('/play_audio/<path:filename>')
def play_audio(filename):
    file_path = os.path.join(SPLIT_FOLDER, filename)
    print("File path (raw):", file_path)  # Bestehende Ausgabe

    context_start = request.args.get('start', type=float)
    context_end = request.args.get('end', type=float)
    query = request.args.get('query')
    result_number = request.args.get('result_number', type=int)

    if context_start is None or context_end is None or query is None or result_number is None:
        return "Erforderliche Parameter fehlen", 400

    context_start_ms = int(context_start * 1000)
    context_end_ms = int(context_end * 1000)

    relevant_part = next(
        (part for part, times in split_times_dict.items()
         if times['Start Time'] * 1000 <= context_start_ms and times['End Time'] * 1000 >= context_end_ms),
        None
    )
    if relevant_part is None:
        return "Kein passendes Audiosegment gefunden", 404

    # Berechne den erwarteten Split-Dateipfad
    split_file_path = os.path.join(SPLIT_FOLDER, f"{os.path.splitext(filename)[0]}{relevant_part}.mp3")
    
    # Debug-Ausgabe: Logge den finalen Split-Dateipfad
    print("Debug: Berechneter Split-Dateipfad:", split_file_path)
    
    # Überprüfe, ob die Datei existiert
    if not os.path.exists(split_file_path):
        print("Error: Split-Datei existiert nicht:", split_file_path)
        return "Datei nicht gefunden (Split-Datei fehlt)", 404
    # Überprüfe, ob Lesezugriff besteht
    elif not os.access(split_file_path, os.R_OK):
        print("Error: Kein Lesezugriff auf die Split-Datei:", split_file_path)
        return "Datei nicht zugreifbar (keine Leserechte)", 403

    cache_key = f"corapan_{query}_{result_number}_{context_start_ms}"
    cached_file_path = os.path.join(TEMP_MP3_FOLDER, f"{cache_key}.mp3")

    if not os.path.exists(cached_file_path):
        try:
            bitrate, channels = get_audio_properties(split_file_path)
            audio = AudioSegment.from_mp3(split_file_path)
            local_start_ms = context_start_ms - int(split_times_dict[relevant_part]['Start Time'] * 1000)
            local_end_ms = context_end_ms - int(split_times_dict[relevant_part]['Start Time'] * 1000)
            part_audio = audio[local_start_ms:local_end_ms]
            part_audio.export(cached_file_path, format='mp3', bitrate=str(bitrate) + 'k', parameters=["-ac", str(channels)])
            print("Debug: Temporäre MP3 exportiert nach:", cached_file_path)
        except FileNotFoundError:
            return "Datei nicht gefunden", 404
        except Exception as e:
            print("Fehler bei der MP3-Generierung:", e)
            return str(e), 500

    return send_file(cached_file_path, mimetype='audio/mp3', as_attachment=True)

@app.route('/get_stats_all_from_db', methods=['GET'])
def get_stats_all_from_db():
    try:
        connection = sqlite3.connect(STATS_ALL_DB_PATH)
        cursor = connection.cursor()
        query = 'SELECT total_word_count, total_duration_all FROM stats;'
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            total_word_count, total_duration_all = row
            return jsonify({'total_word_count': total_word_count, 'total_duration_all': total_duration_all})
        else:
            return jsonify({'error': 'No data found'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        connection.close()

@app.route('/get_stats_files_from_db', methods=['GET'])
def get_stats_files_from_db():
    user = validate_jwt()
    if not isinstance(user, str):
        return user
    try:
        connection = sqlite3.connect(STATS_FILES_DB_PATH)
        cursor = connection.cursor()
        query = 'SELECT filename, date, radio, revision, word_count, duration FROM metadata;'
        cursor.execute(query)
        rows = cursor.fetchall()
        if rows:
            metadata_list = []
            for row in rows:
                filename, date, radio, revision, word_count, duration = row
                metadata_list.append({
                    'filename': filename,
                    'date': date,
                    'radio': radio,
                    'revision': revision,
                    'word_count': word_count,
                    'duration': duration
                })
            return jsonify({'metadata_list': metadata_list})
        else:
            return jsonify({'error': 'No data found'})
    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        connection.close()

@app.route('/corpus')
def corpus():
    user = validate_jwt()
    if not isinstance(user, str):
        # Wenn kein gültiger Token vorhanden ist, wird eine Fehlermeldung an das Template übergeben.
        error_message = (
            '<div class="login-container-atlas">'
            '  <div class="login-form-atlas error">'
            '    <p>'
            '      <span class="error" style="display:inline-flex;align-items:center;gap:0.5rem;">'
            '        <i class="bi bi-lock-fill"></i>'
            '        Inicie <a href="/" class="link-error">sesión</a> para acceder a los datos.'
            '      </span>'
            '    </p>'
            '  </div>'
            '</div>'
        )
        return render_template('corpus.html', 
                               query='',
                               selected_countries=['all'],
                               selected_speaker_types=['all'],
                               selected_sexes=['all'],
                               selected_speech_modes=['all'],
                               selected_discourses=['all'],
                               error_message=error_message,
                               results=[])
    
    sort = request.args.get('sort')
    order = request.args.get('order')
    results = []
    if sort and order:
        conn = sqlite3.connect(TRANSCRIPTION_DB_PATH)
        cursor = conn.cursor()
        sql_query = f"SELECT * FROM tokens ORDER BY {sort} {order}"
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()
    
    # Falls ein gültiger Token vorliegt, wird die Seite normal angezeigt (ohne Fehlermeldung)
    return render_template('corpus.html', 
                           query='',
                           selected_countries=['all'],
                           selected_speaker_types=['all'],
                           selected_sexes=['all'],
                           selected_speech_modes=['all'],
                           selected_discourses=['all'],
                           results=results,
                           error_message="")

@app.route('/search', methods=['GET'])
def search():
    user = validate_jwt()
    if not isinstance(user, str):
        return user

    # ---------------------------------------------------------------
    # Grundparameter
    # ---------------------------------------------------------------
    query_text   = request.args.get('query', '').strip()
    search_mode  = request.args.get('search_mode', 'text')

    token_ids_raw = request.args.get('token_ids', '')
    token_ids     = [tid.strip() for tid in token_ids_raw.split(',') if tid.strip()]

    selected_countries      = request.args.getlist('country_code') or ['all']
    selected_speaker_types  = request.args.getlist('speaker_type')  or ['all']
    selected_sexes          = request.args.getlist('sex')           or ['all']
    selected_speech_modes   = request.args.getlist('speech_mode')   or ['all']
    selected_discourses     = request.args.getlist('discourse')     or ['all']

    sort   = request.args.get('sort', '')
    order  = request.args.get('order', 'asc').lower()

    page       = int(request.args.get('page', 1))
    page_size  = int(request.args.get('page_size', 20))
    offset     = (page - 1) * page_size

    conn   = sqlite3.connect(TRANSCRIPTION_DB_PATH)
    cursor = conn.cursor()

    selected_tab = request.args.get('tab', 'simple')   # << neu

    # ---------------------------------------------------------------
    # Wort‑/Lemma‑Suche (Einzel‑ oder Mehrwort)
    # ---------------------------------------------------------------
    def build_conditions_for_words(words, col, exact):
        if len(words) == 1:
            w = words[0]
            if exact:
                return f"SELECT * FROM tokens t WHERE t.{col} = ?", [w]
            else:
                return f"SELECT * FROM tokens t WHERE t.{col} LIKE ?", [f"%{w}%"]

        join_parts, conditions, params, aliases = [], [], [], []
        for i, w in enumerate(words):
            a = f"t{i+1}"
            aliases.append(a)
            conditions.append(f"{a}.{col} {'=' if exact else 'LIKE'} ?")
            params.append(w if exact else f"%{w}%")

        from_clause = f"FROM tokens {aliases[0]}"
        for i in range(len(words) - 1):
            l, r = aliases[i], aliases[i+1]
            join_parts.append(
                f"JOIN tokens {r} ON {r}.filename = {l}.filename AND {r}.id = {l}.id + 1"
            )

        sql = f"SELECT {aliases[0]}.* {from_clause} {' '.join(join_parts)} WHERE {' AND '.join(conditions)}"
        return sql, params

    words = query_text.split()
    col, exact = ('text', False)
    if search_mode == 'text_exact':   col, exact = ('text', True)
    elif search_mode == 'lemma':      col, exact = ('lemma', False)
    elif search_mode == 'lemma_exact':col, exact = ('lemma', True)

    sql_words, word_params = (None, [])
    if query_text:
        sql_words, word_params = build_conditions_for_words(words, col, exact)

    # ---------------------------------------------------------------
    # Filter
    # ---------------------------------------------------------------
    filters, filter_params = [], []

    if token_ids:
        placeholders = ','.join('?' * len(token_ids))
        filters.append(f"token_id IN ({placeholders})")
        filter_params.extend(token_ids)

    if selected_countries and 'all' not in selected_countries:
        placeholders = ','.join('?' * len(selected_countries))
        filters.append(f"country_code IN ({placeholders})")
        filter_params.extend(selected_countries)

    if selected_speaker_types and 'all' not in selected_speaker_types:
        placeholders = ','.join('?' * len(selected_speaker_types))
        filters.append(f"speaker_type IN ({placeholders})")
        filter_params.extend(selected_speaker_types)

    if selected_sexes and 'all' not in selected_sexes:
        placeholders = ','.join('?' * len(selected_sexes))
        filters.append(f"sex IN ({placeholders})")
        filter_params.extend(selected_sexes)

    if selected_speech_modes and 'all' not in selected_speech_modes:
        placeholders = ','.join('?' * len(selected_speech_modes))
        filters.append(f"mode IN ({placeholders})")
        filter_params.extend(selected_speech_modes)

    if selected_discourses and 'all' not in selected_discourses:
        placeholders = ','.join('?' * len(selected_discourses))
        filters.append(f"discourse IN ({placeholders})")
        filter_params.extend(selected_discourses)

    filter_clause = " AND " + " AND ".join(filters) if filters else ""

    # ---------------------------------------------------------------
    # Sortierung
    # ---------------------------------------------------------------
    sort_map = {
        'palabra': col,
        'modo':    'mode',
        'discurso':'discourse',
        'hablante':'speaker_type',
        'sexo':    'sex',
        'pais':    'country_code',
        'archivo': 'filename'
    }
    sort_column = sort_map.get(sort, col)
    order_sql   = 'DESC' if order == 'desc' else 'ASC'

    # ---------------------------------------------------------------
    # Ergebnis‑SQL
    # ---------------------------------------------------------------
    if sql_words:
        count_sql = f"SELECT COUNT(*) FROM ({sql_words}) AS base WHERE 1=1{filter_clause}"
        cursor.execute(count_sql, word_params + filter_params)
        total_results = cursor.fetchone()[0]

        data_sql = f"""
            SELECT * FROM ({sql_words}) AS base
            WHERE 1=1{filter_clause}
            ORDER BY {sort_column} {order_sql}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, word_params + filter_params + [page_size, offset])
        results = cursor.fetchall()

        all_sql = f"""
            SELECT * FROM ({sql_words}) AS base
            WHERE 1=1{filter_clause}
            ORDER BY {sort_column} {order_sql}
        """
        cursor.execute(all_sql, word_params + filter_params)
        all_results = cursor.fetchall()
    else:
        base_sql = "SELECT * FROM tokens WHERE 1=1" + filter_clause
        count_sql = f"SELECT COUNT(*) FROM ({base_sql})"
        cursor.execute(count_sql, filter_params)
        total_results = cursor.fetchone()[0]

        data_sql = f"""
            {base_sql}
            ORDER BY {sort_column} {order_sql}
            LIMIT ? OFFSET ?
        """
        cursor.execute(data_sql, filter_params + [page_size, offset])
        results = cursor.fetchall()

        cursor.execute(f"{base_sql} ORDER BY {sort_column} {order_sql}", filter_params)
        all_results = cursor.fetchall()

    unique_countries = len(set(r[3] for r in all_results))
    unique_files     = len(set(r[2] for r in all_results))
    total_pages      = math.ceil(total_results / page_size) if page_size else 1

    # -------- Pagination‑Hilfsfunktion ---------------------------------
    def build_display_pages(curr, total):
        """
        Liefert eine Liste wie [1, '…', 4, 5, 6, '…', 23]
        –  maximal 9 Elemente, mit Ellipsen.
        """
        if total <= 9:
            return list(range(1, total + 1))

        pages = []
        if curr > 4:                    # linker Rand
            pages += [1, '…']

        start = max(1, curr - 2)
        end   = min(total, curr + 2)
        pages += list(range(start, end + 1))

        if end < total - 1:             # rechter Rand
            pages += ['…', total]
        elif end == total - 1:
            pages.append(total)

        return pages

    display_pages = build_display_pages(page, total_pages)

    if results:
        threading.Thread(
            target=generate_mp3s_for_search_results,
            args=(results, query_text)
        ).start()

    conn.close()

    return render_template(
    'corpus.html',
    query=query_text,
    token_ids=token_ids_raw,
    search_mode=search_mode,
    results=results,
    all_results=all_results,
    total_results=total_results,
    unique_countries=unique_countries,
    unique_filenames=unique_files,
    selected_countries=selected_countries,
    selected_speaker_types=selected_speaker_types,
    selected_sexes=selected_sexes,
    selected_speech_modes=selected_speech_modes,
    selected_discourses=selected_discourses,
    current_sort=sort,
    current_order=order,
    page=page,
    page_size=page_size,
    total_pages=total_pages,
    display_pages=display_pages,
    selected_tab=selected_tab,
    error_message=""
)

# --- AJAX‑Service: liefere Zeilen zu beliebigen Token‑IDs -----------------
@app.route('/search_tokens_json')
def search_tokens_json():
    # Auth‑Check
    user = validate_jwt()
    if not isinstance(user, str):
        return "unauthorized", 403

    token_ids = [t.strip() for t in
                 request.args.get('token_ids', '').split(',') if t.strip()]
    if not token_ids:
        return jsonify([])

    conn   = sqlite3.connect(TRANSCRIPTION_DB_PATH)
    conn.row_factory = sqlite3.Row      # → Dict-artig zugreifen
    cur    = conn.cursor()
    ph     = ','.join('?'*len(token_ids))
    cur.execute(f"SELECT * FROM tokens WHERE token_id IN ({ph})", token_ids)
    rows   = cur.fetchall()
    conn.close()

    # Nur Felder, die du in der Tabelle brauchst (Index‑Entsprechungen!)
    data = []
    for r in rows:
        data.append({
            'token_id'  : r['token_id'],
            'filename'  : r['filename'],
            'country'   : r['country_code'],
            'sex'       : r['sex'],
            'speaker'   : r['speaker_type'],
            'mode'      : r['mode'],
            'word'      : r['text'],
            'ctx_l'     : r['context_left'],
            'ctx_r'     : r['context_right'],
            'start'     : r['context_start'],
            'end'       : r['context_end']
        })
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
