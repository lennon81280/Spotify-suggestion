![image](https://github.com/lennon81280/Telegram-Suggester-By-Spotify-Suggetion/assets/13959550/90d30785-cca2-475a-9c80-43e00ad058f4)# Telegram Music Suggester

Telegram Music Suggester is a Python script that finds and recommends music from a Telegram channel based on genres. It uses the Telegram API, Spotify API (via Spotipy library), and spotdl to download and recommend songs. The script leverages asynchronous programming with asyncio to efficiently fetch and process data from both APIs.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)

## Introduction

Telegram Music Suggester is a tool designed to suggest and download music from a specified Telegram channel. It works by analyzing the messages in the channel, extracting genre information, and then finding matching songs on Spotify. The script then recommends songs based on the found genres, and finally, downloads the recommended songs using spotdl and sends them back to the Telegram channel with additional metadata.

## Features

- Fetches messages from a specified Telegram channel to find matching songs based on genre tags.
- Uses the Spotify API (via Spotipy library) to search for tracks based on track names and artist names.
- Retrieves song recommendations from Spotify based on the matching songs and certain criteria.
- Downloads the recommended songs using spotdl in mp3 format.
- Sends the recommended songs back to the Telegram channel along with additional metadata like track name, artist name, album name, release date, and genres.
- Handles duplicates in the Telegram channel to avoid suggesting the same song multiple times.
- Provides logging for various events and errors during the process.

## Requirements

Before using the script, make sure you have the following requirements installed:

- Python 3.7+
- Telethon library (`pip install telethon`)
- Spotipy library (`pip install spotipy`)
- Spotdl library (`pip install spotdl`)
- Python-dotenv library (`pip install python-dotenv`)

Additionally, you will need to have the necessary API credentials for both the Telegram and Spotify APIs.

I should mention that your music in music channel must be in this format : 

![image](https://github.com/lennon81280/Telegram-Suggester-By-Spotify-Suggetion/assets/13959550/0a5ecb56-72ef-494b-893c-f9591d9ac955)

## Installation

1. Clone this repository to your local machine:
   git clone https://github.com/lennon81280/Telegram-Suggester-By-Spotify-Suggetion.git
   cd Telegram-Suggester-By-Spotify-Suggetion

    Install the required Python libraries using pip.

Usage

To use the Telegram Music Suggester script:

    Set up your environment variables:
    Fill the .env file in the root directory of the project.
    Add the following environment variables to the .env file:

    API_ID=<your_telegram_api_id>
    API_HASH=<your_telegram_api_hash>
    SESSION_NAME=<your_telegram_session_name>
    CHANNEL_USERNAME=<telegram_channel_username>
    SPOTIPY_CLIENT_ID=<your_spotify_client_id>
    SPOTIPY_CLIENT_SECRET=<your_spotify_client_secret>

    Replace the placeholders with your actual API credentials.

Run the script:

    python telegram_suggest.py
    
    The script will fetch matching songs from the specified Telegram channel, search for each song on Spotify, and recommend songs based on certain criteria. It will then download the recommended songs using spotdl and send them back to the Telegram channel with metadata.

Configuration

You can customize certain parameters in the script to suit your preferences. For example, you can adjust the minimum matching songs required, retry count, and other settings in the main() function.
License

This project is licensed under the MIT License - see the LICENSE file for details.
