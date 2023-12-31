import streamlit as st
import requests
import pandas as pd

# Local API KEY
# import os
# TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

# Cloud API KEY
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]



# Functions
@st.cache_data
def get_query(search):
    url = f"https://api.themoviedb.org/3/search/movie?query={search}&api_key={TMDB_API_KEY}"
    return requests.get(url).json()

@st.cache_data
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

@st.cache_data
def get_movie_information(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    return requests.get(url).json()

@st.cache_data
def movie_title_year(df, id, language):
    # TODO: Handle when no release date
    if language == "Original":
        title = df[df["id"] == id]["original_title"].item()
    else:
        title = df[df["id"] == id]["title"].item()
    year = df[df["id"] == id]["release_date"].item().split("-")[0]
    return title + " (" + year + ")"

@st.cache_data
def movie_title(df):
    if option_title_language == "Original":
        return df["original_title"]
    else:
        return df["title"]

@st.cache_data
def movie_genres(df):
    genres = [i.get("name") for i in df["genres"]]
    if len(genres) == 1:
        return genres[0]
    else:
        last_two = genres[-2] + " and " + genres[-1]
        del genres[-2:]
        genres.append(last_two)
        return ", ".join(genres)

@st.cache_data
def movie_runtime(df):
    minutes = df["runtime"]
    hours = minutes // 60
    minutes -= hours * 60
    return str(hours) + "h " + str(minutes) + "m"

@st.cache_data
def movie_release_date(df):
    ymd = df["release_date"].split("-")
    return "/".join(ymd[::-1])

@st.cache_data
def movie_average_rating(df):
    return str(round(df['vote_average']*10, 2)) + '%'

def movie_output_reviews(output_reviews, x):
    if x in output_reviews.keys():
        return output_reviews.get(x)
    else:
        return [None, None]

def create_output_df():
    output_tmdb_id = list(st.session_state["output_tmdb_id"].keys())
    output_dict = {"tmdbID": output_tmdb_id}
    if option_id == "IMDbID":
        output_imdb_id = list(map(lambda x: st.session_state["output_tmdb_id"].get(x)["imdb_id"], output_tmdb_id))
        output_dict["imdbID"] = output_imdb_id
        output_dict.pop("tmdbID")
    if option_title:
        output_title = list(map(lambda x: movie_title(st.session_state["output_tmdb_id"].get(x)), output_tmdb_id))
        output_dict["Title"] = output_title
    if option_year:
        output_year = list(map(lambda x: movie_release_date(st.session_state["output_tmdb_id"].get(x)).split("/")[-1], output_tmdb_id))
        output_dict["Year"] = output_year
    if option_rating:
        output_rating = list(map(lambda x: movie_output_reviews(st.session_state["output_reviews"], x)[0], output_tmdb_id))
        output_dict["Rating10"] = output_rating
    if option_review:
        output_review = list(map(lambda x: movie_output_reviews(st.session_state["output_reviews"], x)[1], output_tmdb_id))
        output_dict["Review"] = output_review
    return pd.DataFrame.from_dict(output_dict)



# Initialize variables to store values of multitple reruns
if "output_tmdb_id" not in st.session_state:
    st.session_state["output_tmdb_id"] = dict()
if "output_reviews" not in st.session_state:
    st.session_state["output_reviews"] = dict()



# Page configuration
st.set_page_config(page_title = "Letterboxd CSV Generator", page_icon = "🎥", layout = "wide")

# Sidebar
st.sidebar.write("Search Title Language:")
option_title_language = st.sidebar.radio("Search Title Language:", ("Original", "English"), label_visibility = "collapsed")
st.sidebar.write("CSV:")
option_id = st.sidebar.radio("ID:", ("TMDbID", "IMDbID"), label_visibility = "collapsed")
option_title = st.sidebar.checkbox("Title")
option_year = st.sidebar.checkbox("Year")
st.sidebar.write("Review:")
option_rating = st.sidebar.checkbox("Rating")
option_review = st.sidebar.checkbox("Review")


# Title
st.title("Letterboxd CSV Generator")

# Search bar
input_search = st.text_input(f"**{'Search'}**:").replace(" ", "+") # TODO: Check for more replacements
search_query = get_query(input_search)

# Search results
if input_search != "" and search_query.get("total_results") == 0:
    st.error("Zero results!", icon = "🚨")
elif input_search != "":
    # Search input
    search_data = get_data_in_query(input_search)
    input_movie_id = st.selectbox(f"**{'Select Movies'}**:", search_data["id"], format_func = lambda x: movie_title_year(search_data, x, option_title_language))

    # Movie information
    # New query for more information
    movie_info = get_movie_information(input_movie_id)

    # Movie title
    st.header(movie_title(movie_info))
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

    # Subset of movie_info to be used in create_output_df()
    movie_info_subset = {key: value for key, value in movie_info.items() if key in ("imdb_id", "original_title", "title", "release_date")}

    # User review
    if option_rating or option_review:
        movie_review = st.form("movie_review", clear_on_submit = True, border = False)
        movie_review.header("Movie Review")
        if option_rating: 
            input_movie_rating = movie_review.slider("Rating:", 1, 10, 5, 1)
        else:
            input_movie_rating = None
        if option_review:
            input_movie_review = movie_review.text_area("Review:")
        else:
            input_movie_review = None
        if movie_review.form_submit_button("Add to CSV"):
            st.session_state["output_tmdb_id"][input_movie_id] = movie_info_subset
            st.session_state["output_reviews"][input_movie_id] = [input_movie_rating, input_movie_review]
    else:
        add_to_csv = st.button("Add to CSV")
        if add_to_csv:
            st.session_state["output_tmdb_id"][input_movie_id] = movie_info_subset

# Output
st.header("CSV")
st.data_editor(create_output_df(), num_rows = "dynamic")

