import streamlit as st
import pickle
import requests
import html
import re

anime_list = pickle.load(open("anime_list.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

ANILIST_URL = "https://graphql.anilist.co"
ANILIST_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    coverImage {
      large
    }
  }
}
"""

def _try_anilist(name):
    """Single AniList API call. Returns image URL or None."""
    try:
        response = requests.post(
            ANILIST_URL,
            json={"query": ANILIST_QUERY, "variables": {"search": name}},
            timeout=8,
        )
        if response.status_code == 200:
            data = response.json()
            media = data.get("data", {}).get("Media")
            if media:
                return media["coverImage"]["large"]
    except Exception:
        pass
    return None

@st.cache_data(show_spinner=False)
def fetch_image(anime_name):
    """Fetch anime cover image from AniList, trying name variations."""
    # Clean HTML entities (e.g. &#039; → ')
    clean_name = html.unescape(anime_name).strip()

    # Build list of name variations to try
    variations = [clean_name]

    # Remove parenthetical suffixes like (TV), (2011), (OVA)
    no_parens = re.sub(r'\s*\([^)]*\)\s*$', '', clean_name).strip()
    if no_parens and no_parens != clean_name:
        variations.append(no_parens)

    # Remove everything after colon (e.g. "Death Note: Rewrite" → "Death Note")
    if ':' in clean_name:
        before_colon = clean_name.split(':')[0].strip()
        if before_colon and before_colon not in variations:
            variations.append(before_colon)

    for name in variations:
        result = _try_anilist(name)
        if result:
            return result

    return None

st.title("🎌 Anime Recommendation System")
st.write("Find anime similar to your favorite anime")

anime_name = st.selectbox("Select an Anime", anime_list["name"].values)

if st.button("Recommend"):
    index = anime_list[anime_list["name"] == anime_name].index[0]
    similar_indices = similarity[index][:5]
    st.subheader("Recommended Anime")
    cols = st.columns(5)
    for col, i in zip(cols, similar_indices):
        with col:
            name = anime_list.iloc[i]["name"]
            rating = anime_list.iloc[i]["rating"]

            # Use stored URL if valid, otherwise fetch from AniList
            image_url = anime_list.iloc[i]["image_url"]
            if not image_url or not str(image_url).startswith("http"):
                image_url = fetch_image(name)

            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.image("https://placehold.co/150x220?text=N/A", use_container_width=True)

            st.write(f"**{html.unescape(name)}**")
            st.write("⭐", rating)