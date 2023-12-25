import os
import requests
import pandas as pd
import streamlit as st

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

# st.set_page_config(layout = "wide")
st.set_page_config(page_title = "Letterboxd CSV Generator", layout = "wide")



# Options in sidebar
option_language = st.sidebar.radio(f"**{'Title Language'}**:", ("Original", "English"))



# Dashboard title
st.title("Letterboxd CSV Generator")

# Search bar
search = st.text_input(f"**{'Search'}**:").replace(" ", "+") # TODO: Check for more replacements
url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={TMDB_API_KEY}"
r = requests.get(url) # TODO: Handle possible request errors
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

    # st.dataframe(data) # TODO: Delete later

    # Select movie
    def get_title_year(df, id, language):
        # TODO: Handle when no release date
        if language == "Original":
            title = df[df["id"] == id]["original_title"].item()
        else:
            title = df[df["id"] == id]["title"].item()
        year = df[df["id"] == id]["release_date"].item().split("-")[0]
        return title + " (" + year + ")"
    movie = st.selectbox(f"**{'Select Movie'}**:", data["id"], format_func = lambda x: get_title_year(data, x, option_language))

    # New query for more details
    url_details = f"https://api.themoviedb.org/3/movie/{movie}?api_key={TMDB_API_KEY}"
    r_details = requests.get(url_details)
    movie_details = r_details.json()

    def get_genres(movie_details):
        genres = [i.get("name") for i in movie_details["genres"]]
        if len(genres) == 1:
            return genres[0]
        else:
            last_two = genres[-2] + " and " + genres[-1]
            del genres[-2:]
            genres.append(last_two)
            return ", ".join(genres)
    def get_hour_min(movie_details):
        minutes = movie_details["runtime"]
        hours = minutes // 60
        minutes -= hours * 60
        return str(hours) + "h " + str(minutes) + "m"
    def get_date(movie_details):
        ymd = movie_details["release_date"].split("-")
        return "/".join(ymd[::-1])

    # Movie Title
    if option_language == "Original":
        st.header(movie_details["original_title"])
    else:
        st.header(movie_details["title"])
    # Movie poster and some details
    col_1, col_2 = st.columns([1, 4])
    col_1.image(f"https://image.tmdb.org/t/p/original/{movie_details['poster_path']}")
    col_2.write(f"**{'Overview'}**: {movie_details['overview']}")
    col_2.write(f"**{'Genres'}**: {get_genres(movie_details)}") # TODO: Handle missing genres, runtime and release_date
    col_2.write(f"**{'Runtime'}**: {get_hour_min(movie_details)}")
    col_2.write(f"**{'Release Date'}**: {get_date(movie_details)}")
    col_2.write(f"**{'Average Rating'}**: {str(round(movie_details['vote_average']*10, 2)) + '%'}")
    col_2.write(f"**{'IMDb ID'}**: {movie_details['imdb_id']}")

