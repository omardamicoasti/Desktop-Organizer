import os
import shutil
import getpass
import re
import yaml
import logging
from pathlib import Path
from datetime import datetime

# Configuring logging
logging.basicConfig(filename='organize_desktop.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Clean the name of the file from special characters and whitespaces
def clean_name(item, date_format_picked):
    # Get creation time of the file in the format we picked
    formatted_creation_time = datetime.fromtimestamp(os.stat(item).st_ctime).strftime(f'_{date_format_picked}')
    stem, ext = os.path.splitext(item.name)
    if item.name.__contains__(formatted_creation_time):
        end_of_file = ext
    else:
        end_of_file = formatted_creation_time + ext
    return (re.sub(r'[_\s-]+', '_', stem)).replace(" ", "_").replace("-", "_").lower() + end_of_file


# Clean the name of the folder from special characters and whitespaces
def clean_dir_name(item):
    return (re.sub(r'[_\s-]+', '_', item.strip())).replace(" ", "_").replace("-", "_").capitalize()

# Function to generate a unique name
def generate_unique_name(file_name, folder):
    counter = 0
    new_name = file_name
    stem, ext = os.path.splitext(file_name)
    while (folder / new_name).exists():
        counter += 1
        if f"({counter})" in stem:
            new_stem = stem[:stem.rfind('(')] if stem.rfind('(') != -1 else stem
            new_name = f"{new_stem}_({counter}){ext}"
        else:
            new_name = f"{stem}_({counter}){ext}"
    return new_name


# Look for the desktop path checking the user and the OS language
def find_desktop_path():
    global desktop_path
    operating_system = read_running_mode_from_configuration_file("operating-sistem")
    print(f"Operating system: {operating_system}")
    if operating_system.upper() == "WINDOWS":
        for folder_name in ["Users", "Utenti"]:
            desktop_path = os.path.join("C:/", folder_name, getpass.getuser(), "Desktop")
    elif operating_system.upper() == "LINUX":
        desktop_path = os.path.join("/home", getpass.getuser(), "Scrivania")
    if os.path.exists(desktop_path):
        return Path(desktop_path)
    else:
        return None


# Read mode from YAML configuration file
def read_running_mode_from_configuration_file(parameter):
    script_directory = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_directory, 'organize_desktop.yml')
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
        return config['Settings'][parameter].upper()


# Organize files on desktop
def organize_files_on_desktop():

    global date_format_picked
    # Find desktop path
    desktop_path = find_desktop_path()
    if desktop_path is None:
        logging.error("Desktop path not found.")
        return

    # Identify the running mode if CUSTOM or DEFAULT
    mode = read_running_mode_from_configuration_file('mode')
    logging.info(f"Application running in {mode} mode.")

    # Ask user to input the name of the folder where to store files and define data formats
    if mode == "CUSTOM":
        main_folder = desktop_path / clean_dir_name(
            input("\nInserisci il nome della cartella dove contenere i tuoi file : "))
        date_format_input = input(
            "\n\n1 - giorno / mese / anno"
            "\n2 - anno / mese / giorno"
            "\n3 - mese / giorno / anno"
            "\n4 - anno / giorno  /mese\n\n"
            "Scegli un formato di data da utilizzare (1,2,3,4 - default 1): ")
    else:
        main_folder = desktop_path / clean_dir_name(read_running_mode_from_configuration_file('main_folder'))
        date_format_input = "1"
    logging.info(f"Main folder created with name: {main_folder}")

    # If folder does not exist, create it
    if not main_folder.exists():
        main_folder.mkdir()

    # Check if the input is valid and select the date format accordingly
    date_formats = ['%d_%m_%Y', '%Y_%m_%d', '%m_%d_%Y', '%Y_%d_%m']
    if date_format_input in ["1", "2", "3", "4"]:
        date_format_picked = date_formats[int(date_format_input) - 1]
        today_folder = main_folder / datetime.today().strftime(date_format_picked)
    else:
        today_folder = main_folder / datetime.today().strftime(date_formats[0])


    # If today's folder does not exist, create it
    if not today_folder.exists():
        today_folder.mkdir()

    logging.info(f"Today folder: {today_folder}")

    # Iterate over files in desktop
    files_to_move = []
    for item in desktop_path.iterdir():
        if item.is_file() and item.suffix.lower() not in ['.lnk', '.cmd']:
            if (today_folder / clean_name(item, date_format_picked)).exists():
                # If a file with the same name already exists, generate a unique name
                Path.rename(item, today_folder / generate_unique_name(item.name, today_folder))
            else:
                Path.rename(item, today_folder / clean_name(item, date_format_picked))
            files_to_move.append(item)

    # Move files to today's folder
    if files_to_move.__sizeof__() > 0:
        for file_path in files_to_move:
            try:
                logging.info(f"File {file_path} moved to {today_folder}")
                if (today_folder / file_path.name).exists():
                    # If a file with the same name already exists, generate a unique name
                    file_path.rename(today_folder / generate_unique_name(file_path.name, today_folder))
                    shutil.move(str(file_path), str(today_folder))
                else:
                    shutil.move(str(file_path), str(today_folder))
            except FileNotFoundError:
                logging.error(f"File {file_path} not found")
                pass


# Tidy up your messy desktop!
organize_files_on_desktop()
