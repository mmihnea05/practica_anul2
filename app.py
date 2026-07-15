import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Web Scraper", layout="wide")
st.title("📰 Automated web scraper for news articles")

st.subheader("Add a new article")
with st.container():
    url_input = st.text_input("Enter the URL of the news article here:")
    if st.button("Execute"):
        if url_input:
            with st.spinner('Processing the news article...'):
                try:
                    # apel endpoint scrape din main.py
                    resp = requests.post(f"{API_URL}/scrape", params={"url": url_input})
                    if resp.status_code == 200:
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
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df[['source', 'title', 'category', 'publishedAt']])
        else:
            st.info("No news articles available in the database.")
    except Exception as e:
        st.error("Failed to retrieve news articles.")