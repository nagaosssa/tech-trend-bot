import streamlit as st
import json
import os
import subprocess
import sys

# Page Config
st.set_page_config(
    page_title="Bot Control Panel",
    page_icon="🧠",
    layout="wide"
)

# Constants
KNOWN_TOOLS_FILE = "known_tools.json"
CONFIG_FILE = "bot_config.json"

# Load Styles
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    .stButton > button {
        background-color: #238636;
        color: white;
        width: 100%;
    }
    .stTextInput > div > div > input {
        background-color: #0d1117;
        color: white;
    }
    div[data-testid="stExpander"] {
        background-color: #161b22;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def load_tools():
    try:
        with open(KNOWN_TOOLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("known_tools", [])
    except FileNotFoundError:
        return []

def save_tools(tools):
    with open(KNOWN_TOOLS_FILE, "w", encoding="utf-8") as f:
        json.dump({"known_tools": tools}, f, indent=4, ensure_ascii=False)

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "search_category": "Dev Tools, PKM, Privacy Browsers, & Student Deals",
            "target_languages": "TypeScript, PHP, AWS, Rust, Go",
            "excluded_keywords": ""
        }

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def run_bot():
    try:
        # Run bot.py in a subprocess
        result = subprocess.run([sys.executable, "bot.py"], capture_output=True, text=True, encoding="utf-8")
        return result.stdout, result.stderr
    except Exception as e:
        return None, str(e)

# --- UI Layout ---

st.title("🧠 Tech Trend Bot Dashboard")

col1, col2 = st.columns([2, 1])

# Left Column: Manage Tools
with col1:
    st.subheader("🛠️ My Stack (Known Tools)")
    st.caption("Here are the tools you already know. The bot will NOT recommend these as new trends, but may suggest plugins for them.")
    
    tools = load_tools()
    
    # Add New Tool
    with st.form("add_tool_form", clear_on_submit=True):
        new_tool = st.text_input("Add a tool you use (e.g. 'VS Code')")
        submitted = st.form_submit_button("Add to List")
        if submitted and new_tool:
            if new_tool not in tools:
                tools.append(new_tool)
                save_tools(tools)
                st.success(f"Added '{new_tool}'")
                st.rerun()
            else:
                st.warning("Tool already exists.")

    # List Tools
    if tools:
        st.write(f"**Current List ({len(tools)} items)**")
        # Display as pills/tags with delete option
        for i, tool in enumerate(tools):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.code(tool)
            with c2:
                if st.button("🗑️", key=f"del_{i}"):
                    tools.pop(i)
                    save_tools(tools)
                    st.rerun()
    else:
        st.info("No tools registered yet.")

# Right Column: Bot Controls
with col2:
    st.subheader("🤖 Bot Operations")
    
    st.markdown("### Manual Run")
    st.caption("Trigger the bot immediately to check for trends and send a notification.")
    
    if st.button("🚀 Run Bot Now"):
        with st.spinner("Scouting tech trends..."):
            stdout, stderr = run_bot()
            if stderr:
                st.error("Error occurred:")
                st.code(stderr)
            else:
                st.success("Analysis Complete!")
                # Show part of the log
                st.text_area("Bot Logs", stdout, height=300)

    st.divider()
    
    st.divider()
    
    st.markdown("### ⚙️ Search Configuration")
    config = load_config()
    
    with st.form("config_form"):
        new_category = st.text_area("Search Category / Context", value=config.get("search_category", ""))
        new_targets = st.text_input("Target Languages / Techs (comma separated)", value=config.get("target_languages", ""))
        new_excluded = st.text_input("Excluded Keywords (comma separated)", value=config.get("excluded_keywords", ""))
        
        if st.form_submit_button("Save Configuration"):
            config["search_category"] = new_category
            config["target_languages"] = new_targets
            config["excluded_keywords"] = new_excluded
            save_config(config)
            st.success("Configuration saved!")
            st.rerun()

    st.caption(f"Config File: `{CONFIG_FILE}`")

