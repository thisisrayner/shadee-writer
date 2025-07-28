# DEBUGGING app.py - DO NOT LEAVE IN PRODUCTION
import streamlit as st

st.set_page_config(page_title="Secrets Debugger", layout="wide")
st.title("🕵️ Streamlit Secrets Debugger")

st.info("This app will show you exactly what Streamlit is reading from your secrets.")

st.header("Full `st.secrets` Object")
st.write("Below is the entire secrets object. You can expand it to see the structure.")
st.write(st.secrets)

st.header("Checking for `[authentication]` section")
try:
    auth_section = st.secrets["authentication"]
    st.success("✅ Found the `[authentication]` section.")
    st.json(auth_section.to_dict()) # Use .to_dict() to show it nicely
except Exception as e:
    st.error(f"❌ Could not find or access the `[authentication]` section. Error: {e}")

st.header("Checking for the `users` list inside `[authentication]`")
try:
    users_list = st.secrets["authentication"]["users"]
    st.success("✅ Found the `users` key inside the `[authentication]` section.")
    
    st.write(f"**Type of `users` object is:** `{type(users_list)}`")
    
    if isinstance(users_list, list):
        st.success("✅ The `users` object is correctly configured as a LIST.")
        st.write("**Contents:**")
        st.json(users_list)
    else:
        st.error(f"❌ **CRITICAL ERROR:** The `users` object is a `{type(users_list)}`, but the code expects a LIST. This is likely caused by using `[users]` instead of `[[users]]` in your secrets.")

except Exception as e:
    st.error(f"❌ Could not find or access the `users` key. Error: {e}")

# End of app.py
