#!/usr/bin/env python
import requests
import time
import json
import os

# Konfiguration
DYNDNS_USER = "Benutzer"
DYNDNS_PASS = "Password"
DYNDNS_HOST = "example.de"
UPDATE_URL = "example.com/nic/update"

# Aktivierung von IPv4 und IPv6
ENABLE_IPV4 = True
ENABLE_IPV6 = True

# Intervall-Konfiguration
INITIAL_INTERVAL = 300  # 5 Minuten
MAX_INTERVAL = 3600     # 1 Stunde
MIN_INTERVAL = 300      # 5 Minuten
INCREASE_STEP = 300     # 5 Minuten
DECREASE_STEP = 60      # 1 Minute
STABILIZATION_COUNT = 5 # Anzahl der erfolgreichen Updates, um das Intervall zu stabilisieren

current_interval = INITIAL_INTERVAL
success_count = 0

# Pfad zur Speicherdatei
CACHE_FILE = "/home/pi/dyndns_cache.json"

def get_ipv4():
    response = requests.get("https://api.ipify.org")
    return response.text

def get_ipv6():
    response = requests.get("https://api64.ipify.org")
    return response.text

def update_dyndns(ipv4=None, ipv6=None):
    url = f"{UPDATE_URL}?hostname={DYNDNS_HOST}"
    if ipv4:
        url += f"&myip={ipv4}"
    if ipv6:
        if ipv4:
            url += f",{ipv6}"
        else:
            url += f"&myip={ipv6}"
    
    response = requests.get(url, auth=(DYNDNS_USER, DYNDNS_PASS))
    if "good" in response.text or "nochg" in response.text:
        return True
    else:
        return False

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    return {"ipv4": None, "ipv6": None}

def save_cache(ipv4, ipv6):
    with open(CACHE_FILE, 'w') as file:
        json.dump({"ipv4": ipv4, "ipv6": ipv6}, file)

def main():
    global current_interval, success_count
    cache = load_cache()
    last_ipv4 = cache.get("ipv4")
    last_ipv6 = cache.get("ipv6")

    while True:
        ipv4 = get_ipv4() if ENABLE_IPV4 else None
        ipv6 = get_ipv6() if ENABLE_IPV6 else None

        if ipv4 == last_ipv4 and ipv6 == last_ipv6:
            success_count += 1
            if success_count >= STABILIZATION_COUNT:
                current_interval = min(current_interval + INCREASE_STEP, MAX_INTERVAL)
                success_count = 0  # Reset the success count after stabilization
                print(f"No change detected. Increasing interval to {current_interval} seconds.")
        else:
            success = update_dyndns(ipv4=ipv4, ipv6=ipv6)
            if success:
                last_ipv4 = ipv4
                last_ipv6 = ipv6
                save_cache(last_ipv4, last_ipv6)
                success_count += 1
                if success_count >= STABILIZATION_COUNT:
                    current_interval = max(current_interval - DECREASE_STEP, MIN_INTERVAL)
                    success_count = 0  # Reset the success count after stabilization
                print(f"IP updated successfully. Current interval is {current_interval} seconds.")
            else:
                current_interval = min(current_interval + INCREASE_STEP, MAX_INTERVAL)
                success_count = 0
                print(f"Update failed. Increasing interval to {current_interval} seconds.")

        time.sleep(current_interval)

if __name__ == "__main__":
    main()
