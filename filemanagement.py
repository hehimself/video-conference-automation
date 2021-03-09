import glob
import os
import zipfile
import subprocess
import configparser
import serial
def teams_downloads_function(downloads_directory, directory_to_extract_to):
    downloads_directory = downloads_directory
    directory_to_extract_to = directory_to_extract_to
    list_of_files = glob.glob(downloads_directory) # * means all if need specific format then *.zip
    latest_file = max(list_of_files, key=os.path.getctime)

    with zipfile.ZipFile(latest_file,"r") as zip_ref:
        zip_ref.extractall(directory_to_extract_to)

    list_of_files = glob.glob(directory_to_extract_to + "/*")
    latest_file = max(list_of_files, key=os.path.getctime).replace("/","\\")
    subprocess.Popen(r'explorer /select, "{latest_file}"'.format(latest_file=latest_file))

if __name__ == "__main__":
    # downloads_directory = config['FILE_MANAGEMENT']['DOWNLOADS_DIRECTORY']
    # directory_to_extract_to = config['FILE_MANAGEMENT']['DIRECTORY_TO_EXTRACT_TO']
    # teams_downloads_function(downloads_directory, directory_to_extract_to)
    pass