import asyncio
import os
from telethon import TelegramClient
import random
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
import logging
import subprocess
import urllib.parse

dotenv_path="/opt/telegram_suggest/.env"
from dotenv import load_dotenv
load_dotenv(dotenv_path)

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

client = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

async def get_matching_songs():
    global client
    try:
        if not client:
            client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            await client.start()

        channel = await client.get_entity(CHANNEL_USERNAME)
        messages = await client.get_messages(channel, limit=None)

        # Shuffle the messages list for increased randomness
        random.shuffle(messages)

        # Get a random message from the list
        random_message = random.choice(messages)

        # Extract genres from the first random song
        genres = set(tag.strip() for tag in random_message.text.split() if tag.startswith('#'))

        # Filter other messages that contain at least two matching genres
        matching_messages = []
        for msg in messages:
            if msg.text:
                count_matching_genres = sum(genre in msg.text for genre in genres)
                if count_matching_genres >= 2:
                    matching_messages.append(msg)
                    if len(matching_messages) >= 3:
                        break  # Stop the loop if we have at least 3 matching messages

        # Create an empty list to store the song details
        song_details = []

        # Append each selected song's details to the list
        for song in matching_messages[:3]:  # Select the first three matching messages
            track_name = ''
            artist_name = ''
            for line in song.text.strip().split('\n'):
                if line.startswith('Track Name:'):
                    track_name = line.split('Track Name:', 1)[-1].strip().replace(' ', '%20')
                elif line.startswith('Artist:'):
                    artist_name = line.split('Artist:', 1)[-1].strip().replace(' ', '%20')

            if track_name and artist_name:
                song_details.append(f"track:{track_name}%20artist:{artist_name}")

        logger.info("Matching songs found:")
        for idx, song_detail in enumerate(song_details, start=1):
            logger.info(f"{idx}. {song_detail}")

        return song_details

    except Exception as e:
        logger.error(f"Error in get_matching_songs: {e}")
        return []

    finally:
        await client.disconnect()

# Helper function to search for a track in Spotify
def search_track(sp, track_name, artist_name):
    query = f"track:{track_name} artist:{artist_name}"
    result = sp.search(q=query, type='track', limit=1)
    items = result.get('tracks', {}).get('items', [])
    if items:
        return items[0]['id']
    return None

async def get_song_recommendation(sp, song_ids):
    try:
        recommendation = sp.recommendations(seed_tracks=song_ids, limit=1, min_popularity=70)
        if recommendation['tracks']:
            track = recommendation['tracks'][0]
            track_url = track['external_urls']['spotify']
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            album_name = track['album']['name']
            release_date = track['album']['release_date']
            genres = [f"#{genre}" for genre in track['artists'][0].get('genres', [])]  # Handle case when genres are not available

            logger.info(f"Recommendation Popularity: {track['popularity']}")
            logger.info(f"Recommendation Track: {track_name} - Artist: {artist_name} - Album: {album_name} - Release Date: {release_date}")

            # Check if the recommended song is a duplicate
            is_duplicate = await duplicate_finder(track_name, artist_name)
            if is_duplicate:
                logger.warning("Duplicate song found in the channel. Recommending another song.")
                return await get_song_recommendation(sp, song_ids)  # Recommend another song
            return track_url, track_name, artist_name, album_name, release_date, genres  # Return additional metadata
    except Exception as e:
        logger.error(f"Error while fetching song recommendation: {e}")
    return None, None, None, None, None, None  # Return None for all values if recommendation fails


async def duplicate_finder(track_name, artist_name):
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()

        channel = await client.get_entity(CHANNEL_USERNAME)
        messages = await client.get_messages(channel, limit=None)

        for msg in messages:
            if msg.text:
                lines = msg.text.strip().split('\n')
                track_found = False
                artist_found = False

                for line in lines:
                    if line.startswith('Track Name:'):
                        channel_track_name = line.split('Track Name:', 1)[-1].strip()
                        if track_name.lower() == channel_track_name.lower():
                            track_found = True

                    elif line.startswith('Artist:'):
                        channel_artist_name = line.split('Artist:', 1)[-1].strip()
                        if artist_name.lower() == channel_artist_name.lower():
                            artist_found = True

                # If both track and artist found, it is a duplicate
                if track_found and artist_found:
                    logger.warning(f"Duplicate found: {track_name} - {artist_name} in channel's music.")
                    await asyncio.sleep(1)  # Sleep for 1 second
                    return True

    except Exception as e:
        logger.error(f"Error while checking for duplicates: {e}")

    finally:
        await client.disconnect()

    return False

