# Spotify Playlist Archiver

Automatically create cumulative archives of multiple Spotify playlists using GitHub Actions. This tool adds new tracks from your playlists to permanent archive playlists with "(Cumulative)" suffix, maintaining growing collections of your music history. Archive playlists are never cleared - they only grow by adding new tracks that weren't previously archived.

## Features

- 🕒 **Daily Automation**: Runs automatically every day at 9:00 AM UTC
- 📝 **Multiple Playlists**: Archive multiple playlists in a single run with custom names
- 🔄 **Cumulative Updates**: Adds new tracks to existing archive playlists without removing old ones
- 📝 **Permanent Archives**: Creates playlists with "(Cumulative)" suffix that preserve all historically added tracks
- 🔒 **Private Archives**: Archive playlists are kept private by default
- 📊 **Detailed Logging**: Tracks all archived playlists with comprehensive metadata
- 🚀 **Manual Triggers**: Run archives on-demand via GitHub Actions
- 🎵 **Complete Track Info**: Preserves track names, artists, and metadata

## ⚠️ Important Notice: Spotify API Restrictions

**As of November 27, 2024**, Spotify has restricted access to **algorithmic and editorial playlists** (Daily Mix, Discover Weekly, Release Radar, etc.) for new and development-mode applications.

**Affected Playlists:**
- Playlist IDs starting with `37i9dQ` (Daily Mix, Discover Weekly, etc.)
- Spotify's auto-generated and editorial playlists
- Most "Made for You" playlists

**What This Means:**
- ❌ You **cannot** archive Spotify's algorithmic playlists
- ✅ You **can** archive your own playlists and playlists you follow
- ✅ Existing apps with extended access are unaffected

**Solution:** Test your playlist IDs manually or use your own created playlists to avoid API restrictions.

## Prerequisites

1. **Spotify Account**: You need a Spotify account (Free or Premium)
2. **Spotify App**: Create a Spotify application at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
3. **GitHub Repository**: Fork or create a repository with this code

## Setup Instructions

### Step 1: Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click "Create app"
3. Fill in the details:
   - **App name**: "Playlist Archiver" (or your preferred name)
   - **App description**: "Daily playlist archiving tool"
   - **Redirect URI**: `http://localhost:8080/callback`
   - **API used**: Web API
4. Save the app and note your **Client ID** and **Client Secret**

### Step 2: Get Authentication Tokens

Run the setup script locally to get your refresh token:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the authentication setup
python setup_auth.py
```

Follow the prompts to:
1. Enter your Spotify Client ID and Secret
2. Authorize the app in your browser
3. Copy the redirect URL back to the script
4. Get your refresh token

### Step 3: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

**Required Secrets:**
- `SPOTIFY_CLIENT_ID`: Your Spotify app's Client ID
- `SPOTIFY_CLIENT_SECRET`: Your Spotify app's Client Secret
- `SPOTIFY_REFRESH_TOKEN`: The refresh token from the setup script

**Playlist Configuration (choose one method):**
- `SPOTIFY_PLAYLISTS_CONFIG`: JSON array of playlist configurations (recommended for custom names)
- `SPOTIFY_PLAYLIST_IDS`: Comma-separated playlist IDs (handles single or multiple playlists)

#### Playlist Configuration Methods

**Method 1: Multiple Playlists with Custom Names (Recommended)**

Set `SPOTIFY_PLAYLISTS_CONFIG` as a JSON array:
```json
[
  {
    "playlist_id": "4rOoJ6Ffppi7YouzCP0tjz",
    "custom_name": "My Favorite Songs Archive"
  },
  {
    "playlist_id": "1BxfuPKGuaTgP6aM0EcjTK",
    "custom_name": "Road Trip Playlist Archive"
  },
  {
    "playlist_id": "3cEYpjA9oz9GiPac4AsH4n",
    "custom_name": null
  }
]
```

⚠️ **Note:** Avoid playlist IDs starting with `37i9dQ` as these are blocked algorithmic playlists.

**Method 2: Simple Playlist IDs**

Set `SPOTIFY_PLAYLIST_IDS` to single or multiple comma-separated IDs:

*Single playlist:*
```
SPOTIFY_PLAYLIST_IDS=4rOoJ6Ffppi7YouzCP0tjz
```
**Result:** `"Original Playlist Name (Cumulative)"`

*Multiple playlists:*
```
SPOTIFY_PLAYLIST_IDS=4rOoJ6Ffppi7YouzCP0tjz,1BxfuPKGuaTgP6aM0EcjTK,3cEYpjA9oz9GiPac4AsH4n
```
**Results:** Each playlist creates an archive with its original name + "(Cumulative)"

⚠️ **Note:** Only use accessible playlist IDs. Avoid IDs starting with `37i9dQ` as these are blocked algorithmic playlists.

#### Finding Playlist IDs

**Method 1: From Your Spotify Library**
Go to your Spotify library and use playlists you created or follow that are publicly accessible.

**Method 2: Manual Extraction**
From a Spotify playlist URL like:
```
https://open.spotify.com/playlist/4rOoJ6Ffppi7YouzCP0tjz?si=...
```

The playlist ID is: `4rOoJ6Ffppi7YouzCP0tjz`

⚠️ **Important:** Only use playlist IDs from playlists you created or have access to. Verify they work before adding to your configuration.

### Step 4: Configure Schedule (Optional)

The default schedule runs daily at 9:00 AM UTC. To change this:

1. Edit `.github/workflows/archive-playlist.yml`
2. Modify the cron expression in the `schedule` section:

```yaml
schedule:
  # Run daily at 9:00 AM UTC
  - cron: '0 9 * * *'
