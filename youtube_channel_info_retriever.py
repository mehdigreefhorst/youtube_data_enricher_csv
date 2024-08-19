
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import dotenv
dotenv.load_dotenv()


def select_language():
    """
    Prompts the user to select a language for the application.

    :return: (str) The selected language code ('EN' or 'FR')
    """
    language = input("Choose language (Type 'EN' for English or 'FR' for French): ").upper()
    if language in ['EN', 'FR']:
        return language
    else:
        print("Invalid language selection. Please choose either 'EN' or 'FR'.")
        return select_language()


def translate_message(message, language):
    """
    Translates a given message to the selected language.

    :param message: (str) The message key to be translated
    :param language: (str) The language code ('EN' or 'FR')
    :return: (str) The translated message
    """
    translations = {
        'EN': {
            'enter_channel_name': "Enter the YouTube channel name: ",
            'channel_info': "Channel Information:",
            'description': "Description: ",
            'subscribers': "Subscribers: ",
            'views': "Views: ",
            'total_videos': "Total Videos: ",
            'created_at': "Created at: ",
            'on_youtube_since': "On YouTube since: ",
            'latest_video': "Latest Video:",
            'title': "Title: ",
            'published_at': "Published at: ",
            'url': "URL: ",
            'no_video_found': "No video found.",
            'invalid_channel': "The specified channel does not exist or is inaccessible."
        },
        'FR': {
            'enter_channel_name': "Entrez le nom de la chaîne YouTube : ",
            'channel_info': "Informations sur la chaîne :",
            'description': "Description : ",
            'subscribers': "Abonnés : ",
            'views': "Vues : ",
            'total_videos': "Total de vidéos : ",
            'created_at': "Créée le : ",
            'on_youtube_since': "Sur YouTube depuis : ",
            'latest_video': "Dernière vidéo :",
            'title': "Titre : ",
            'published_at': "Publiée le : ",
            'url': "URL : ",
            'no_video_found': "Aucune vidéo trouvée.",
            'invalid_channel': "La chaîne spécifiée n'existe pas ou est inaccessible."
        }
    }
    return translations[language][message]


def search_channel(channel_name):
    """
    Searches for a YouTube channel by name.

    :param channel_name: (str) The name of the channel to search for
    :return: (str) The channel ID if found, None otherwise
    """
    API_KEY = os.getenv("YOUTUBE_API_KEY")

    print("I am searching the channel name for its ID with API_KEY: ", API_KEY)
    print("I am searching the channel name for its ID with channel_name: ", channel_name)

    youtube = build('youtube', 'v3', developerKey=API_KEY)
    try:
        request = youtube.search().list(
            part='snippet',
            q=channel_name,
            type='channel'
        )
        response = request.execute()

        if 'items' in response and response['items']:
            channel = response['items'][0]
            channel_id = channel['id']['channelId']
            return channel_id
    except HttpError as e:
        print(f"Error: {e}")
    return None


def get_channel_info(channel_id):
    """
    Retrieves detailed information about a YouTube channel.

    :param channel_id: (str) The ID of the channel
    :return: (tuple) Channel title, description, subscriber count, view count, video count, and creation date
    """
    API_KEY = os.getenv("YOUTUBE_API_KEY")

    print("API_KEY: ", API_KEY)
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    try:
        request = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        response = request.execute()

        if 'items' in response:
            channel = response['items'][0]
            channel_title = channel['snippet']['title']
            description = channel['snippet']['description']
            subs_count = int(channel['statistics']['subscriberCount'])
            view_count = int(channel['statistics']['viewCount'])
            video_count = int(channel['statistics']['videoCount'])
            created_at = channel['snippet']['publishedAt']
            return channel_title, description, subs_count, view_count, video_count, created_at
    except HttpError as e:
        print(f"Error: {e}")
    return None, None, None, None, None, None


def get_latest_video_info(channel_id):
    """
    Retrieves information about the latest video from a YouTube channel.

    :param channel_id: (str) The ID of the channel
    :return: (tuple) Video title, publish date, and URL of the latest video
    """
    API_KEY = os.getenv("YOUTUBE_API_KEY")

    youtube = build('youtube', 'v3', developerKey=API_KEY)
    try:
        request = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            order='date',
            type='video',
            maxResults=1
        )
        response = request.execute()

        if 'items' in response and response['items']:
            latest_video = response['items'][0]
            video_title = latest_video['snippet']['title']
            video_published_at = latest_video['snippet']['publishedAt']
            video_url = f"https://www.youtube.com/watch?v={latest_video['id']['videoId']}"
            return video_title, video_published_at, video_url
        else:
            return None, None, None
    except HttpError as e:
        print(f"Error: {e}")
        return None, None, None


def format_number(number):
    """
    Formats a number with comma separators.

    :param number: (int) The number to format
    :return: (str) The formatted number as a string
    """
    return "{:,}".format(number)


def get_details_channel_info(language=None, channel_name=None):
    """
    Retrieves and displays detailed information about a YouTube channel.

    :param language: (str, optional) The language code for output ('EN' or 'FR')
    :param channel_name: (str, optional) The name of the channel to search for
    :return: (dict) A dictionary containing all the retrieved channel information
    """
    if language is None:
        language = select_language()

    if channel_name is None:
        channel_name = input(translate_message('enter_channel_name', language))

    channel_id = None
    channel_title = None
    description = None
    subs_count = None
    view_count = None
    video_count = None
    created_at = None

    video_title = None
    video_published_at = None
    video_url = None

    if channel_name:
        channel_id = search_channel(channel_name)

        if channel_id:
            channel_title, description, subs_count, view_count, video_count, created_at = get_channel_info(channel_id)
            if channel_title:
                print(f"\n{translate_message('channel_info', language)} '{channel_title}':")
                print(f"{translate_message('description', language)} {description}")
                print(f"{translate_message('subscribers', language)} {format_number(subs_count)}")
                print(f"{translate_message('views', language)} {format_number(view_count)}")
                print(f"{translate_message('total_videos', language)} {format_number(video_count)}")
                print(f"{translate_message('created_at', language)} {created_at}")
                print(f"{translate_message('on_youtube_since', language)} {created_at[:10]}")

                video_title, video_published_at, video_url = get_latest_video_info(channel_id)
                if video_title:
                    print(f"\n{translate_message('latest_video', language)}")
                    print(f"{translate_message('title', language)} {video_title}")
                    print(f"{translate_message('published_at', language)} {video_published_at}")
                    print(f"{translate_message('url', language)} {video_url}")

                else:
                    print(f"\n{translate_message('no_video_found', language)}")
            else:
                print(f"\n{translate_message('invalid_channel', language)}")
        else:
            print(f"\n{translate_message('invalid_channel', language)}")

    return {
        "Channel Name": channel_name,
        "Channel ID": channel_id,
        "Channel Title": channel_title,
        "Description": description,
        "Subscribers": subs_count,
        "Views": view_count,
        "Total Videos": video_count,
        "Created At": created_at,
        "Latest Video Title": video_title,
        "Published At": video_published_at,
        "Latest_Video URL": video_url
    }


if __name__ == "__main__":
    print(get_details_channel_info())