async def download_song(client, sp, recommendation_url, artist_name, track_name, album_name, release_date):
    try:
        # Use spotdl to download the song using the Spotify link
        spotdl_download_command = [
            'spotdl',
            recommendation_url,
            '--format',
            'mp3',
            '--overwrite',
            'skip',
            '--output',
            './mp3',
        ]
        subprocess.run(spotdl_download_command, check=True)

        logger.info("Song downloaded successfully.")

        # Get the artist and track name from the recommendation URL
        recommendation_artist_name = artist_name
        recommendation_track_name = track_name

        # Send all .mp3 files in the ./mp3 folder to Telegram
        for filename in os.listdir('./mp3'):
            if filename.endswith('.mp3'):
                file_path = os.path.join('./mp3', filename)

                # Get song metadata for the downloaded song
                metadata = await get_song_metadata(sp, recommendation_url)
                if metadata:
                    caption = (
                        f"Track Name: {metadata['track_name']}\n"
                        f"Artist: {metadata['artist']}\n"
                        f"Album: {metadata['album']}\n"
                        f"Release Date: {metadata['release_date']}\n"
                        f"Genres: {' '.join(metadata['genres'])}\n"
                    )
                else:
                    # If metadata retrieval fails, use the original values
                    caption = (
                        f"Track Name: {recommendation_track_name}\n"
                        f"Artist: {recommendation_artist_name}\n"
                        f"Album: {album_name}\n"
                        f"Release Date: {release_date}\n"
                    )

                # Send the file to the Telegram channel with the caption
                await send_to_telegram(client, file_path, caption)

                os.remove(file_path)
                logger.info(f"File '{filename}' sent and removed successfully.")
                
                # Break the loop after successfully sending the file
                break

    except Exception as e:
        logger.error(f"Error while downloading the song: {e}")

# Helper function to get song metadata from Spotify
async def get_song_metadata(sp, song_id):
    try:
        track_info = sp.track(song_id)
        artist_id = track_info['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        genres = artist_info['genres']

        # Format genre tags by replacing spaces and dashes with underscores
        genre_tags = ['#' + genre.replace(' ', '_').replace('-', '_').replace('&', '_') for genre in genres]

        # Retrieve danceability value
        audio_features = sp.audio_features(song_id)
        danceability = audio_features[0]['danceability']

        # Check danceability value and add #dance to genre_tags if necessary
        if danceability > 0.7:
            genre_tags.append('#dance')

        # Prepare the metadata dictionary
        metadata = {
            'track_name': track_info['name'],
            'artist': track_info['artists'][0]['name'],
            'album': track_info['album']['name'],
            'release_date': track_info['album']['release_date'],
            'genres': genre_tags
        }

        return metadata

    except Exception as e:
        logger.error(f"Error while fetching song metadata: {e}")

    return None
async def send_to_telegram(client, file_path, filecaption):
    try:
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.start()
        # Send the file to the Telegram channel
        entity = await client.get_entity(CHANNEL_USERNAME)  # await the get_entity method
        await client.send_file(entity, file=file_path , caption=filecaption)  # pass the file as 'file' parameter

        logger.info(f"File sent successfully to {CHANNEL_USERNAME}.")

    except Exception as e:
        logger.error(f"Error while sending file to Telegram: {e}")

    finally:
        await client.disconnect()


# Main function to run the script
async def main():
    loop = asyncio.get_event_loop()
    retry_count = 5
    min_matching_songs = 2

    matching_songs = []
    duplicate_counter = 0  # Initialize duplicate counter

    while len(matching_songs) < min_matching_songs:
        matching_songs = await get_matching_songs()
        if len(matching_songs) < min_matching_songs:
            logger.warning(f"Matching songs not sufficient. Retrying...")
            await asyncio.sleep(1)

        retry_count -= 1
        if retry_count <= 0:
            logger.error("Insufficient matching songs after multiple attempts. Exiting.")
            return

        # If matching_songs is empty, it means get_matching_songs returned no songs due to duplicates.
        # In that case, reset the duplicate counter and start over with get_matching_songs.
        if not matching_songs:
            duplicate_counter = 0

        if duplicate_counter >= 3:
            logger.warning("Reached maximum duplicate count. Starting over with get_matching_songs.")
            duplicate_counter = 0
        else:
            duplicate_counter += 1

    # Initialize the Spotipy client
    auth_manager = SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
    sp = Spotify(auth_manager=auth_manager)

    # Search for each song in Spotify and get the song ID and recommendation
    metadata_list = []
    for song_detail in matching_songs:
        track_name = song_detail.split('track:')[1].split('%20artist:')[0].replace('%20', ' ')
        artist_name = song_detail.split('%20artist:')[1].replace('%20', ' ')

        song_id = search_track(sp, track_name, artist_name)
        if song_id:
            logger.info(f"Track: {track_name} - Artist: {artist_name} - ID: {song_id}")

            # Get song metadata from Spotify
            metadata = await get_song_metadata(sp, song_id)
            if metadata:
                metadata_list.append(metadata)
            else:
                logger.warning(f"Failed to fetch metadata for Track: {track_name} - Artist: {artist_name}")

        else:
            logger.warning(f"Track: {track_name} - Artist: {artist_name} - Not found on Spotify")

    # Get song recommendation based on seed tracks
    if metadata_list:
        for metadata in metadata_list:
            recommendation_url, recommendation_track_name, recommendation_artist_name, album_name, release_date, genres = await get_song_recommendation(sp, [song_id])
            if recommendation_url:
                logger.info(f"Recommendation Track: {recommendation_track_name} - Artist: {recommendation_artist_name} - URL: {recommendation_url}")

                # Create formatted caption with metadata
                caption = (
                    f"Track Name: {metadata['track_name']}\n"
                    f"Artist: {metadata['artist']}\n"
                    f"Album: {metadata['album']}\n"
                    f"Release Date: {metadata['release_date']}\n"
                    f"Genres: {' '.join(metadata['genres'])}\n"
                )

                await download_song(client, sp, recommendation_url, artist_name, track_name, album_name, release_date)
                # Break the loop after successfully sending the file
                break

            else:
                logger.info("No recommendation found.")
    
    # Disconnect the client after sending the file
    await client.disconnect()

# Run the main function
if __name__ == '__main__':
    asyncio.run(main())

