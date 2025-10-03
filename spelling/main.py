import streamlit as st
import random
import time
from datetime import datetime, timezone, timedelta
from google.cloud import bigquery

# Word bank: prompt → correct + distractors
word_bank = {
    "chuchichäschtli": {"correct": "Küchenschränkchen", "distractors": ["Uhrenkästchen"]},
    "gschwind": {"correct": "schnell", "distractors": ["windig"]},
    "gfrörli": {"correct": "Person, die immer friert", "distractors": ["Eis"]},
    "gschnägg": {"correct": "Schnecke", "distractors": ["schick"]},
    "grüezi": {"correct": "Hallo", "distractors": ["Auf Wiedersehen"]},
    "zämehöckle": {"correct": "sich zusammensetzen", "distractors": ["zusammenbrechen"]},
    "lisme": {"correct": "stricken", "distractors": ["lesen"]},
    "plöfferä": {"correct": "angeben", "distractors": ["platzen"]},
    "tätsch": {"correct": "Schlag", "distractors": ["Tanz"]},
    "verhebe": {"correct": "funktionieren", "distractors": ["verheiraten"]},
    "schpänne": {"correct": "zusammenarbeiten", "distractors": ["sich verspannen"]},
    "schmöcke": {"correct": "riechen", "distractors": ["schmücken"]},
    "gäbig": {"correct": "praktisch", "distractors": ["großzügig"]},
    "rüüdig": {"correct": "sehr", "distractors": ["wütend"]},
    "gmüetlich": {"correct": "gemütlich", "distractors": ["müde"]},
    "schlönz": {"correct": "Rotz", "distractors": ["Schlitz"]},
    "tüpflischiisser": {"correct": "Pedant", "distractors": ["Kritiker"]},
    "güsel": {"correct": "Abfall", "distractors": ["Gemüse"]},
    "büez": {"correct": "Arbeit", "distractors": ["Besen"]},
    "chnorzi": {"correct": "Mürrischer Mensch", "distractors": ["Knopf"]},
    "giggerig": {"correct": "gierig", "distractors": ["kichernd"]},
    "schludrig": {"correct": "nachlässig", "distractors": ["schlammig"]},
    "fätzä": {"correct": "herumrennen", "distractors": ["zerreißen"]},
    "tschäderä": {"correct": "klappern", "distractors": ["reden"]},
    "schwubblä": {"correct": "herumzappeln", "distractors": ["schwimmen"]},
    "tätschä": {"correct": "klatschen", "distractors": ["tanzen"]},
    "güggs": {"correct": "Hahn", "distractors": ["Gurke"]},
    "pfusä": {"correct": "schlafen", "distractors": ["arbeiten"]},
    "schlürfä": {"correct": "schlürfen", "distractors": ["schlurfen"]},
    "gfrässig": {"correct": "gefräßig", "distractors": ["frech"]},
    "schlönzlig": {"correct": "rotzig", "distractors": ["schlank"]},
    "bögg": {"correct": "Strohfigur", "distractors": ["Berg"]},
    "schpienzä": {"correct": "spionieren", "distractors": ["spielen"]},
    "schlänggä": {"correct": "schlängeln", "distractors": ["schlagen"]},
    "schwytzä": {"correct": "schwitzen", "distractors": ["schweigen"]},
    "gümmelä": {"correct": "herumtrödeln", "distractors": ["springen"]},
    "schlufi": {"correct": "Langweiler", "distractors": ["Schlupfloch"]},
    "rüffä": {"correct": "tadeln", "distractors": ["rufen"]},
    "schmöisä": {"correct": "werfen", "distractors": ["schmieren"]},
    "tätschlig": {"correct": "robust", "distractors": ["tänzerisch"]},
    "bsetzistei": {"correct": "Pflasterstein", "distractors": ["Besenstiel"]},
    "zägg": {"correct": "Schlag", "distractors": ["Zacke"]},
    "schlunz": {"correct": "Dreck", "distractors": ["Schlupf"]},
    "güx": {"correct": "kurzer Blick", "distractors": ["Guss"]},
    "schpöitzä": {"correct": "spucken", "distractors": ["spritzen"]},
    "schwubblig": {"correct": "zappelig", "distractors": ["schwammig"]},
    "gnusch": {"correct": "Durcheinander", "distractors": ["Knoten"]},
    "tschumpel": {"correct": "ungeschickter Mensch", "distractors": ["Schimpanse"]},
    "gümmel": {"correct": "Trödler", "distractors": ["Gummi"]},
    "tschäderlig": {"correct": "klappernd", "distractors": ["tänzelnd"]},
    "pfuslig": {"correct": "schlampig", "distractors": ["schläfrig"]},
    "schwytzig": {"correct": "verschwitzt", "distractors": ["schweizerisch"]},
}

joke_prizes = [
    "You win a virtual fondue set 🫕",
    "Your neighbor now respects your laundry slot 🧺",
    "You unlocked the secret to Bernese dialect. Just kidding 😅",
    "You get a free permit to complain about SBB delays 🚆",
    "You are now fluent in passive-aggressive notes 📄",
]

# Initialize session state
if "round" not in st.session_state:
    st.session_state.round = 1
    st.session_state.score = 0
    st.session_state.history = []
    st.session_state.current_prompt = None
    st.session_state.options = []
    st.session_state.correct_answer = None
    st.session_state.feedback_shown = False
    st.session_state.used_prompts = []

# Spielername und Tierkopf
animal_emojis = {
    "hund": "🐶",
    "katze": "🐱",
    "fuchs": "🦊",
    "bär": "🐻",
    "panda": "🐼",
    "löwe": "🦁",
    "frosch": "🐸",
    "affe": "🐵",
    "pinguin": "🐧",
    "huhn": "🐔",
}

