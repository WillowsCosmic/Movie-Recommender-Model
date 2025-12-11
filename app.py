import streamlit as st
import pickle
import pandas as pd
import requests
import os

import time
from functools import lru_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import gdown
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "gdown"])
    import gdown

st.set_page_config(  
    page_title="Movie Recommender System",  
    page_icon="🎬",  
    layout="wide"  
)

MOVIES_FILE_ID = "19w6iEsn353beu-ff6aiCB-IuFll4xOMl"
SIMILARITY_FILE_ID = "1-xv-m08NhIrk68GXzYqRvQ_rab9shvrD"

@st.cache_resource
def download_files():
    if not os.path.exists('movies.pkl'):
        with st.spinner('📥 Downloading movie data...'):
            try:
                url = f'https://drive.google.com/uc?id={MOVIES_FILE_ID}'
                gdown.download(url, 'movies.pkl', quiet=False)
                st.success('✅ Movie data downloaded!')
            except Exception as e:
                st.error(f"❌ Error downloading movies.pkl: {e}")
                return False
    
    if not os.path.exists('similarity.pkl'):
        with st.spinner('📥 Downloading similarity matrix (176 MB)... This will take ~30 seconds'):
            try:
                url = f'https://drive.google.com/uc?id={SIMILARITY_FILE_ID}'
                gdown.download(url, 'similarity.pkl', quiet=False)
                st.success('✅ Similarity matrix downloaded!')
            except Exception as e:
                st.error(f"❌ Error downloading similarity.pkl: {e}")
                return False
    
    return True

@st.cache_data
def load_data():
    if not download_files():
        st.error("⚠️ Failed to download model files.")
        st.stop()
    
    try:
        movies_list = pickle.load(open('movies.pkl', 'rb'))
        similarity = pickle.load(open('similarity.pkl', 'rb'))
        return movies_list, similarity
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        st.stop()

movies_list, similarity = load_data()
movies = movies_list
movie_titles = movies_list['title'].tolist()

API_KEY = "2bf0d9cdd98c101e0f531525a622c3b6"

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

@lru_cache(maxsize=5000)
def safe_tmdb_fetch(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    time.sleep(0.05)

    try:
        r = session.get(url, timeout=5)
        return r.json()
    except Exception as e:
        print("TMDb Error:", e)
        return {}

def fetch_poster(movie_id): 
    data = safe_tmdb_fetch(movie_id)
    poster_path = data.get("poster_path")
    if poster_path:
        return "https://image.tmdb.org/t/p/w500/" + poster_path

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)),reverse=True,key=lambda x:x[1])[1:6]
    
    recommended_movies = []
    recommended_movies_posters = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies,recommended_movies_posters

st.title('Movie Recommender System')

selected_movie_name = st.selectbox(
    "Select a movie", movie_titles
)

st.markdown("""
<style>
    .main-title {  
        text-align: center;  
        font-size: 3.5rem;  
        font-weight: bold;  
        background: linear-gradient(120deg, #e74c3c, #8e44ad, #3498db);  
        -webkit-background-clip: text;  
        -webkit-text-fill-color: transparent;  
        margin-bottom: 0.5rem;  
        padding: 1rem 0;  
    }  
    
    .subtitle {  
        text-align: center;  
        font-size: 1.2rem;  
        color: #95a5a6;  
        margin-bottom: 2rem;  
    }  
    
    .movie-card {  
        text-align: center;  
        padding: 0.5rem;  
        transition: transform 0.3s ease;  
    }  
    
    .movie-card:hover {  
        transform: translateY(-10px);  
    }  
    
    .movie-title {  
        font-size: 1rem;  
        font-weight: 600;  
        margin-top: 0.8rem;  
        color: #ecf0f1;  
        min-height: 48px;  
        display: flex;  
        align-items: center;  
        justify-content: center;  
        text-align: center;  
        line-height: 1.4;  
    }  
    .stButton>button {  
        width: 100%;  
        background: linear-gradient(90deg, #e74c3c, #8e44ad);  
        color: white;  
        font-size: 1.1rem;  
        font-weight: 600;  
        padding: 0.75rem 2rem;  
        border-radius: 8px;  
        border: none;  
        transition: all 0.3s ease;  
        margin-top: 1rem;  
    }  
    
    .stButton>button:hover {  
        background: linear-gradient(90deg, #c0392b, #6c3483);  
        transform: scale(1.02);  
    }  
    
    .stSelectbox {  
        margin-bottom: 1rem;  
    }  
</style>
""", unsafe_allow_html=True)

if st.button('Recommend'):
    names, posters = recommend(selected_movie_name)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]
    
    for i, col in enumerate(cols):
        with col:
            st.image(posters[i], use_container_width=True)
            st.markdown(f'<div class="movie-title">{names[i]}</div>', 
                       unsafe_allow_html=True)