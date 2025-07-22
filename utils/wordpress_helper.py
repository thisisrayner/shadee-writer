# Version 1.0.0:
# - Initial implementation for creating draft posts in WordPress.

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
        # The endpoint for creating posts
        api_url = f"{wp_url}/wp-json/wp/v2/posts"
        
        # Prepare the authentication using the Application Password
        credentials = f"{wp_user}:{wp_pass}"
        token = base64.b64encode(credentials.encode())
        headers = {'Authorization': f'Basic {token.decode("utf-8")}'}
        
        # Prepare the post data
        post_data = {
            'title': title,
            'content': content,
            'status': 'draft'  # This is crucial for creating a draft
        }

        # --- Make the API Call ---
        response = requests.post(api_url, headers=headers, json=post_data)

        # --- Check the Response ---
        if response.status_code == 201: # 201 means "Created" successfully
            post_id = response.json().get('id')
            post_link = response.json().get('link')
            st.success(f"Successfully created draft post: '{title}' in WordPress!")
            st.markdown(f"**[Edit your new draft here]({post_link})**")
            return True
        else:
            # Provide a detailed error message if it fails
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
