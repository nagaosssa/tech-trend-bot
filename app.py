import streamlit as st
import os
from dotenv import load_dotenv
from api_client import PerplexityClient

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Perplexity Consultant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

try:
    local_css("styles.css")
except FileNotFoundError:
    pass # Handle case where styles might not be ready yet

# Title and Header
st.title("🧠 Perplexity Strategic Consultant")
st.markdown("### Elevate your productivity with AI-driven search and tool recommendations.")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input("Perplexity API Key", type="password", value=os.getenv("PERPLEXITY_API_KEY") or "")
    if api_key_input and not os.getenv("PERPLEXITY_API_KEY"):
         os.environ["PERPLEXITY_API_KEY"] = api_key_input
         
    st.divider()
    st.info("Input your goal, and we will generate optimized search queries and tool recommendations.")

# Main Input
user_goal = st.text_area("What do you want to achieve?", height=100, placeholder="e.g., I want to automate my daily Instagram posts with AI...")
submit_btn = st.button("Generate Proposals")

if submit_btn:
    if not user_goal:
        st.warning("Please enter a goal.")
    elif not api_key_input:
        st.error("Please provide a Perplexity API Key in the sidebar or .env file.")
    else:
        with st.spinner("Analyzing your request with Perplexity Sonar Pro..."):
            try:
                client = PerplexityClient(api_key=api_key_input)
                result = client.get_proposals(user_goal)
                
                if "error" in result:
                    st.error(f"API Error: {result['error']}")
                else:
                    # Summary Section
                    st.success("Analysis Complete!")
                    st.markdown(f"### 💡 Strategic Advice\n{result.get('summary_advice', 'No summary provided.')}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 🔍 Recommended Search Queries")
                        for item in result.get("search_queries", []):
                            with st.expander(f"**{item['query']}**", expanded=True):
                                st.write(item.get("reason", ""))
                                st.markdown(f"[Search on Google](https://www.google.com/search?q={item['query'].replace(' ', '+')})")
                    
                    with col2:
                        st.markdown("### 🛠 Recommended Tools & Services")
                        for item in result.get("recommendations", []):
                            container = st.container()
                            container.markdown(
                                f"""
                                <div class="recommendation-card">
                                    <h4>{item['name']} <span style="font-size:0.8em; color:#888;">({item['type']})</span></h4>
                                    <p>{item['description']}</p>
                                    <p style="color:#238636; font-size:0.9em;"><em>Why: {item['reason']}</em></p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

