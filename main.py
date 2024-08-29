import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from youtube_channel_info_retriever import get_details_channel_info
from youtube_video_enricher import add_new_columns_to_df
import json


def select_file():
    """
    Opens a file dialog for the user to select a CSV file.

    :return: (str) The path of the selected file
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    return file_path


def map_columns(df):
    """
    Prompts the user to map columns in the DataFrame.

    :param df: (pandas.DataFrame) The input DataFrame
    :return: (tuple) Lists of video link columns and the channel name column
    """
    print("Available columns:")
    for i, col in enumerate(df.columns):
        print(f"{i + 1}. {col}")

    video_link_columns = []
    while True:
        col_num = input("Enter the number of a column containing video links (or press Enter to finish): ")
        if col_num == "":
            break
        try:
            col_num = int(col_num) - 1
            if 0 <= col_num < len(df.columns):
                video_link_columns.append(df.columns[col_num])
            else:
                print("Invalid column number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    channel_name_column = ""
    while True:
        col_num = input("Enter the number of the column containing channel names: ")
        try:
            col_num = int(col_num) - 1
            if 0 <= col_num < len(df.columns):
                channel_name_column = df.columns[col_num]
                break
            else:
                print("Invalid column number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    print(f"Video link columns: {video_link_columns}")
    print(f"Channel name column: {channel_name_column}")

    return video_link_columns, channel_name_column


def save_file(df):
    """
    Prompts the user to select a location to save the enriched DataFrame.

    :param df: (pandas.DataFrame) The enriched DataFrame to save
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        df.to_csv(file_path, index=False)
        print(f"File saved successfully at: {file_path}")
    else:
        print("File not saved.")


def add_channel_data_to_df(df, channel_name_column):
    """
    Adds channel data to the DataFrame, using caching for efficiency.

    :param df: (pandas.DataFrame) The input DataFrame
    :param channel_name_column: (str) Name of the column containing channel names
    :return: (pandas.DataFrame) The updated DataFrame with new channel data columns
    """
    cache_folder = "cached_channels"
    os.makedirs(cache_folder, exist_ok=True)

    def get_cached_channel_info(channel_name):
        """Helper function to get or create cached channel info"""
        filename = os.path.join(cache_folder, f"{channel_name.replace(' ', '_').lower()}.json")

        if os.path.exists(filename):
            with open(filename, 'r') as f:
                json_data = json.load(f)

                if json_data and json_data.get("Channel ID", None) is not None:
                    print("I used my cached system")
                    return json_data

                #return json.load(f)

        channel_info = get_details_channel_info(channel_name=channel_name, language="EN")

        if channel_info:
            with open(filename, 'w') as f:
                json.dump(channel_info, f)

        return channel_info

    # Get unique channel names to avoid redundant API calls
    unique_channels = df[channel_name_column].unique()

    # Create a dictionary to store channel data
    channel_data = {}

    # Fetch data for each unique channel
    for channel_name in unique_channels:
        if pd.notna(channel_name):
            channel_info = get_cached_channel_info(channel_name)
            if channel_info:
                channel_data[channel_name] = channel_info

    # Add new columns to the DataFrame
    if channel_data:
        # Get all possible keys from the channel data
        all_keys = set().union(*(d.keys() for d in channel_data.values()))
        latest_video_column_name = "Latest_Video URL"

        # Create new columns for each key
        for key in all_keys:
            col_name = f"{key}"
            df[col_name] = df[channel_name_column].map(lambda x: channel_data.get(x, {}).get(key, None))
    else:
        print("No channel data found.")
        latest_video_column_name = None

    return df, latest_video_column_name


def main():
    # Select input file
    input_file = select_file()
    if not input_file:
        print("No file selected. Exiting.")
        return
    print("Selected file:", input_file)

    # Read the CSV file
    df = pd.read_csv(input_file)

    # Map columns
    video_link_columns, channel_name_column = map_columns(df)

    # Add channel data to DataFrame
    channel_info_df, latest_video_column_name = add_channel_data_to_df(df, channel_name_column)

    # Enrich data
    if latest_video_column_name:
        print("latest_video_column_name : ", latest_video_column_name)
        video_link_columns.append(latest_video_column_name)
    print("channel_info_df columns : \n", channel_info_df.columns)

    print()
    print("video_link_columns : ", video_link_columns)

    enriched_df = add_new_columns_to_df(channel_info_df, video_link_columns, channel_name_column)

    # Save enriched data
    save_file(enriched_df)


if __name__ == "__main__":
    main()