# Umgekehrtes Mapping: Emoji → Tiername
emoji_to_name = {v: k for k, v in animal_emojis.items()}

st.sidebar.header("👤 Spielerprofil")
player_name = st.sidebar.text_input("Dein Name", value="Gast")
animal_options = list(animal_emojis.items())
selected = st.sidebar.selectbox("Wähle deinen Tierkopf", animal_options, format_func=lambda x: x[1])

# Ergebnis:
st.session_state.player_name = player_name
st.session_state.animal = selected[0]       # z. B. "hund"
st.session_state.animal_icon = selected[1]  # z. B. "🐶"

project_id = "my-sh-project-398715"
dataset_id = "spelling_data"
table_id = "ranking"

client = bigquery.Client(project=project_id)

def fetch_leaderboard():
    query = f"""
        SELECT user, animal, percentage, required_time
        FROM `{project_id}.{dataset_id}.{table_id}`
        ORDER BY percentage DESC, required_time ASC
        LIMIT 5
    """
    return client.query(query).to_dataframe()


def show_leaderboard():
    df = fetch_leaderboard()
    df["Ergebnis"] = df["percentage"].astype(str)
    df["Zeit"] = df["required_time"]
    df["Spieler"] = df["animal"].map(animal_emojis) + " " + df["user"]

    display_df = df[["Spieler", "Ergebnis", "Zeit"]]

    st.sidebar.markdown("---")
    st.sidebar.subheader("🏆 Rangliste")
    st.sidebar.dataframe(display_df.reset_index(drop=True), use_container_width=True, hide_index=True)

show_leaderboard()

def setup_round():
    available_prompts = [p for p in word_bank.keys() if p not in st.session_state.used_prompts]
    if not available_prompts:
        st.session_state.round = 999  # trigger end screen
        return

    prompt = random.choice(available_prompts)
    entry = word_bank[prompt]
    correct_answer = entry["correct"]
    distractors = entry["distractors"]

    options = [correct_answer] + distractors
    random.shuffle(options)

    st.session_state.current_prompt = prompt
    st.session_state.correct_answer = correct_answer
    st.session_state.options = options
    st.session_state.feedback_shown = False
    st.session_state.used_prompts.append(prompt)

max_rounds = 2

# Setup first round
if st.session_state.current_prompt is None and st.session_state.round <= max_rounds:
    setup_round()

st.markdown(
    "<div style='text-align: center'><img src='https://upload.wikimedia.org/wikipedia/commons/f/f3/Flag_of_Switzerland.svg' width='50'></div>",
    unsafe_allow_html=True
)

st.title("Swiss German Quiz")

if "game_started" not in st.session_state:
    st.session_state.game_started = False

if not st.session_state.game_started:
    if st.button("▶️ Spiel starten"):
        st.session_state.game_started = True
        st.session_state.start_time = time.time()
        st.rerun()
    else:
        st.stop()  # Prevent rest of app from running until started

current_display_round = min(st.session_state.round, max_rounds)
st.markdown(f"**Punkte:** {st.session_state.score} (Frage {current_display_round} von {max_rounds})")
st.markdown(f"### {st.session_state.animal_icon} {st.session_state.player_name} spielt gerade")

# Game loop
if st.session_state.round <= max_rounds and st.session_state.current_prompt is not None:
    st.markdown(
        f"<h2 style='text-align: center; font-size: 36px;'>{st.session_state.current_prompt}</h2>",
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    cols = st.columns(len(st.session_state.options))
    for i, option in enumerate(st.session_state.options):
        if cols[i].button(option) and not st.session_state.feedback_shown:
            st.session_state.feedback_shown = True

            if option == st.session_state.correct_answer:
                st.success("✅ Korrekt!")
                st.session_state.score += 10
            else:
                st.error("❌ Leider nein!")
                st.markdown(f"richtige Antwort: `{st.session_state.correct_answer}`")

            st.session_state.history.append((st.session_state.current_prompt, option))

            with st.empty():
                time.sleep(2)
                st.session_state.round += 1
                setup_round()
                st.rerun()

def save_result_to_bigquery():
    end_time = time.time()
    raw_seconds = round(end_time - st.session_state.start_time)
    duration_str = str(timedelta(seconds=raw_seconds))  # e.g. '0:00:35'
    row = {
        "user": st.session_state.player_name,
        "animal": st.session_state.animal,
        "percentage": int((st.session_state.score / (max_rounds * 10)) * 100),
        "required_time": duration_str,
        "run_date": datetime.now(timezone.utc).date().isoformat()
    }
    st.markdown(row)
    st.markdown(f"{project_id}.{dataset_id}.{table_id}")
    errors = client.insert_rows_json(f"{project_id}.{dataset_id}.{table_id}", [row])
    if errors:
        st.error(errors)
        st.error("❌ Fehler beim Speichern in BigQuery")
    else:
        st.success("✅ Ergebnis gespeichert!")

# End of game
if st.session_state.round > max_rounds:
    if "result_saved" not in st.session_state:
        save_result_to_bigquery()
    st.session_state.result_saved = True

    st.header("🏁 Spiel vorbei")
    st.markdown(f"**Punkte:** {st.session_state.score}")

    if st.session_state.score >= 40:
        st.success("🏅 Du bist ein Bewilligungs-Paladin!")
    elif st.session_state.score >= 25:
        st.info("🎖️ Du bist ein Kantönli-Kenner.")
    else:
        st.warning("📄 Das ist ausbaufähig. Probier es nochmal ...")

    if st.button("Nochmal spielen"):
        st.session_state.clear()
        st.rerun()
