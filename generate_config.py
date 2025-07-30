#!/usr/bin/env python3
"""
Playlist Configuration Generator

This utility script helps users generate the JSON configuration for multiple
playlists by interactively collecting playlist information and testing access.

Usage:
    python generate_config.py

The script will:
1. Authenticate with Spotify
2. Allow you to search for playlists or enter playlist URLs/IDs
3. Test access to each playlist
4. Generate the JSON configuration
5. Save it to a file or display for copying to GitHub secrets
"""

import os
import sys
import json
import re
from typing import List, Dict, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

class PlaylistConfigGenerator:
    def __init__(self):
        """Initialize the Spotify client."""
        load_dotenv()
        self.sp = self._authenticate()
        self.user_id = self._get_current_user_id()
        self.configs = []

    def _authenticate(self) -> spotipy.Spotify:
        """Authenticate with Spotify using OAuth."""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8080/callback')

        if not client_id or not client_secret:
            print("❌ SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in environment or .env file")
            print("   Run 'python setup_auth.py' first to get your credentials")
            sys.exit(1)

        scope = "playlist-read-private playlist-modify-public playlist-modify-private"

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache_config"
        )

        return spotipy.Spotify(auth_manager=auth_manager)

    def _get_current_user_id(self) -> str:
        """Get the current user's Spotify ID."""
        try:
            user_info = self.sp.current_user()
            return user_info['id']
        except Exception as e:
            print(f"❌ Failed to get current user: {e}")
            sys.exit(1)

    def extract_playlist_id(self, input_str: str) -> Optional[str]:
        """Extract playlist ID from URL or return if already an ID."""
        input_str = input_str.strip()

        # If it's already a playlist ID (22 character alphanumeric string)
        if re.match(r'^[a-zA-Z0-9]{22}$', input_str):
            return input_str

        # Extract from Spotify URL
        url_patterns = [
            r'spotify\.com/playlist/([a-zA-Z0-9]{22})',
            r'spotify:playlist:([a-zA-Z0-9]{22})'
        ]

        for pattern in url_patterns:
            match = re.search(pattern, input_str)
            if match:
                return match.group(1)

        return None

    def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        """Get playlist information and verify access."""
        try:
            playlist = self.sp.playlist(playlist_id)
            return {
                'id': playlist_id,
                'name': playlist['name'],
                'owner': playlist['owner']['display_name'],
                'track_count': playlist['tracks']['total'],
                'public': playlist['public'],
                'description': playlist.get('description', '')
            }
        except Exception as e:
            print(f"❌ Failed to access playlist {playlist_id}: {e}")
            return None

    def search_playlists(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for playlists by name."""
        try:
            results = self.sp.search(q=query, type='playlist', limit=limit)
            playlists = []

            for playlist in results['playlists']['items']:
                playlists.append({
                    'id': playlist['id'],
                    'name': playlist['name'],
                    'owner': playlist['owner']['display_name'],
                    'track_count': playlist['tracks']['total'],
                    'public': playlist['public']
                })

            return playlists
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

    def show_user_playlists(self, limit: int = 20) -> List[Dict]:
        """Show user's own playlists."""
        try:
            playlists = []
            results = self.sp.current_user_playlists(limit=limit)

            for playlist in results['items']:
                if playlist['owner']['id'] == self.user_id:
                    playlists.append({
                        'id': playlist['id'],
                        'name': playlist['name'],
                        'owner': playlist['owner']['display_name'],
                        'track_count': playlist['tracks']['total'],
                        'public': playlist['public']
                    })

            return playlists
        except Exception as e:
            print(f"❌ Failed to get user playlists: {e}")
            return []

    def add_playlist_interactive(self) -> bool:
        """Interactive playlist addition."""
        print(f"\n📝 Add Playlist {len(self.configs) + 1}")
        print("=" * 40)

        while True:
            print("\nChoose an option:")
            print("1. Enter playlist URL or ID")
            print("2. Search for playlists")
            print("3. Show my playlists")
            print("4. Skip this playlist")

            choice = input("Enter choice (1-4): ").strip()

            if choice == '1':
                return self._add_by_url()
            elif choice == '2':
                return self._add_by_search()
            elif choice == '3':
                return self._add_from_user_playlists()
            elif choice == '4':
                return False
            else:
                print("❌ Invalid choice. Please enter 1-4.")

    def _add_by_url(self) -> bool:
        """Add playlist by URL or ID."""
        url_or_id = input("\nEnter Spotify playlist URL or ID: ").strip()

        if not url_or_id:
            return False

        playlist_id = self.extract_playlist_id(url_or_id)
        if not playlist_id:
            print("❌ Invalid playlist URL or ID format")
            return False

        return self._confirm_and_add_playlist(playlist_id)

    def _add_by_search(self) -> bool:
        """Add playlist by searching."""
        query = input("\nEnter search term: ").strip()

        if not query:
            return False

        print(f"🔍 Searching for '{query}'...")
        playlists = self.search_playlists(query)

        if not playlists:
            print("❌ No playlists found")
            return False

        return self._select_from_list(playlists)

    def _add_from_user_playlists(self) -> bool:
        """Add from user's own playlists."""
        print(f"\n📋 Your playlists:")
        playlists = self.show_user_playlists()

        if not playlists:
            print("❌ No playlists found")
            return False

        return self._select_from_list(playlists)

    def _select_from_list(self, playlists: List[Dict]) -> bool:
        """Select playlist from a list."""
        print(f"\nFound {len(playlists)} playlist(s):")

        for i, playlist in enumerate(playlists, 1):
            print(f"{i:2d}. {playlist['name']}")
            print(f"     By: {playlist['owner']} | Tracks: {playlist['track_count']} | {'Public' if playlist['public'] else 'Private'}")

        while True:
            try:
                choice = input(f"\nSelect playlist (1-{len(playlists)}) or 0 to cancel: ").strip()

                if choice == '0':
                    return False

                index = int(choice) - 1
                if 0 <= index < len(playlists):
                    selected_playlist = playlists[index]
                    return self._confirm_and_add_playlist(selected_playlist['id'])
                else:
                    print(f"❌ Please enter a number between 1 and {len(playlists)}")

            except ValueError:
                print("❌ Please enter a valid number")

    def _confirm_and_add_playlist(self, playlist_id: str) -> bool:
        """Confirm and add playlist to configuration."""
        # Get playlist info
        playlist_info = self.get_playlist_info(playlist_id)
        if not playlist_info:
            return False

        print(f"\n✅ Playlist found:")
        print(f"   Name: {playlist_info['name']}")
        print(f"   Owner: {playlist_info['owner']}")
        print(f"   Tracks: {playlist_info['track_count']}")
        print(f"   Status: {'Public' if playlist_info['public'] else 'Private'}")

        # Check if already added
        if any(config['playlist_id'] == playlist_id for config in self.configs):
            print("⚠️  This playlist is already in your configuration")
            return False

        # Get custom name
        print(f"\n📝 Archive naming:")
        print(f"   Default: '{playlist_info['name']} (Cumulative)'")
        custom_name = input("   Enter custom archive name prefix (or press Enter for default): ").strip()

        if not custom_name:
            custom_name = None
        else:
            print(f"   Custom: '{custom_name} (Cumulative)'")

        # Confirm addition
        confirm = input(f"\nAdd this playlist to configuration? (Y/n): ").strip().lower()
        if confirm in ['', 'y', 'yes']:
            config = {
                'playlist_id': playlist_id,
                'custom_name': custom_name
            }
            self.configs.append(config)
            print(f"✅ Added: {playlist_info['name']}")
            return True

        return False

    def review_and_save_config(self):
        """Review configuration and save."""
        if not self.configs:
            print("\n❌ No playlists configured!")
            return

        print(f"\n📋 Configuration Review ({len(self.configs)} playlists):")
        print("=" * 50)

        for i, config in enumerate(self.configs, 1):
            playlist_info = self.get_playlist_info(config['playlist_id'])
            if playlist_info:
                archive_name = f"{config['custom_name'] or playlist_info['name']} (Cumulative)"
                print(f"{i}. {playlist_info['name']}")
                print(f"   ID: {config['playlist_id']}")
                print(f"   Archive name: {archive_name}")
                print(f"   Tracks: {playlist_info['track_count']}")

        print(f"\n🔧 Generated JSON Configuration:")
        json_config = json.dumps(self.configs, indent=2)
        print(json_config)

        # Ask where to save
        print(f"\n💾 Save options:")
        print("1. Save to playlists_config.json file")
        print("2. Display for GitHub Secrets (copy-paste)")
        print("3. Save to custom file")
        print("4. Don't save")

        choice = input("Choose option (1-4): ").strip()

        if choice == '1':
            self._save_to_file('playlists_config.json', json_config)
        elif choice == '2':
            self._display_for_github_secrets(json_config)
        elif choice == '3':
            filename = input("Enter filename: ").strip()
            if filename:
                self._save_to_file(filename, json_config)
        elif choice == '4':
            print("💾 Configuration not saved")
        else:
            print("❌ Invalid choice, configuration not saved")

    def _save_to_file(self, filename: str, json_config: str):
        """Save configuration to file."""
        try:
            with open(filename, 'w') as f:
                f.write(json_config)
            print(f"✅ Configuration saved to {filename}")
            print(f"\n📝 To use in GitHub Actions:")
            print(f"   1. Copy the contents of {filename}")
            print(f"   2. Add as SPOTIFY_PLAYLISTS_CONFIG secret in GitHub")
        except Exception as e:
            print(f"❌ Failed to save to {filename}: {e}")

    def _display_for_github_secrets(self, json_config: str):
        """Display configuration for GitHub Secrets."""
        print(f"\n🔐 GitHub Secret Configuration:")
        print("=" * 50)
        print("Secret Name: SPOTIFY_PLAYLISTS_CONFIG")
        print("Secret Value (copy everything below this line):")
        print("-" * 50)
        print(json_config)
        print("-" * 50)
        print("\n📝 Instructions:")
        print("1. Go to your GitHub repository")
        print("2. Go to Settings > Secrets and variables > Actions")
        print("3. Click 'New repository secret'")
        print("4. Name: SPOTIFY_PLAYLISTS_CONFIG")
        print("5. Value: Copy the JSON above (including the square brackets)")

    def run(self):
        """Run the interactive configuration generator."""
        print("🎵 Spotify Playlist Archiver - Configuration Generator")
        print("=" * 55)
        print(f"👤 Logged in as: {self.user_id}")

        print(f"\nThis tool will help you create a configuration for multiple playlists.")
        print(f"You can add playlists by URL, search, or select from your own playlists.")

        # Add playlists interactively
        while True:
            if self.add_playlist_interactive():
                print(f"\n📊 Current configuration: {len(self.configs)} playlist(s)")

                if len(self.configs) > 0:
                    add_more = input("Add another playlist? (Y/n): ").strip().lower()
                    if add_more in ['n', 'no']:
                        break
            else:
                if len(self.configs) == 0:
                    continue_setup = input("No playlists added yet. Continue? (Y/n): ").strip().lower()
                    if continue_setup in ['n', 'no']:
                        break
                else:
                    break

        # Review and save
        if self.configs:
            self.review_and_save_config()

            print(f"\n✅ Configuration generator completed!")
            print(f"📊 Total playlists configured: {len(self.configs)}")
            print(f"\n🚀 Next steps:")
            print(f"1. Add the JSON configuration to your GitHub repository secrets")
            print(f"2. Verify your playlists are accessible in Spotify")
            print(f"3. The GitHub Action will use your configuration automatically")
        else:
            print(f"\n❌ No playlists configured. Run the script again to try again.")

def main():
    """Main function."""
    try:
        generator = PlaylistConfigGenerator()
        generator.run()

        # Clean up cache file
        try:
            os.remove(".spotify_cache_config")
        except:
            pass

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Configuration generator interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
