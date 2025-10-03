import streamlit as st
import random
import time

# Word bank: prompt → correct answer
word_bank = {
    "chuchichäschtli": ["Küchenschränkchen", "Uhrenkästchen"],
    "gschwind": ["schnell", "windig"],
    "gfrörli": ["Person, die immer friert", "Eis"],
    "gschnägg": ["Schnecke", "schick"],
    "grüezi": ["Hallo", "Auf Wiedersehen"],
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

def setup_round():
    available_prompts = [p for p in word_bank.keys() if p not in st.session_state.used_prompts]
    if not available_prompts:
        st.session_state.round = 999  # trigger end screen
        return

    prompt = random.choice(available_prompts)
    correct = word_bank[prompt]
    distractors = random.sample([v for v in word_bank.values() if v != correct], 2)
    options = distractors + [correct]
    options = word_bank.values()
    random.shuffle(options)

    st.session_state.current_prompt = prompt
    st.session_state.correct_answer = correct
    st.session_state.options = options
    st.session_state.feedback_shown = False
    st.session_state.used_prompts.append(prompt)

# Setup first round
if st.session_state.current_prompt is None and st.session_state.round <= 5:
    setup_round()

st.markdown(
    "<div style='text-align: center'><img src='https://upload.wikimedia.org/wikipedia/commons/f/f3/Flag_of_Switzerland.svg' width='50'></div>",
    unsafe_allow_html=True
)

st.title("Swiss German Quiz")
#st.subheader(f"Frage {st.session_state.round} von 5")
st.markdown(f"**Punkte:** {st.session_state.score} (Frage {st.session_state.round} von 5)")

# Game loop
if st.session_state.round <= 5:
    st.markdown(
        f"<h2 style='text-align: center; font-size: 36px;'>{st.session_state.current_prompt}</h2>",
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    # Show buttons for each option
    cols = st.columns(3)
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

            # Delay and rerun
            with st.empty():
                time.sleep(2)
                st.session_state.round += 1
                setup_round()
                st.rerun()

# End of game
if st.session_state.round > 5:
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
