# Book-Recommendation-System
BookVault is a **Book Recommendation System** that suggests books to users based on collaborative filtering and popularity.   The project includes both a **Jupyter Notebook (EDA + Model Building)** and an interactive **Streamlit Web App** for book recommendations.  
#  Business Problem
With the vast number of books available online, readers often struggle to find their next read.  
This system aims to:  
1. Recommend books similar to the ones users enjoyed (personalized recommendations).  
2. Highlight trending/popular books based on ratings and reviews.  

---

##  Project Structure
├── app.py # Streamlit app
├── book_recomm_Sys.ipynb # Jupyter Notebook (EDA + recommender logic)
├── books.pkl # Metadata of books
├── pt.pkl # Pivot table of user-book interactions
├── similarity_scores.pkl # Precomputed similarity matrix
├── Popular.pkl # Preprocessed popular books
├── requirements.txt # Dependencies

## 🔍 Data Description
Dataset used is the **Book-Crossing dataset**, containing:  
- **Book-Title** – Title of the book  
- **Book-Author** – Author of the book  
- **ISBN** – Unique identifier  
- **Image-URL-S/M/L** – Book cover images  
- **Ratings** – User ratings of books  

---

## 🛠️ Methodology
1. **Data Cleaning**  
   - Removed duplicate/missing values  
   - Standardized author names & titles  

2. **Exploratory Data Analysis (EDA)**  
   - Most popular authors and books  
   - Ratings distribution  

3. **Recommendation System**  
   - **Popularity-based filtering** – books with highest ratings/reviews  
   - **Collaborative filtering** – similarity matrix (cosine similarity) built on user-item interactions  

4. **Web App Development**  
   - Built with **Streamlit** for interactivity  
   - Book covers fetched dynamically from URLs/OpenLibrary API  
   - Clean UI with hover effects & two tabs: *Popular Books* and *Personalized Recommendations*  

---

## 📊 Features in Web App
- **Popular Books**  
  - Displays trending books with ratings & reviews  
- **Personalized Recommendations**  
  - User selects a book → App suggests similar titles  
- **Hover & UI Enhancements**  
  - Smooth hover effects on book covers  
  - Clean, modern interface  
