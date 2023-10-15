import sys
# sys.path.append('/Users/carol/opt/anaconda3/envs/osl_py38/lib/python3.8/site-packages')
import requests
import os
import cv2
import numpy as np
import json
import re
from google.cloud import vision
from google.cloud.vision_v1 import ImageAnnotatorClient
from tabulate import tabulate
from PIL import Image

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'./ServiceAccountToken.json'

client = vision.ImageAnnotatorClient()

def download_file_from_google_drive(id, destination):
    URL = f"https://drive.google.com/uc?id={id}"
    CHUNK_SIZE = 32768
    try:
        with requests.get(URL, stream=True) as response:
            response.raise_for_status()
            with open(destination, "wb") as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
        print(f"Download successful: {destination}")
    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
        print("Download failed.")
    except Exception as err:
        print(f"Error: {err}")
        print("Download failed.")

def save_file(file_id, name):
    current_directory = os.getcwd()
    destination = os.path.join(current_directory, name)
    print(f"Download {file_id} to {destination}")
    download_file_from_google_drive(file_id, destination)
    img = cv2.imread(destination)
    return img

def remove_noise(img):
    # print("showing image:press '0' to close window ")
    # print('image shape(HKID)' + str(img.shape))
    blur = cv2.bilateralFilter(img, 9, 75, 75)
    sharpening_kernel = np.array([[-1, -1, -1],
                                  [-1, 9, -1],
                                  [-1, -1, -1]])
    sharpened_img = cv2.filter2D(blur, -1, sharpening_kernel)
    return sharpened_img

def extract_text_from_image(img):
    rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    _, encoded_image = cv2.imencode('.png', rgb_image)
    content = encoded_image.tobytes()
    image = vision.Image(content=content)
    image_context = vision.ImageContext(language_hints=["en", "zh"])
    response = client.text_detection(image=image, image_context=image_context)
    texts = response.text_annotations
    # extracted_text = texts[0].description
    # print("---description---"+str(texts[0].description)+"---description---")
    extracted_text = ""
    for text in texts:
        extracted_text += text.description + " "
    # return extracted_text.strip()
    return texts[0].description ,extracted_text.strip()


def verify_hkid(hkid):
    str_valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if len(hkid) < 8:
        return False
    hkid = hkid.upper()
    hkid_pat = r'^([A-Z]{1,2})([0-9]{6})([A0-9])$'
    match_array = re.match(hkid_pat, hkid)
    if match_array is None:
        return False
    char_part, num_part, check_digit = match_array.groups()
    check_sum = 0
    if len(char_part) == 2:
        check_sum += 9 * (10 + str_valid_chars.index(char_part[0]))
        check_sum += 8 * (10 + str_valid_chars.index(char_part[1]))
    else:
        check_sum += 9 * 36
        check_sum += 8 * (10 + str_valid_chars.index(char_part))
    for i in range(len(num_part)):
        check_sum += (7 - i) * int(num_part[i])
    remaining = check_sum % 11
    verify = 0 if remaining == 0 else 11 - remaining
    return verify == 10 if check_digit == 'A' else verify == int(check_digit)

def extract_name_and_hkid(extracted_text):
    hkid_pattern = r'\([A-Z]+\)|[A-Z]{1}\d{6}'
    name_pattern = r'([\u4e00-\u9fa5\s]+|[A-Za-z\s]+)'
    cleaned_text = extracted_text.replace("香港永久性居民身份證", "").replace("HONG KONG PERMANENT IDENTITY CARD", "").replace("SAMPLE","")
    # print("****cleaned text****"+str(cleaned_text)+"\n****cleaned text****")
    cleaned_text_lines = cleaned_text.split('\n')
    # print("****cleaned text****"+str(cleaned_text_lines)+"\n****cleaned text****")

    name_matches = re.findall(name_pattern, cleaned_text)

    hkid = cleaned_text_lines[-1]
    chinese_name = name_matches[0].strip() if name_matches else None
    for idx, line in enumerate(cleaned_text_lines):
        if chinese_name and chinese_name in line and idx + 1 < len(cleaned_text_lines):
            english_name = cleaned_text_lines[idx + 1]

    return chinese_name, english_name, hkid



def extract_address(extracted_text):
    extracted_text = extracted_text.split('\n')
    keywords = ['flat', 'room', 'floor']
    stop_keywords = ['NT', 'HK', 'KW']
    found_items = []

    for index, line in enumerate(extracted_text):
        # Check if the line starts with any of the specified keywords
        if any(keyword in line.lower() for keyword in keywords):
            # Check if the entire line is in uppercase
            if line.strip().isupper():
                address_lines = [line]  # Initialize address lines with the first line
                # Continue adding lines to the address until a stop keyword is encountered
                for i in range(index + 1, len(extracted_text)):
                    next_line = extracted_text[i].strip()
                    address_lines.append(next_line)
                    if any(stop_keyword in next_line.upper() for stop_keyword in stop_keywords):
                        break
                # Join address lines into a single string
                address_string = '\n'.join(address_lines)
                found_items.append(address_string)

    print("+---------address-----------+")
    print(found_items)
    print("+---------address-----------+")
    return found_items


def main():

    hkid_img = save_file('1RNpnIpWD0SfejIZgP6osVG4W3xU7UJCG', 'HKID.png')
    address_img = save_file('1o20DmvcsqV1qzPkllxjIIvIhX_XRPxPc', 'Address.jpg')
    processed_hkid_img = remove_noise(hkid_img)
    processed_address_img = remove_noise(address_img)
    extracted_key_text ,extracted_full_text= extract_text_from_image(processed_hkid_img)
    address_key_text ,address_full_text= extract_text_from_image(processed_address_img)
    address = extract_address(address_key_text)
    address_list = extract_address(address_key_text)
    address_string = '\n'.join(address_list)

    chinese_name, english_name, hkid = extract_name_and_hkid(extracted_key_text)
    hkid = hkid.replace(" ","").replace(")","").replace("(","")
    is_hkid_text_valid = verify_hkid(hkid)

    extracted_data = {
        "chinese_name": chinese_name,
        "english_name": english_name,
        "hkid": hkid,
        "is_hkid_text_valid": is_hkid_text_valid
    }
    json_data = json.dumps(extracted_data)

    extracted_full_data = {
        "extracted_full_text": extracted_full_text
    }
    json_full_data = json.dumps(extracted_full_data)
#saving file to jason
    with open('hkid_data.json', 'w') as json_file:
        json_file.write(json_full_data)
    
    with open('address_data.json', 'w') as json_file:
        json_file.write(address_string)

    with open('address_full_data.json', 'w') as json_file:
        json_file.write(address_full_text)

    print("Extracted full data :"+str(extracted_full_data))
    print("***Extracted Data (JSON) saved to 'hkid_data.json'***")
    table = tabulate([json.loads(json_data)], headers='keys', tablefmt='pretty')
    print("Extracted Data (name,hkid)(JSON Table):")
    print(table)


if __name__ == "__main__":
    main()
