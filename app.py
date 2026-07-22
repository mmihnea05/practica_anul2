import streamlit as st
import requests
import pandas as pd

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
                    else:
                        st.error("Error occurred while scraping.")
                except Exception as e:
                    st.error(f"Unable to contact the server: {e}")
        else:
            st.warning("Enter a valid URL.")

st.subheader("News articles saved in the database")
if st.button("Refresh the list"):
    try:
        data = requests.get(f"{API_URL}/news").json()
        # formatare coloana publishedAt
        if data:
            df = pd.DataFrame(data)
            if 'publishedAt' in df.columns:
                df['publishedAt'] = pd.to_datetime(df['publishedAt']).dt.strftime('%d.%m.%Y, %H:%M:%S')
           
            st.dataframe(df[['id', 'source', 'author', 'title', 'category', 'description', 'url', 'urlToImage', 'publishedAt', 'content']])
        else:
            st.info("No news articles available in the database.")
    except Exception as e:
        st.error("Failed to retrieve news articles.")

st.divider()
st.subheader("Manage Database")

col1, col2 = st.columns(2)

with col1:
    st.write("### Delete news article by ID")
    article_id_to_delete = st.text_input("Enter the ID of the article to delete:")
    if st.button("Delete article"):
        try:
            resp = requests.delete(f"{API_URL}/news/{article_id_to_delete}")
            if resp.status_code == 200:
                st.success(f"Article with ID {article_id_to_delete} has been deleted successfully!")
            else:
                st.error("Article not found or an error occurred.")
        except Exception as e:
            st.error(f"Unable to contact the server: {e}")

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
                else:
                    st.error("Error occurred while deleting articles.")
            except Exception as e:
                st.error(f"Unable to contact the server: {e}")
        else:
            st.warning("Please check the confirmation box to delete all articles.")

# pornire interfata Streamlit: streamlit run app.py