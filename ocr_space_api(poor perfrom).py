import io
import json
import cv2
import numpy as np
import requests
import os
import cv2

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

def save_file(file_id,name):
    current_directory = os.getcwd()  # Get the current working directory
    destination = os.path.join(current_directory, name)  # Save the file in the current directory with the name "images.png"
    print(f"Download {file_id} to {destination}")
    download_file_from_google_drive(file_id, destination)
    img = cv2.imread(destination)
    return img


def remove_noise(img):
    print("showing image:press '0' to close window " )
    print(img.shape)
    blur = cv2.bilateralFilter(img,9,75,75)	
    # Apply sharpening filter to enhance edges
    sharpening_kernel = np.array([[-1, -1, -1],
                                  [-1, 9, -1],
                                  [-1, -1, -1]])
    sharpened_img = cv2.filter2D(blur, -1, sharpening_kernel)
    
    cv2.imshow('gray img',sharpened_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows
    return sharpened_img

def main():
    img_hkid = save_file('1RNpnIpWD0SfejIZgP6osVG4W3xU7UJCG', 'HKID')
    img = remove_noise(img_hkid)
    # Cutting image
    height, width, _ = img.shape
    roi = img[0: height, 400: width]

    url_api = "https://api.ocr.space/parse/image"
    _, compressed_image = cv2.imencode(".png", roi, [1, 90])
    file_bytes = io.BytesIO(compressed_image)
    result = requests.post(url_api,
                           files={"HKID.png": file_bytes},
                           data={"apikey": "K88067149888957",
                                 "language": "eng"})
    
    print("API Response:")
    print(result.text)  # Print API response for debugging purposes
    
    result = result.content.decode()
    result = json.loads(result)
    
    parsed_results = result.get("ParsedResults", [])
    if parsed_results:
        text_detected = parsed_results[0].get("ParsedText")
        print("Text detected:\n")
        print(text_detected)
    else:
        print("No valid results returned from the API.")

if __name__ == "__main__":
    main()

