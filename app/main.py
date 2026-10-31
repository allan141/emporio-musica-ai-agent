"""Run with: streamlit run app/main.py"""
import sys
from pathlib import Path

# Streamlit runs this file as a script: keep project root importable.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from app.agent import StoreAgent

st.set_page_config(page_title="Empório da Música | AI Assistant", page_icon="🎸", layout="centered")
st.title("🎸 Empório da Música")
st.caption("Sua música começa aqui. Protótipo acadêmico — dados demonstrativos, não em tempo real.")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent" not in st.session_state:
    try:
        st.session_state.agent = StoreAgent()
    except Exception as error:
        st.error(f"Could not initialize the assistant: {error}")
        st.stop()

with st.sidebar:
    st.subheader("Sobre o protótipo")
    st.write("Consultas demonstrativas de catálogo, pedidos e políticas da loja.")
    st.warning("Os dados são um snapshot CSV. Não representam estoque ou entregas em tempo real.")
    if st.button("Nova conversa"):
        st.session_state.messages = []
        st.session_state.agent = StoreAgent()
        st.rerun()

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

if prompt := st.chat_input("Pergunte sobre instrumentos, preços, pedidos ou trocas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Consultando informações da loja..."):
            try:
                answer = st.session_state.agent.send(prompt)
            except Exception as error:
                answer = ("Não consegui consultar o modelo agora. Verifique sua chave, modelo e limites "
                          f"da API. Detalhe técnico: {type(error).__name__}")
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
