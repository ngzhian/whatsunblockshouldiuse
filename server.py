import re
import os
import json

from io import StringIO

from bottle import static_file, request, run, route
from bs4 import BeautifulSoup

import requests


# Read port selected by the cloud for our application
PORT = int(os.getenv('VCAP_APP_PORT', 8080))

if os.getenv("VCAP_SERVICES"):
    services = json.loads(os.getenv("VCAP_SERVICES"))
    service_name = 'question_and_answer';
    if services and services[service_name]:
        svc = services[service_name][0]['credentials'];
        svc_url = svc['url']
        svc_username = svc['username'];
        svc_password = svc['password'];
        print(svc_url, svc_username, svc_password)

EPA_URL = 'http://iaspub.epa.gov/enviro/m_uv?'
EPA_URL_FORMAT = EPA_URL + 'lat={lat}&lon={lon}'
CACHE = {}

@route('/')
def index():
    return static_file('index.html', root='static')

@route('/uv')
def uv():
    print(CACHE)
    url = EPA_URL_FORMAT.format(lat=request.query.lat, lon=request.query.lon)
    if url in CACHE:
        print('Cache hit')
        return CACHE.get(url)

    response = requests.get(url).text
    index, level, desc = extract_index_level_desc(response)
    results = {'index': index, 'level': level, 'desc': desc}

    CACHE[url] = results
    return results

@route('/ask')
def ask():
    question = request.forms.get('ask') or request.query.get('ask')
    if not question:
        return {}
    answer = ask_watson(question)
    return {'answer': answer}

def extract_index_level_desc(contents):
    soup = BeautifulSoup(contents)
    content = soup.find(id="content")
    uv_index_line = content.b
    img_tag = content.findAll('img')[-1]
    image_url = img_tag.attrs['src']
    desc = list(list(img_tag.children)[-1].children)[0]
    index, level = uv_index_level(image_url)
    return index, level, desc

def uv_index_level(url):
    """Example url:
    http://www.epa.gov/enviro/facebook/img/iphone/UV_Index_4_Moderate.png
    """
    pattern = re.compile(r'[/._]')
    components = re.split(pattern, url)
    index = components[-3]
    level = components[-2].lower()
    return index, level

def get_location_text(uv_index_line):
    pattern = re.compile(r'<[Ii]>[^<]+</[Ii]>')
    location = pattern.search(uv_index_line).group(0)[3:-4]
    return location


@route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root='static')

@route('/favicon.ico')
def favicon():
    return static_file('favicon.ico', root='')

def ask_watson(question):
    question = question.strip()
    USERNAME = 'd83e357f-9b61-4bcb-b44b-46f934606d12'
    PASSWORD = 'aIpNYMrmSIup'
    URL = 'https://gateway.watsonplatform.net/question-and-answer-beta/api/v1/question/healthcare'

    print('Asking watson', question)

    response = requests.post(
        URL,
        json={'question': {'questionText': question}},
        headers={
            'Accept': 'application/json',
            'X-SyncTimeout': 30,
        },
        auth=(USERNAME, PASSWORD))
    return response.json()

if __name__ == '__main__':
    run(host='0.0.0.0', port=PORT, debug=True, reloader=True)