```

Common cron examples:
- `0 12 * * *` - Daily at noon UTC
- `0 9 * * 1` - Weekly on Mondays at 9 AM UTC
- `0 9 1 * *` - Monthly on the 1st at 9 AM UTC

## Usage

### Automatic Daily Archives

Once set up, the GitHub Action will automatically:
1. Run daily at your scheduled time
2. Process all configured playlists
3. Create new archive playlists or add new tracks to existing ones
4. Add only new tracks that weren't previously archived (duplicates are avoided)
5. Log detailed results for all operations

### Manual Archives

You can also trigger archives manually:

1. Go to your repository's **Actions** tab
2. Select "Archive Spotify Playlist"
3. Click "Run workflow"
4. Optionally specify:
   - JSON playlist configuration (overrides repository secrets)
   - Comma-separated playlist IDs for quick archive

### Viewing Results

After each run, you can:
- Check the **Actions** tab for run status and logs
- Download the `archive_log.json` artifact for detailed results
- See your new archive playlists in Spotify

## Archive Log Format

The tool creates an `archive_log.json` file with detailed information organized by archive sessions:

```json
{
  "archive_sessions": [
    {
      "session_date": "2024-01-15T09:00:00",
      "total_playlists": 2,
      "successful_archives": 2,
      "archives": [
        {
          "success": true,
          "original_playlist": "My Favorite Songs",
          "original_playlist_id": "4rOoJ6Ffppi7YouzCP0tjz",
          "archive_playlist": "My Favorite Songs (Cumulative)",
          "archive_playlist_id": "1a2b3c4d5e6f7g8h9i0j1k2l",
          "track_count": 50,
          "archived_at": "2024-01-15T09:00:00",
          "action_taken": "updated",
          "tracks": [
            {
              "id": "4iV5W9uYEdYUVa79Axb7Rh",
              "name": "Song Title",
              "artists": ["Artist Name"],
              "uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
              "added_at": "2024-01-14T15:30:00Z"
            }
          ]
        }
      ]
    }
  ]
}
```

**Action Types:**
- `created`: New cumulative archive playlist was created with all source tracks
- `updated (added X new tracks)`: X new tracks were added to existing archive
- `no changes (all tracks already archived)`: All source tracks were already in archive
- `no changes (source playlist empty, archive preserved)`: Source is empty but archive remains intact

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Verify your Client ID and Secret are correct
- Ensure your refresh token hasn't expired (re-run `setup_auth.py`)
- Check that redirect URI matches exactly: `http://localhost:8080/callback`

**"Playlist not found" or "HTTP 404 errors"**
- ⚠️ **Most likely cause:** Trying to archive blocked algorithmic playlists (IDs starting with `37i9dQ`)
- Use your own created playlists instead of Spotify's algorithmic ones
- Verify the playlist ID is correct and not deleted
- Check that you have permission to read the playlist
- Verify you have access to the playlist in Spotify

**"Failed to create archive playlist"**
- Verify you have sufficient permissions
- Check your Spotify account status
- Ensure you haven't hit playlist creation limits

**GitHub Action fails with 404 errors**
- This usually means you're trying to archive blocked algorithmic playlists
- Remove `SPOTIFY_PLAYLIST_IDS` secret to use your local `playlists_config.json`
- Or update the secret with accessible playlist IDs (avoid `37i9dQ` prefixes)
- Check that all required secrets are set correctly
- Verify secret names match exactly
- Review the action logs for specific error messages

### Debug Mode

To get more detailed logs, you can modify the Python script to use DEBUG level logging:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Customization

### Custom Archive Names

**For JSON Configuration:**
Use the `custom_name` field in your playlist configuration:
```json
{
  "playlist_id": "4rOoJ6Ffppi7YouzCP0tjz",
  "custom_name": "My Favorite Songs Archive"
}
```
Result: "My Favorite Songs Archive (Cumulative)"

