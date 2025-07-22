# Version 1.1.0:
# - Updated to handle 202 "Accepted" as a valid success status code from WordPress.
# - Improved error parsing for non-JSON responses (like firewall HTML).
# Previous versions:
# - Version 1.0.0: Initial implementation for creating draft posts.

"""
Module: wordpress_helper.py
Purpose: Handles all interactions with the WordPress REST API to create posts.
"""

# --- Imports ---
import streamlit as st
import requests
import base64

def create_wordpress_draft(title, content):
    """
    Creates a new post in WordPress with the status set to 'draft'.

    Args:
        title (str): The title of the post.
        content (str): The HTML or plain text content of the post.

    Returns:
        bool: True if the post was created successfully, False otherwise.
    """
    try:
        # --- Get Credentials from Secrets ---
        wp_url = st.secrets["wordpress"]["WP_URL"]
        wp_user = st.secrets["wordpress"]["WP_USERNAME"]
        wp_pass = st.secrets["wordpress"]["WP_APP_PASSWORD"]

        # --- Prepare the Request ---
        api_url = f"{wp_url}/wp-json/wp/v2/posts"
        credentials = f"{wp_user}:{wp_pass}"
        token = base64.b64encode(credentials.encode())
        headers = {'Authorization': f'Basic {token.decode("utf-8")}'}
        
        post_data = {
            'title': title,
            'content': content,
            'status': 'draft'
        }

        # --- Make the API Call ---
        response = requests.post(api_url, headers=headers, json=post_data)

        # --- Check the Response ---
        # Check for success codes 201 (Created) or 202 (Accepted)
        if response.status_code in [201, 202]:
            try:
                # Try to parse the expected JSON response
                response_data = response.json()
                post_link = response_data.get('link')
                st.success(f"Successfully created draft post: '{title}' in WordPress!")
                if post_link:
                    st.markdown(f"**[Edit your new draft here]({post_link})**")
                return True
            except requests.exceptions.JSONDecodeError:
                # This happens if we get a success code but the body is HTML (like a firewall page)
                st.error("WordPress accepted the request, but returned an unexpected response (likely a firewall or CAPTCHA page). Please check your hosting's IP whitelist settings.")
                st.code(response.text, language="html")
                return False
        else:
            # Handle other, explicit error codes
            st.error(f"Failed to create WordPress draft. Status Code: {response.status_code}")
            try:
                st.error(f"Response: {response.json()}")
            except Exception:
                st.error(f"Could not parse error response: {response.text}")
            return False

    except KeyError as e:
        st.error(f"Missing WordPress credentials in secrets.toml: {e}")
        st.info("Please ensure your .streamlit/secrets.toml file contains a [wordpress] section with WP_URL, WP_USERNAME, and WP_APP_PASSWORD.")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred while sending to WordPress: {e}")
        return False

# End of wordpress_helper.py
