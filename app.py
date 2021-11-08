import streamlit as st
from multiapp import MultiApp
from apps import home, state, nation # import your app modules here

app = MultiApp()

# set page config and layout
# TODO potentially add more configurations
st.set_page_config(layout='wide')
# Add all your application here
app.add_app("Home", home.app)
app.add_app("State/County view", state.app)
app.add_app("National view", nation.app)

# The main app
app.run()