**For Simple Playlist IDs:**
Archives automatically use the original playlist name:
```
SPOTIFY_PLAYLIST_IDS=4rOoJ6Ffppi7YouzCP0tjz
```
Result: "Original Playlist Name (Cumulative)"

### Multiple Playlists

The system natively supports multiple playlists using the JSON configuration method. For advanced setups:

1. **Different Schedules**: Create multiple workflow files with different cron schedules
2. **Playlist Groups**: Group related playlists in separate configuration files
3. **Custom Workflows**: Create specialized workflows for different playlist categories

### Archive Settings

Modify the script to change archive behavior:

- **Public vs Private**: Change `public=False` to `public=True` in `create_archive_playlist()`
- **Description Format**: Modify the description template in `create_archive_playlist()`
- **Archive Naming**: Modify the naming logic in `archive_playlist()` method (change "(Cumulative)" suffix)
- **Reuse Behavior**: Modify `find_existing_archive()` to change how existing archives are detected

## API Limits

Spotify has rate limits on their API:
- **General**: 100 requests per second per app
- **Playlist Operations**: More restrictive for write operations

The tool includes automatic batching and error handling to respect these limits.

## Privacy & Security

- Archive playlists are **private by default**
- Your Spotify credentials are stored as **encrypted GitHub secrets**
- The tool only requests necessary permissions
- No personal data is stored or transmitted outside of Spotify and GitHub

## Frequently Asked Questions

### Q: Why am I getting 404 errors for playlist IDs starting with `37i9dQ`?

**A:** These are Spotify's algorithmic playlists (Daily Mix, Discover Weekly, etc.) that were blocked from API access on November 27, 2024. You cannot archive these playlists anymore with new or development-mode apps.

**Solutions:**
- Archive your own created playlists instead of Spotify's generated ones
- Use playlists you follow that are publicly accessible
- Create manual playlists based on tracks you like from algorithmic playlists

### Q: Can I still archive my own playlists and playlists I follow?

**A:** Yes! The API restrictions only affect Spotify's algorithmic and editorial playlists. You can still archive:
- ✅ Playlists you created
- ✅ Public playlists you follow (if accessible)
- ✅ Collaborative playlists you're part of
- ❌ Spotify's algorithmic playlists (37i9dQ...)

### Q: How do I know which playlists I can archive?

**A:** Test your playlists manually:
1. Use your own created playlists (always accessible)
2. Verify playlist access by checking them in your Spotify library
3. Avoid playlist IDs starting with `37i9dQ`

### Q: Can I get access to algorithmic playlists somehow?

**A:** Possibly, but it's difficult:
1. **Apply for Extended API Access** through your Spotify Developer Dashboard
2. Explain your use case for needing algorithmic playlist access
3. Wait for Spotify's approval (not guaranteed)
4. Existing apps with extended access are unaffected by the restrictions

### Q: My GitHub Action worked before but now fails with 404 errors. What happened?

**A:** Your `SPOTIFY_PLAYLIST_IDS` GitHub secret likely contains blocked algorithmic playlist IDs.

**Fix:**
1. Use your own created playlists instead of algorithmic ones
2. Either remove the `SPOTIFY_PLAYLIST_IDS` secret to use your `playlists_config.json` file
3. Or update the secret with accessible playlist IDs (avoid `37i9dQ` prefixes)

### Q: What's the difference between playlist types?

**A:**
- **Your Playlists**: Created by you - ✅ Always archivable
- **Followed Playlists**: Public playlists you follow - ✅ Usually archivable
- **Collaborative Playlists**: Shared playlists - ✅ Usually archivable
- **Algorithmic Playlists** (37i9dQ...): Spotify-generated - ❌ Blocked since Nov 2024

### Q: Can I archive multiple playlists at once?

**A:** Yes! Use the JSON configuration format:
```json
[
  {"playlist_id": "your_playlist_id_1", "custom_name": "Archive Name 1"},
  {"playlist_id": "your_playlist_id_2", "custom_name": "Archive Name 2"}
]
```

### Q: What happens if I try to archive an empty playlist?

**A:** If the source playlist is empty:
- For new archives: No archive playlist will be created
- For existing archives: The archive playlist is preserved with all its existing tracks intact

### Q: How often should I run the archiver?

**A:** The default daily schedule works well for most users. You can adjust the frequency based on how often your playlists change:
- **Daily**: For frequently updated playlists
- **Weekly**: For occasionally updated playlists
- **Manual**: Use "Run workflow" button for on-demand archiving

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review GitHub Action logs
3. Create an issue with:
   - Error messages
   - Steps to reproduce
   - Your setup configuration (without secrets)
