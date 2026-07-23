import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Web Scraper", page_icon="📰", layout="wide")
st.title("📰 Automated web scraper for news articles")

st.subheader("Add a new article")
with st.container():
    url_input = st.text_input("Enter the URL of the news article here:")
    if st.button("Execute"):
        if url_input:
            with st.spinner('Processing the news article...'):
                try:
                    resp = requests.post(f"{API_URL}/scrape", params={"url": url_input})
                    if resp.status_code == 200:
                        res_data = resp.json()
                        if res_data.get("status") == "duplicate":
                            st.warning("This news article has already been processed and exists in the database.")
                        else:
                            st.success("The news article has been added to the database!")
                            time.sleep(2)
                            st.rerun() # update interface after adding a new article
                    else:
                        st.error("Error occurred while scraping.")
                except Exception as e:
                    st.error(f"Unable to contact the server: {e}")
        else:
            st.warning("Enter a valid URL.")

st.subheader("News articles saved in the database")

try:
    response = requests.get(f"{API_URL}/news")
    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            st.session_state['news_df'] = df
        else:
            st.session_state['news_df'] = pd.DataFrame()
    else:
        st.error("Failed to retrieve news articles.")
except Exception as e:
    st.error(f"Unable to contact the server: {e}")

if 'news_df' in st.session_state and not st.session_state['news_df'].empty:
    df = st.session_state['news_df']
    
    search_query = st.text_input("Find news articles by ID, title, author or source:")
    if search_query:
        query = search_query.lower()
        filtered_df = df[
            df['id'].astype(str).str.lower().str.contains(query, na=False) |
            df['title'].str.lower().str.contains(query, na=False) |
            df['author'].str.lower().str.contains(query, na=False) |
            df['source'].str.lower().str.contains(query, na=False)
        ]
    else:
        filtered_df = df

    if 'publishedAt' in filtered_df.columns:
        filtered_df['publishedAt'] = pd.to_datetime(filtered_df['publishedAt']).dt.strftime('%d.%m.%Y, %H:%M:%S')
    
    st.dataframe(filtered_df[['id', 'source', 'author', 'title', 'category', 'description', 'url', 'urlToImage', 'publishedAt', 'content']])
else:
    st.info("No news articles available in the database.")

st.divider()
st.subheader("Manage Database")

col1, col2 = st.columns(2)

with col1:
    st.write("### Delete news article by ID")
    article_id_to_delete = st.text_input("Enter the ID of the article to delete:")
    if st.button("Delete article"):
        if article_id_to_delete:
            try:
                resp = requests.delete(f"{API_URL}/news/{article_id_to_delete}")
                if resp.status_code == 200:
                    st.success(f"Article with ID {article_id_to_delete} has been deleted successfully!")
                    st.rerun() # update interface after deletion
                elif resp.status_code == 404:
                    st.error("Article not found in the database.")
                else:
                    st.error("Article not found or an error occurred.")
            except Exception as e:
                st.error(f"Unable to contact the server: {e}")
        else:
            st.warning("Please enter a valid article ID.")

with col2:
    st.write("### Delete all news articles")
    st.warning("Warning! This action will clear the entire database.")
    confirm_delete_all = st.checkbox("Confirm that I want to delete all articles")
    if st.button("Delete all articles"):
        if confirm_delete_all:
            try:
                resp = requests.delete(f"{API_URL}/news")
                if resp.status_code == 200:
                    st.success("All news articles have been deleted from the database.")
                    if 'news_df' in st.session_state:
                        del st.session_state['news_df']
                    st.rerun() # update interface after deletion
                else:
                    st.error("Error occurred while deleting articles.")
            except Exception as e:
                st.error(f"Unable to contact the server: {e}")
        else:
            st.warning("Please check the confirmation box to delete all articles.")

# pornire interfata Streamlit: streamlit run app.py