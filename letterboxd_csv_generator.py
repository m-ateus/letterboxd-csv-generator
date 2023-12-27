import os
import requests
import pandas as pd
import streamlit as st

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")



# API functions
def get_query(search):
    url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={TMDB_API_KEY}"
    return requests.get(url).json()

def get_data_in_query(search):
    data = []
    for i in range(1, get_query(search).get("total_pages") + 1):
        url_i = f"https://api.themoviedb.org/3/search/movie?query={search}&page={i}&api_key={TMDB_API_KEY}"
        r_i = requests.get(url_i)
        r_json_i = r_i.json()
        data_i = r_json_i["results"] # List of dicts
        data.extend(data_i)          # Add data_i elements to data_temp
    data = pd.DataFrame(data)
    data.sort_values(by = ["popularity"], ascending = False, inplace = True)
    return data

def get_movie_information(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    return requests.get(url).json()

def movie_title_year(df, id, language):
    # TODO: Handle when no release date
    if language == "Original":
        title = df[df["id"] == id]["original_title"].item()
    else:
        title = df[df["id"] == id]["title"].item()
    year = df[df["id"] == id]["release_date"].item().split("-")[0]
    return title + " (" + year + ")"

def movie_genres(df):
    genres = [i.get("name") for i in df["genres"]]
    if len(genres) == 1:
        return genres[0]
    else:
        last_two = genres[-2] + " and " + genres[-1]
        del genres[-2:]
        genres.append(last_two)
        return ", ".join(genres)

def movie_runtime(df):
    minutes = df["runtime"]
    hours = minutes // 60
    minutes -= hours * 60
    return str(hours) + "h " + str(minutes) + "m"

def movie_release_date(df):
    ymd = df["release_date"].split("-")
    return "/".join(ymd[::-1])

def movie_average_rating(df):
    return str(round(df['vote_average']*10, 2)) + '%'



# Page configuration
st.set_page_config(page_title = "Letterboxd CSV Generator", layout = "wide")

# Sidebar
st.sidebar.write("Title Language:")
option_title_language = st.sidebar.radio("Title Language:", ("Original", "English"), label_visibility = "collapsed")
st.sidebar.write("Review:")
option_rating = st.sidebar.checkbox("Rating")
option_review = st.sidebar.checkbox("Write a review")

# Title
st.title("Letterboxd CSV Generator")

# Search bar
input_search = st.text_input(f"**{'Search'}**:").replace(" ", "+") # TODO: Check for more replacements
search_query = get_query(input_search)

# Search results
if input_search == "":
    st.error("Empty search!", icon = "🚨")
elif search_query.get("total_results") == 0:
    st.error("Zero results!", icon = "🚨")
else:
    data = get_data_in_query(input_search)

    # st.dataframe(data) # TODO: Delete later

    input_movie_id = st.selectbox(f"**{'Select Movie'}**:", data["id"], format_func = lambda x: movie_title_year(data, x, option_title_language))

    # New query for more details
    movie_info = get_movie_information(input_movie_id)


    # Movie title
    if option_title_language == "Original":
        st.header(movie_info["original_title"])
    else:
        st.header(movie_info["title"])
    # Movie information
    col_1, col_2 = st.columns([1, 4])
    col_1.image(f"https://image.tmdb.org/t/p/original/{movie_info['poster_path']}")
    col_2.write(f"**{'Overview'}**: {movie_info['overview']}")
    col_2.write(f"**{'Genres'}**: {movie_genres(movie_info)}") # TODO: Handle missing genres, runtime and release_date
    col_2.write(f"**{'Runtime'}**: {movie_runtime(movie_info)}")
    col_2.write(f"**{'Release Date'}**: {movie_release_date(movie_info)}")
    col_2.write(f"**{'Average Rating'}**: {movie_average_rating(movie_info)}")
    col_2.write(f"**{'TMDb ID'}**: {input_movie_id}")
    col_2.write(f"**{'IMDb ID'}**: {movie_info['imdb_id']}")

    # Initialize empty dataframe
    if "letterboxd_df" not in st.session_state:
        st.session_state["letterboxd_df"] = pd.DataFrame(columns = ["tmdbID"])

    st.write(st.session_state["letterboxd_df"])

