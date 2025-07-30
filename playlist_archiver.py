#!/usr/bin/env python3
"""
Spotify Playlist Archiver

This script creates daily archives of multiple Spotify playlists by copying
all tracks to archive playlists. It reuses existing archive playlists if they exist.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlaylistArchiver:
    def __init__(self):
        """Initialize the Spotify client with OAuth authentication."""
        self.sp = self._authenticate()
        self.user_id = self._get_current_user_id()

    def _authenticate(self) -> spotipy.Spotify:
        """Authenticate with Spotify using OAuth."""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8080/callback')

        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set")

        # For GitHub Actions, we'll use a refresh token approach
        scope = "playlist-read-private playlist-modify-public playlist-modify-private"

        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=None,  # Don't use cache file in GitHub Actions
            show_dialog=False
        )

        # Try to use refresh token if available
        refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')
        if refresh_token:
            token_info = auth_manager.refresh_access_token(refresh_token)
            return spotipy.Spotify(auth_manager=auth_manager)

        return spotipy.Spotify(auth_manager=auth_manager)

    def _get_current_user_id(self) -> str:
        """Get the current user's Spotify ID."""
        try:
            user_info = self.sp.current_user()
            return user_info['id']
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Get all tracks from a playlist."""
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)

        while results:
            for item in results['items']:
                if item['track'] and item['track']['id']:  # Skip local files and None tracks
                    track_info = {
                        'id': item['track']['id'],
                        'name': item['track']['name'],
                        'artists': [artist['name'] for artist in item['track']['artists']],
                        'uri': item['track']['uri'],
                        'added_at': item['added_at']
                    }
                    tracks.append(track_info)

            if results['next']:
                results = self.sp.next(results)
            else:
                break

        logger.info(f"Retrieved {len(tracks)} tracks from playlist")
        return tracks

    def find_existing_archive(self, original_playlist_name: str, custom_name: Optional[str] = None) -> Optional[str]:
        """Find existing archive playlist by name pattern."""
        try:
            # Generate archive name
            if custom_name:
                archive_name = f"{custom_name} (Cumulative)"
            else:
                archive_name = f"{original_playlist_name} (Cumulative)"

            results = self.sp.current_user_playlists(limit=50)
            while results:
                for playlist in results['items']:
                    if playlist['name'] == archive_name and playlist['owner']['id'] == self.user_id:
                        logger.info(f"Found existing archive playlist: {archive_name}")
                        return playlist['id']

                if results['next']:
                    results = self.sp.next(results)
                else:
                    break

            return None
        except Exception as e:
            logger.error(f"Error searching for existing archive: {e}")
            return None

    def create_archive_playlist(self, original_playlist_id: str, archive_name: str) -> str:
        """Create a new playlist for the archive."""
        try:
            # Get original playlist info
            original_playlist = self.sp.playlist(original_playlist_id)

            # Create description with original playlist info
            description = (
                f"Cumulative archive of '{original_playlist['name']}' "
                f"(last updated: {datetime.now().strftime('%Y-%m-%d at %H:%M UTC')}). "
                f"Original playlist: spotify:playlist:{original_playlist_id}"
            )

            # Create new playlist
            new_playlist = self.sp.user_playlist_create(
                user=self.user_id,
                name=archive_name,
                public=False,  # Keep archives private by default
                description=description
            )

            logger.info(f"Created archive playlist: {archive_name}")
            return new_playlist['id']

        except Exception as e:
            logger.error(f"Failed to create archive playlist: {e}")
            raise

    def get_archive_tracks(self, playlist_id: str) -> List[str]:
        """Get all track URIs from an archive playlist."""
        track_uris = []
        try:
            results = self.sp.playlist_tracks(playlist_id, fields="items(track(uri))")

            while results:
                for item in results['items']:
                    if item['track'] and item['track']['uri']:
                        track_uris.append(item['track']['uri'])

                if results['next']:
                    results = self.sp.next(results)
                else:
                    break

            logger.info(f"Found {len(track_uris)} existing tracks in archive")
            return track_uris

        except Exception as e:
            logger.error(f"Failed to get archive tracks: {e}")
            return []

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        """Add tracks to a playlist in batches."""
        # Spotify API allows max 100 tracks per request
        batch_size = 100

        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            try:
                self.sp.playlist_add_items(playlist_id, batch)
                logger.info(f"Added {len(batch)} tracks to playlist (batch {i//batch_size + 1})")
            except Exception as e:
                logger.error(f"Failed to add batch {i//batch_size + 1}: {e}")
                raise

    def archive_playlist(self, playlist_id: str, custom_name: Optional[str] = None) -> Dict:
        """
        Archive a playlist by creating or updating a cumulative archive playlist.

        Args:
            playlist_id: The Spotify playlist ID to archive
            custom_name: Optional custom name for the archive (will have "(Cumulative)" appended)

        Returns:
            Dict with archive information
        """
        try:
            # Get original playlist info
            original_playlist = self.sp.playlist(playlist_id)
            original_name = original_playlist['name']

            # Generate archive name
            if custom_name:
                archive_name = f"{custom_name} (Cumulative)"
            else:
                archive_name = f"{original_name} (Cumulative)"

            # Get all tracks from original playlist
            tracks = self.get_playlist_tracks(playlist_id)

            # Check if archive playlist already exists
            existing_archive_id = self.find_existing_archive(original_name, custom_name)

            if existing_archive_id:
                logger.info(f"Reusing existing archive playlist: {archive_name}")
                archive_playlist_id = existing_archive_id

                # Get existing tracks from archive
                existing_track_uris = self.get_archive_tracks(archive_playlist_id)
                existing_track_set = set(existing_track_uris)

                if tracks:
                    # Find new tracks that aren't already in the archive
                    source_track_uris = [track['uri'] for track in tracks]
                    new_track_uris = [uri for uri in source_track_uris if uri not in existing_track_set]

                    if new_track_uris:
                        self.add_tracks_to_playlist(archive_playlist_id, new_track_uris)
                        action_taken = f"updated (added {len(new_track_uris)} new tracks)"
                        logger.info(f"Added {len(new_track_uris)} new tracks to existing archive")
                    else:
                        action_taken = "no changes (all tracks already archived)"
                        logger.info("No new tracks to add - all tracks already in archive")
                else:
                    action_taken = "no changes (source playlist empty, archive preserved)"
                    logger.info("Source playlist is empty, but archive playlist preserved")
            else:
                if not tracks:
                    logger.warning("No tracks found in playlist to archive")
                    return {
                        'success': True,
                        'message': 'Playlist was empty - no archive created',
                        'original_playlist': original_name,
                        'track_count': 0
                    }

                # Create new archive playlist
                archive_playlist_id = self.create_archive_playlist(playlist_id, archive_name)
                track_uris = [track['uri'] for track in tracks]
                self.add_tracks_to_playlist(archive_playlist_id, track_uris)
                action_taken = "created"

            # Create summary
            # Get final track count from archive
            final_archive_tracks = self.get_archive_tracks(archive_playlist_id)

            result = {
                'success': True,
                'original_playlist': original_name,
                'original_playlist_id': playlist_id,
                'archive_playlist': archive_name,
                'archive_playlist_id': archive_playlist_id,
                'source_track_count': len(tracks),
                'archive_track_count': len(final_archive_tracks),
                'archived_at': datetime.now().isoformat(),
                'action_taken': action_taken,
                'tracks': tracks
            }

            logger.info(f"Successfully processed archive for playlist '{original_name}': {action_taken}")
            return result

        except Exception as e:
            # Check if this is likely a Spotify API restriction error
            error_msg = str(e)
            is_404_error = "404" in error_msg or "Resource not found" in error_msg
            is_algorithmic_playlist = playlist_id.startswith('37i9dQ')

            if is_404_error and is_algorithmic_playlist:
                enhanced_error = (
                    f"Playlist {playlist_id} is not accessible. This appears to be a Spotify "
                    f"algorithmic playlist (Daily Mix, Discover Weekly, etc.) which are blocked "
                    f"from API access since November 27, 2024. Use your own created playlists "
                    f"instead of algorithmic ones. Original error: {error_msg}"
                )
                logger.error(enhanced_error)
                return {
                    'success': False,
                    'error': enhanced_error,
                    'original_playlist_id': playlist_id,
                    'action_taken': 'failed',
                    'is_api_restriction': True
                }
            else:
                logger.error(f"Failed to archive playlist: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'original_playlist_id': playlist_id,
                    'action_taken': 'failed'
                }

    def archive_multiple_playlists(self, playlist_configs: List[Dict]) -> List[Dict]:
        """
        Archive multiple playlists.

        Args:
            playlist_configs: List of dicts with keys: 'playlist_id', 'custom_name' (optional)

        Returns:
            List of archive results
        """
        results = []

        for config in playlist_configs:
            playlist_id = config['playlist_id']
            custom_name = config.get('custom_name')

            logger.info(f"Processing playlist: {playlist_id}")
            result = self.archive_playlist(playlist_id, custom_name)
            results.append(result)

        return results

    def save_archive_log(self, archive_results: List[Dict], log_file: str = 'archive_log.json') -> None:
        """Save archive results to a log file."""
        try:
            # Load existing log or create new one
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {'archive_sessions': []}

            # Add new archive session entry
            session_entry = {
                'session_date': datetime.now().isoformat(),
                'archives': archive_results,
                'total_playlists': len(archive_results),
                'successful_archives': len([r for r in archive_results if r.get('success', False)])
            }

            log_data['archive_sessions'].append(session_entry)

            # Save updated log
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)

            logger.info(f"Archive log saved to {log_file}")

        except Exception as e:
            logger.error(f"Failed to save archive log: {e}")


def parse_playlist_config() -> List[Dict]:
    """Parse playlist configuration from environment variables."""
    # Try to get playlist configuration as JSON first
    playlist_config_json = os.getenv('SPOTIFY_PLAYLISTS_CONFIG')
    if playlist_config_json:
        try:
            config = json.loads(playlist_config_json)
            if isinstance(config, list):
                return config
            else:
                logger.error("SPOTIFY_PLAYLISTS_CONFIG must be a JSON array")
                sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in SPOTIFY_PLAYLISTS_CONFIG: {e}")
            sys.exit(1)

    # Try comma-separated playlist IDs (handles single or multiple)
    playlist_ids = os.getenv('SPOTIFY_PLAYLIST_IDS')
    if playlist_ids:
        playlists = []
        ids_list = [pid.strip() for pid in playlist_ids.split(',') if pid.strip()]

        for pid in ids_list:
            playlist_config = {
                'playlist_id': pid,
                'custom_name': None
            }
            playlists.append(playlist_config)
        return playlists

    logger.error("No playlist configuration found. Set SPOTIFY_PLAYLISTS_CONFIG or SPOTIFY_PLAYLIST_IDS")
    sys.exit(1)

def main():
    """Main function to run the playlist archiver."""
    # Parse playlist configuration
    playlist_configs = parse_playlist_config()

    logger.info(f"Found {len(playlist_configs)} playlist(s) to archive")

    # Check for potential API restriction issues
    algorithmic_count = sum(1 for config in playlist_configs if config['playlist_id'].startswith('37i9dQ'))
    if algorithmic_count > 0:
        logger.warning(f"Detected {algorithmic_count} algorithmic playlist(s) that may be blocked by Spotify API restrictions")
        logger.warning("If you encounter 404 errors, use your own created playlists instead of algorithmic ones")

    # Initialize archiver
    try:
        archiver = PlaylistArchiver()

        # Archive all playlists
        results = archiver.archive_multiple_playlists(playlist_configs)

        # Save log
        archiver.save_archive_log(results)

        # Print summary
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]

        print(f"📊 Archive Summary:")
        print(f"   Total playlists: {len(results)}")
        print(f"   Successful: {len(successful)}")
        print(f"   Failed: {len(failed)}")

        for result in successful:
            action = result.get('action_taken', 'processed')
            source_count = result.get('source_track_count', 0)
            archive_count = result.get('archive_track_count', 0)
            print(f"✅ {action.title()}: {result['original_playlist']} → {result['archive_playlist']}")
            print(f"   Source: {source_count} tracks | Archive: {archive_count} tracks")

        for result in failed:
            error_msg = result.get('error', 'Unknown error')
            playlist_name = result.get('original_playlist', 'Unknown')
            playlist_id = result.get('original_playlist_id', 'Unknown')

            # Provide additional guidance for API restriction errors
            if result.get('is_api_restriction'):
                print(f"❌ Failed: {playlist_name} - SPOTIFY API RESTRICTION")
                print(f"   Playlist ID {playlist_id} is blocked (algorithmic playlist)")
                print(f"   💡 Solution: Use your own created playlists instead of algorithmic ones")
            else:
                print(f"❌ Failed: {playlist_name} - {error_msg}")

        if failed:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
