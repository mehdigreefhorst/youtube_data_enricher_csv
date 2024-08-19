import os
import json
import pandas as pd
import time
from youtube_transcript_api import YouTubeTranscriptApi
import re


def get_video_id_from_youtube_link(youtube_link):
    """
    Extracts the video ID from a YouTube link.

    :param youtube_link: (str) The YouTube video URL
    :return: (str) The extracted video ID
    """
    video_id = re.search(r'(?<=v=)[^&]+', youtube_link)

    if '?' in youtube_link:
        location_split = youtube_link.find('?')
        video_id = youtube_link[:location_split]
        #return video_id
    if "youtu." in youtube_link:
        url = youtube_link.split('youtu.')[1]
        index_start_id = url.find('/') + 1
        video_id_with_extra_random_characters = url[index_start_id:]

        #replace everything that starts with % or & or ? or #
        video_id = ""
        for i, char in enumerate(video_id_with_extra_random_characters):
            if char in ['%', '&', '?', '#']:
                break
            else:
                video_id += char
        #return video_id
    if video_id:
        return video_id
    else:
        return None


def get_important_video_data(video_id_or_url):
    """
    Retrieves important data for a YouTube video.

    :param video_id_or_url: (str) The YouTube video ID or URL
    :return: (dict) Dictionary containing important video data
    """
    if 'youtube.com' in video_id_or_url or 'youtu.be' in video_id_or_url:
        video_id = get_video_id_from_youtube_link(video_id_or_url)
    else:
        video_id = video_id_or_url

    try:
        transcript_list, (audio_track_list, video_meta_data) = YouTubeTranscriptApi.list_transcript_audio_tracks(
            video_id)

        available_languages = [info.language for info in transcript_list]
        available_audiotracks = [language for language in audio_track_list]

        views = get_video_views(video_meta_data).get('views')
        title = get_title_from_video_meta_data(video_meta_data).get('title')

        return {
            'video_id': video_id,
            'available_languages': available_languages,
            'available_audiotracks': available_audiotracks,
            'views': views,
            'title': title
        }
    except Exception as e:
        print(f"Error retrieving data for video {video_id}: {e}")
        return {
            'video_id': video_id,
            'available_languages': None,
            'available_audiotracks': None,
            'views': None,
            'title': None
        }


def get_video_views(video_meta_data):
    """
    Extracts the view count from video metadata.

    :param video_meta_data: (str) Metadata of the video
    :return: (dict) Dictionary containing the view count
    """
    try:
        views_start_meta_data = video_meta_data.split('"metadata":{"simpleText":')[1]
        views_end_index = views_start_meta_data.find(" views")
        views = views_start_meta_data[:views_end_index]
        views = re.sub(r'\D', '', views)
        return {'views': int(views)}
    except Exception as e:
        print(f"Error extracting video views: {e}")
        return {'views': None}


def get_title_from_video_meta_data(video_meta_data):
    """
    Extracts the title from video metadata.

    :param video_meta_data: (str) Metadata of the video
    :return: (dict) Dictionary containing the video title
    """
    try:
        title_start_meta_data = video_meta_data.split('{"accessibilityData":{"label":')[1]
        title_end_index = title_start_meta_data.find("}")
        title = title_start_meta_data[:title_end_index]
        return {'title': title}
    except Exception as e:
        print(f"Error extracting video title: {e}")
        return {'title': None}


def add_new_columns_to_df(df, video_link_columns, channel_name_column, starting_row_index=0):
    """
    Adds new columns to the DataFrame with YouTube video and channel data, using caching for efficiency.

    :param df: (pandas.DataFrame) The input DataFrame
    :param video_link_columns: (list) List of column names containing video links
    :param channel_name_column: (str) Name of the column containing channel names
    :param starting_row_index: (int) The index to start processing from
    :return: (pandas.DataFrame) The updated DataFrame with new columns
    """
    df_copy = df.copy()
    cache_folder = "cached_data"
    os.makedirs(cache_folder, exist_ok=True)

    def get_cached_data(cache_type, identifier):
        """Helper function to get or create cached data"""
        filename = os.path.join(cache_folder, f"{cache_type}_{identifier.replace('/', '_')}.json")

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()
                return json.loads(content)

        return None

    def save_cached_data(cache_type, identifier, data):
        """Helper function to save data to cache"""
        filename = os.path.join(cache_folder, f"{cache_type}_{identifier.replace('/', '_')}.json")
        with open(filename, 'w') as f:
            json.dump(data, f)

    # Initialize new columns
    for column in video_link_columns:
        new_columns = [
            f"video_id_{column}",
            f"available_languages_{column}",
            f"available_audiotracks_{column}",
            f"views_{column}",
            f"title_{column}"
        ]
        for new_column in new_columns:
            df_copy[new_column] = pd.NA

    for index, row in df_copy.iloc[starting_row_index:].iterrows():
        # Process video data
        for column in video_link_columns:
            video_link = row[column]
            if pd.notna(video_link):
                video_id = get_video_id_from_youtube_link(video_link)
                video_data = get_cached_data('video', video_id)

                if video_data is None:
                    video_data = get_important_video_data(video_link)
                    save_cached_data('video', video_id, video_data)
                    time.sleep(5)  # Delay for API rate limiting

                for key, value in video_data.items():
                    column_name = f"{key}_{column}"
                    if column_name in df_copy.columns:
                        df_copy.at[index, column_name] = value

    return df_copy

if __name__ == "__main__":
    print(get_video_id_from_youtube_link("https://youtu.be/mNfqAHZM-x4"))