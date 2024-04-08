import json
import urllib3
import certifi
import time

from django.conf import settings


http = urllib3.PoolManager(
    cert_reqs="CERT_REQUIRED",
    ca_certs=certifi.where()
)

def get_file_url(file, filename):
    try:
        url = "https://api.gladia.io/v2/upload"
        fields = {'audio': (filename, file.read())}

        encoded_fields, content_type = urllib3.filepost.encode_multipart_formdata(fields)


        headers = {
            "x-gladia-key": settings.GLADIA_API_KEY,
            "Content-Type": content_type
        }

        response = http.request(
            'POST',
            url,
            body=encoded_fields,
            headers=headers
        )

        if response.status == 200:
            data = response.json()
            file_url = data.get('audio_url', None)
            return file_url
        else:
            print(f"Error: Failed to upload file to Gladia.io. Response: {response.json()}")
            return None
    except Exception as e:
       print(f"Error: {str(e)}")
       return None


def get_result_url(file_url):
    url = "https://api.gladia.io/v2/transcription"

    payload = {
        "audio_url": file_url
    }

    headers = {
        "x-gladia-key": settings.GLADIA_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = http.request(
            'POST',
            url,
            body=json.dumps(payload),
            headers=headers
        )

        if response.status == 201:
            data = response.json()
            result_url = data.get('result_url')
            return result_url
        else:
            print(f"Error: Failed to generate result_url to Gladia.io. Response: {response.json()}")
            return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def get_transcription_text(result_url):
    headers = {
        "x-gladia-key": settings.GLADIA_API_KEY,
    }

    
    while True:
        try:
            response = http.request(
                'GET',
                result_url,
                headers=headers
            )

            if response.status == 200:
                data = json.loads(response.data.decode('utf-8'))
                if data.get('status') == 'done':
                    return data.get('result')
                else:
                    print(f"Transcription status is '{data.get('status')}'. Waiting...")
            else:
                print(f"Error: Failed to fetch transcription result from Gladia.io. Status code: {response.status}")

            time.sleep(60)
        except Exception as e:
            print(f"Error: {str(e)}")
            return None