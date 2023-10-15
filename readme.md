HKID and Address Extraction using Google Cloud Vision API

 This script extracts information from an image of a Hong Kong Identity Card (HKID) and an address proof letter. It utilizes the Google Cloud Vision API for Optical Character Recognition (OCR) and performs data validation on the extracted HKID information.

Before running the script, make sure you have the following:

1)Python Environment: The script is developed using Python 3.8.
2)Tocken file: Ensure you have the ServiceAccountToken.json file for authentication(which was already provided in the same file)
3)Conda Environment: It's recommended to create a Conda environment to manage dependencies. You can use the environment.yml file to recreate the environment. 
    To create the environment, run:
    conda env create -f environment.yml
    conda activate myenv

run google_api.py file to start



