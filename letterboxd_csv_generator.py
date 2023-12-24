import os
import requests
import pandas as pd
import streamlit as st

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")



# Options in sidebar
option_title = st.sidebar.radio("Title:", ("Original", "English"))



# Dashboard title
st.title("Letterboxd CSV Generator")

# Search bar
search = st.text_input("Search:").replace(" ", "+") # Check for more replacements
url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={TMDB_API_KEY}"
r = requests.get(url) # Handle possible request errors
r_json = r.json()

# Search results
if search == "":
    st.error("Empty search!", icon = "🚨")
elif r_json.get("total_results") == 0:
    st.error("Zero results!", icon = "🚨")
else:
    # Get data from every page
    data = []
    for i in range(1, r_json.get("total_pages") + 1):
        url_i = f"https://api.themoviedb.org/3/search/movie?query={search}&page={i}&api_key={TMDB_API_KEY}"
        r_i = requests.get(url_i)
        r_json_i = r_i.json()
        data_i = r_json_i["results"] # List of dicts
        data.extend(data_i)          # Add data_i elements to data_temp
    data = pd.DataFrame(data)
    data.sort_values(by = ["popularity"], ascending = False, inplace = True)
    st.dataframe(data)

