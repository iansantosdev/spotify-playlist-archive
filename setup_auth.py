#!/usr/bin/env python3
"""
Spotify Authentication Setup Script

This script helps you obtain the necessary authentication tokens for the
Spotify Playlist Archiver. Run this script locally to get your refresh token.
"""

import os
import sys
from urllib.parse import urlparse, parse_qs
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser

def get_spotify_credentials():
    """Get Spotify credentials from user input or environment."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

    if not client_id:
        client_id = input("Enter your Spotify Client ID: ").strip()

    if not client_secret:
        client_secret = input("Enter your Spotify Client Secret: ").strip()

    if not client_id or not client_secret:
        print("❌ Client ID and Client Secret are required!")
        sys.exit(1)

    return client_id, client_secret

def setup_spotify_auth():
    """Set up Spotify authentication and get refresh token."""
    print("🎵 Spotify Playlist Archiver - Authentication Setup")
    print("=" * 50)

    # Get credentials
    client_id, client_secret = get_spotify_credentials()

    # Set up OAuth
    redirect_uri = "http://localhost:8080/callback"
    scope = "playlist-read-private playlist-modify-public playlist-modify-private"

    print(f"\n📝 Setting up OAuth with:")
    print(f"   Client ID: {client_id[:8]}...")
    print(f"   Redirect URI: {redirect_uri}")
    print(f"   Scope: {scope}")

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        cache_path=".spotify_cache"
    )

    # Get authorization URL
    auth_url = auth_manager.get_authorize_url()

    print(f"\n🌐 Opening authorization URL in your browser...")
    print(f"   URL: {auth_url}")

    # Try to open browser automatically
    try:
        webbrowser.open(auth_url)
        print("   ✅ Browser opened automatically")
    except:
        print("   ⚠️  Could not open browser automatically")
        print("   Please manually open the URL above in your browser")

    print("\n📋 Instructions:")
    print("1. Log in to Spotify in the opened browser window")
    print("2. Grant permissions to the app")
    print("3. You'll be redirected to a localhost URL that won't load (this is normal)")
    print("4. Copy the ENTIRE redirect URL from your browser's address bar")
    print("5. Paste it below")

    # Get the redirect URL from user
    redirect_response = input("\n🔗 Paste the full redirect URL here: ").strip()

    if not redirect_response.startswith("http://localhost:8080/callback"):
        print("❌ Invalid redirect URL. Make sure you copied the complete URL.")
        sys.exit(1)

    # Extract authorization code
    try:
        parsed_url = urlparse(redirect_response)
        query_params = parse_qs(parsed_url.query)
        auth_code = query_params.get('code', [None])[0]

        if not auth_code:
            print("❌ No authorization code found in URL")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error parsing redirect URL: {e}")
        sys.exit(1)

    # Exchange code for tokens
    try:
        print("\n🔄 Exchanging authorization code for tokens...")
        token_info = auth_manager.get_access_token(auth_code)

        if not token_info:
            print("❌ Failed to get access token")
            sys.exit(1)

        access_token = token_info['access_token']
        refresh_token = token_info['refresh_token']

        print("✅ Successfully obtained tokens!")

    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        sys.exit(1)

    # Test the tokens
    try:
        print("\n🧪 Testing authentication...")
        sp = spotipy.Spotify(auth_manager=auth_manager)
        user_info = sp.current_user()

        print(f"✅ Authentication successful!")
        print(f"   Logged in as: {user_info['display_name']} ({user_info['id']})")

    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        sys.exit(1)

    # Display results
    print("\n" + "=" * 50)
    print("🎉 SETUP COMPLETE!")
    print("=" * 50)
    print("\n📝 Add these secrets to your GitHub repository:")
    print("   Go to: Settings > Secrets and variables > Actions\n")

    print("🔑 Required GitHub Secrets:")
    print(f"   SPOTIFY_CLIENT_ID = {client_id}")
    print(f"   SPOTIFY_CLIENT_SECRET = {client_secret}")
    print(f"   SPOTIFY_REFRESH_TOKEN = {refresh_token}")

    print(f"\n🎵 Your Spotify User ID: {user_info['id']}")

    # Get playlist ID
    print("\n📋 Optional: Set up your playlist ID")
    playlist_url = input("Enter your Spotify playlist URL (or press Enter to skip): ").strip()

    if playlist_url:
        try:
            # Extract playlist ID from URL
            if "playlist/" in playlist_url:
                playlist_id = playlist_url.split("playlist/")[1].split("?")[0]
                print(f"\n📝 Additional GitHub Secret:")
                print(f"   SPOTIFY_PLAYLIST_ID = {playlist_id}")

                # Test playlist access
                try:
                    playlist = sp.playlist(playlist_id)
                    print(f"✅ Playlist found: '{playlist['name']}' ({playlist['tracks']['total']} tracks)")
                except Exception as e:
                    print(f"⚠️  Warning: Could not access playlist: {e}")
            else:
                print("⚠️  Invalid playlist URL format")
        except Exception as e:
            print(f"⚠️  Error processing playlist URL: {e}")

    print("\n🚀 Next steps:")
    print("1. Add the secrets to your GitHub repository")
    print("2. Set SPOTIFY_PLAYLIST_ID if you haven't already")
    print("3. The GitHub Action will run daily at 9:00 AM UTC")
    print("4. You can also trigger it manually from the Actions tab")

    # Clean up
    try:
        os.remove(".spotify_cache")
    except:
        pass

if __name__ == "__main__":
    setup_spotify_auth()
