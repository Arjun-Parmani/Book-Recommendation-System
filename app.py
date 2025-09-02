import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests
from PIL import Image, ImageDraw
import io
import os
import base64

# ---------------------------
# Page config
# ---------------------------
st.set_page_config(
    page_title="BookVault Recommender",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# CSS (light, clean + hover)
# ---------------------------
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #1F2937; }

    .main-header {
        font-size: 2.4rem; color: #111827; text-align: center;
        margin-bottom: 1.5rem; font-weight: 800;
    }
    .sub-header { font-size: 1.4rem; color: #111827; margin-bottom: 1rem; font-weight: 700; }

    /*.book-card {
        background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        transition: transform .2s ease, box-shadow .2s ease;
    }
    .book-card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }*/

    /* Fixed-size cover container + hover */
    .cover-wrap {
        width: 160px; height: 240px; margin: 0 auto 8px auto;
        border-radius: 10px; overflow: hidden; background: #F3F4F6;
    }
    .cover-img {
        display: block; width: auto; max-width: 100%;
        height: 100%; max-height: 100%;
        object-fit: contain; image-rendering: 100%;
        transition: transform .18s ease, box-shadow .18s ease;
    }
    .cover-wrap:hover .cover-img {
        transform: scale(1.03);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        cursor: pointer;
    }
    .header{
    font-color=#ffffff
    }

    .book-title { font-size: 1.05rem; font-weight: 700; color: #111827; margin: 10px 0 6px; }
    .book-author { font-size: .95rem; color: #374151; margin-bottom: 8px; font-style: italic; }

    .rating-badge {
        background-color: #FACC15; color: #1E293B; padding: 4px 8px; border-radius: 12px;
        font-size: .8rem; font-weight: 700; display: inline-block; margin-right: 8px;
    }
    .rating-count { color: #374151; font-size: .9rem; }

    .stButton > button {
      background-color: #FFFFFF !important; color: #111827 !important;
      border: 1px solid #E5E7EB !important; border-radius: 8px !important;
      padding: .6rem 1rem !important; font-weight: 700 !important;
      box-shadow: 0 1px 2px rgba(0,0,0,.05) !important;
    }
    .stButton > button:hover { background-color: #F9FAFB !important; border-color: #D1D5DB !important; box-shadow: 0 2px 8px rgba(0,0,0,.08) !important; }
    .stButton > button:active { background-color: #F3F4F6 !important; }
    .stButton > button:focus { outline: none !important; box-shadow: 0 0 0 3px rgba(37,99,235,.15) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Data loading
# ---------------------------
@st.cache_data(show_spinner=False)
def _load_pickle(path: str):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

@st.cache_data(show_spinner=True)
def load_data():
    books = _load_pickle('books.pkl')
    pt = _load_pickle('pt.pkl')
    popular_df = _load_pickle('Popular.pkl')  # optional
    similarity_scores = _load_pickle('similarity_scores.pkl')
    missing = []
    if books is None: missing.append('books.pkl')
    if pt is None: missing.append('pt.pkl')
    if similarity_scores is None: missing.append('similarity_scores.pkl')
    return books, pt, popular_df, similarity_scores, missing

books, pt, popular_df, similarity_scores, missing = load_data()

if missing:
    st.error(f"Missing files: {', '.join(missing)}. Please place them next to this app.")
    st.stop()

# ---------------------------
# Image helpers (no crop, no upscale)
# ---------------------------
def _normalize_url(u: str) -> str:
    if not isinstance(u, str): return ""
    u = u.strip()
    if not u: return ""
    if u.startswith("//"): u = "https:" + u
    if u.startswith("http://"): u = u.replace("http://", "https://", 1)
    u = u.replace("images.amazon.com/images/P/", "images-na.ssl-images-amazon.com/images/P/")
    return u

@st.cache_data(show_spinner=False, ttl=3600)
def _fetch_image(url: str):
    if not isinstance(url, str) or not url.strip():
        return None
    try:
        r = requests.get(
            _normalize_url(url), timeout=6, allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (BookVault/1.0)"}
        )
        if r.status_code != 200 or "image" not in r.headers.get("Content-Type","").lower():
            return None
        return Image.open(io.BytesIO(r.content))
    except Exception:
        return None

def _placeholder_cover(title: str, w: int = 160, h: int = 240):
    img = Image.new("RGB", (w, h), (243, 244, 246))  # neutral-100
    draw = ImageDraw.Draw(img)
    text = (title or "No Cover")[:100]
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if len((cur + " " + wd).strip()) <= 16:
            cur = (cur + " " + wd).strip()
        else:
            lines.append(cur); cur = wd
    if cur: lines.append(cur)
    y = h // 2 - min(5, len(lines)) * 16
    for ln in lines[:5]:
        draw.text((12, y), ln, fill=(55, 65, 81))
        y += 28
    return img

def _resolve_cover_from_row(row: dict):
    for col in ("Image-URL-M", "Image-URL-L", "Image-URL-S"):
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            img = _fetch_image(str(row[col]))
            if img: return img
    isbn = str(row.get("ISBN", "") or "").replace("-", "").strip()
    if isbn:
        ol = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg?default=false"
        img = _fetch_image(ol)
        if img: return img
    return _placeholder_cover(row.get("Book-Title", ""))

def _resolve_cover_from_title(title: str):
    tmp = books[books['Book-Title'] == title].drop_duplicates('Book-Title')
    if not tmp.empty:
        return _resolve_cover_from_row(tmp.iloc[0].to_dict())
    return _placeholder_cover(title)

def cover_html(img: Image.Image, canvas_w: int = 160, canvas_h: int = 240, pad: int = 8) -> str:
    """Return a <div class='cover-wrap'><img class='cover-img' .../></div> with no upscaling/cropping."""
    if img is None:
        img = _placeholder_cover("", canvas_w, canvas_h)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")

    # downscale to fit inside the canvas, never upscale
    box_w = max(1, canvas_w - 2 * pad)
    box_h = max(1, canvas_h - 2 * pad)
    w, h = img.size
    scale = min(1.0, min(box_w / float(w), box_h / float(h)))
    new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
    if (new_w, new_h) != (w, h):
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # encode to base64 (no Streamlit deprecation warnings)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # center within the fixed container via CSS
    return f"""
    <div class="cover-wrap">
      <img class="cover-img" src="data:image/png;base64,{b64}" alt="cover"/>
    </div>
    """

# ---------------------------
# Recommendation logic 
# ---------------------------
def recommend(book_name: str, top_k: int = 6):
    try:
        if book_name not in pt.index:
            return []
        index = np.where(pt.index == book_name)[0][0]
        similar_items = sorted(
            list(enumerate(similarity_scores[index])),
            key=lambda x: x[1],
            reverse=True
        )[1: top_k + 1]

        data = []
        for i in similar_items:
            temp_df = books[books['Book-Title'] == pt.index[i[0]]]
            title = temp_df.drop_duplicates('Book-Title')['Book-Title'].values
            author = temp_df.drop_duplicates('Book-Title')['Book-Author'].values
            img = temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values
            item = [
                title[0] if len(title) else "",
                author[0] if len(author) else "",
                img[0] if len(img) else "",
            ]
            data.append(item)
        return data
    except Exception:
        return []

# ---------------------------
# UI
# ---------------------------
st.markdown('<h1 class="main-header">📚 BookVault Recommender</h1>', unsafe_allow_html=True)
st.markdown("Discover your next favorite book with a tidy, fast UI built on your existing logic.")

# Sidebar
with st.sidebar:
    st.markdown('<h2 style="color:#fff;margin:0 0 8px">BookVault</h2>', unsafe_allow_html=True)

    st.image(
        "https://www.publicdomainpictures.net/pictures/210000/velka/old-books-vintage-background.jpg",
        width=500
    )

    st.markdown('<h3 style="color:#fff;margin:12px 0 6px">Navigation</h3>', unsafe_allow_html=True)
    page = st.radio("Go to", ["Popular Books", "Personalized Recommendations"], index=0)

    st.markdown(
        '<hr style="border:none;height:1px;background:rgba(255,255,255,.25);margin:12px 0" />',
        unsafe_allow_html=True
    )

    st.markdown('<h3 style="color:#fff;margin:0 0 6px">About</h3>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#fff;opacity:.9">'
        'BookVault blends popularity and collaborative filtering. '
        'Pick a book you enjoyed to see similar titles.'
        '</div>',
        unsafe_allow_html=True
    )


# ---------------------------
# Popular Books
# ---------------------------
if page == "Popular Books":
    st.markdown('<h2 class="sub-header">📈 Most Popular Books</h2>', unsafe_allow_html=True)
    st.caption("Highest-rated and most-reviewed titles in the catalog.")
    if isinstance(popular_df, pd.DataFrame) and not popular_df.empty:
        cols = st.columns(4)
        for idx, (_, row) in enumerate(popular_df.head(12).iterrows()):
            with cols[idx % 4]:
                st.markdown('<div class="book-card">', unsafe_allow_html=True)

                img = _resolve_cover_from_row(row.to_dict())
                st.markdown(cover_html(img), unsafe_allow_html=True)  # HTML renderer (no yellow warnings)

                st.markdown(f'<div class="book-title">{row.get("Book-Title","")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="book-author">by {row.get("Book-Author","")}</div>', unsafe_allow_html=True)

                badges = []
                if 'avg_rating' in row and pd.notna(row['avg_rating']):
                    badges.append(f'<span class="rating-badge">⭐ {float(row["avg_rating"]):.1f}</span>')
                if 'num_rating' in row and pd.notna(row['num_rating']):
                    badges.append(f'<span class="rating-count">{int(row["num_rating"])} ratings</span>')
                if badges:
                    st.markdown(" ".join(badges), unsafe_allow_html=True)

                if 'Year-Of-Publication' in row and pd.notna(row['Year-Of-Publication']):
                    st.caption(f"Published: {int(row['Year-Of-Publication'])}")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No popular books data found (Popular.pkl).")

# ---------------------------
# Personalized Recommendations
# ---------------------------
else:
    st.markdown('<h2 class="sub-header">🎯 Personalized Recommendations</h2>', unsafe_allow_html=True)
    st.caption("Choose a book you enjoyed and we’ll suggest similar ones.")

    options = list(pt.index) if hasattr(pt, "index") else []
    if not options:
        st.warning("Your pivot table has no index to select from.")
        st.stop()

    selected_book = st.selectbox("Select a book you enjoyed:", options)

    k = st.slider("How many recommendations?", 3, 12, 6, 1)
    go = st.button("Get Recommendations")

    if go:
        with st.spinner("Finding the perfect books for you..."):
            recs = recommend(selected_book, top_k=k)

        if recs:
            cols = st.columns(4)
            for i, (title, author, img_url) in enumerate(recs):
                with cols[i % 4]:
                    st.markdown('<div class="book-card">', unsafe_allow_html=True)

                    raw_img = _resolve_cover_from_title(title)
                    if raw_img is None:
                        raw_img = _fetch_image(img_url)
                    st.markdown(cover_html(raw_img), unsafe_allow_html=True)

                    st.markdown(f'<div class="book-title">{title}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="book-author">by {author}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            st.success("Done.")
        else:
            st.warning("No recommendations for that title. Try another selection.")
