import requests
from collections import deque
import time
import random


class RateLimiter:
    def __init__(self, max_calls, period):
        self.calls = deque()
        self.max_calls = max_calls
        self.period = period  # en segundos

    def wait(self):
        current = time.time()
        while self.calls and self.calls[0] <= current - self.period:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (current - self.calls[0])
            # Añadir jitter
            wait_time = wait_time / 2 + random.uniform(0, wait_time / 2)
            print(f"Rate limit alcanzado. Esperando {wait_time:.2f} segundos.")
            time.sleep(wait_time)
        self.calls.append(time.time())


def get_link_next(link_header: str):
    header_links = link_header.split(',')
    url = None
    for link in header_links:
        if 'rel="next"' in link:
            start = link.find('<') + 1
            end = link.find('>')
            if start > 0 and end > start:
                url = link[start:end]
            break
    return url


api_version = '2023-07'
api_key = "*****"
password = "*****"
store_url = "*****"
base_url = f"https://{store_url}/admin/api/{api_version}"
headers = {
    'Content-Type': 'application/json',
    'X-Shopify-Access-Token': password
}
session = requests.Session()
rate_limiter = RateLimiter(max_calls=4, period=1)
url = f"{base_url}/inventory_levels.json"
params = {
    'inventory_item_ids': '43574186508333,43660062982189,43660063014957,43660063047725,43748969742381,43748969775149,43748969807917,43748969840685,43753611231277,43768682446893,43768682479661,43822381531181,43822381563949,43574186541101,43660063080493,43660063113261,43660063146029,43748969873453,43748969906221,43748969938989,43748969971757,43753611264045,43768682512429,43768682545197,43822381596717,43822381629485,43574186573869,43660063178797,43660063211565,43660063244333,43748970004525,43748970037293,43748970070061,43748970102829,43753611296813,43768682577965,43768682610733,43822381662253,43822381695021,43574186606637,43660063277101,43660063309869,43660063342637,43748970135597,43748970168365,43748970201133,43748970233901,43753611329581,43768682643501,43768682676269,43822381727789,43822381760557,43574186639405,43660063375405,43660063408173,43660063440941,43748970266669,43748970299437,43748970332205,43748970364973,43753611362349,43768682709037,43768682741805,43822381793325,43822381826093,43574186672173,43660063473709,43660063506477,43660063539245,43748970397741,43748970430509,43748970463277,43748970496045,43753611395117,43768682774573,43768682807341,43822381858861,43822381891629,44943358885933,44943358918701,44943358951469,44943358984237,44943359017005,44943359049773,44943359082541,44943359115309,44943359148077,44943359180845,44943359213613,44943359246381,44943359279149,44943411314733,44943411347501',
    'limit': 250
}
inventory = []


while url:
    rate_limiter.wait()
    response = session.get(url, headers=headers, params=params)
    # log_api_call(response)
    link_header = None
    if response.status_code == 200:
        data = response.json()
        fetched_inventory = data.get('inventory_levels', [])
        inventory.extend(fetched_inventory)
        print("inventory-len0", len(inventory))
        link_header = response.headers.get('Link')
        # print("response.headers-->", response.headers)
    if link_header:
        url = get_link_next(link_header)
        params = None
    else:
        url = None

# print("inventory", inventory)
print("inventory-len", len(inventory))
