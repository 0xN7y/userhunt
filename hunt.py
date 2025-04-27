import argparse
import requests
import yaml
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from colorama import Fore, Style, init

init(autoreset=True)


def load_(config_path):
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            return data.get('platforms', [])
    except Exception as e:
        print(f"{Fore.RED}[!] Error loading configuration: {e}")
        sys.exit(1)


def check_uname(platform, username, session, proxies=None):
    url = platform['url'].format(username=username)
    try:
        response = session.get(url, proxies=proxies, timeout=10)
        if response.status_code == 200:
            return (platform['name'], url, True)
        elif response.status_code == 404:
            return (platform['name'], url, False)
        else:
            return (platform['name'], url, None)
    except requests.RequestException:
        return (platform['name'], url, None)


def main():
    parser = argparse.ArgumentParser(description="UserHunt: Search for usernames across social media platforms.")
    parser.add_argument("username", help="Username to search for")
    parser.add_argument("--config", default="./config/platforms.yaml", help="Path to YAML configuration file")
    parser.add_argument("--tor", action="store_true", help="Route traffic through Tor network")
    parser.add_argument("--proxy", help="Specify a proxy (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--output", help="Output file to save results")
    parser.add_argument("--threads", type=int, default=10, help="Number of concurrent threads")
    args = parser.parse_args()


    proxies = None
    if args.tor:
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
    elif args.proxy:
        proxies = {
            'http': args.proxy,
            'https': args.proxy
        }


    platforms = load_(args.config)
    if not platforms:
        print(f"{Fore.RED}[!] No platforms found in the configuration file.")
        sys.exit(1)


    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/n7y (Windows NT 10.0; Win64; x64)'
    }
    session.headers.update(headers)


    print(f"{Fore.CYAN}[+] Starting scan for username: {args.username}")
    results = []
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        future_to_platform = {
            executor.submit(check_uname, platform, args.username, session, proxies): platform
            for platform in platforms
        }
        for future in tqdm(as_completed(future_to_platform), total=len(platforms), desc="Scanning", ncols=100):
            platform_name, url, exists = future.result()
            if exists is True:
                print(f"{Fore.GREEN}[FOUND] {platform_name}: {url}")
                results.append((platform_name, url, "FOUND"))
            elif exists is False:
                print(f"{Fore.RED}[NOT FOUND] {platform_name}: {url}")
                results.append((platform_name, url, "NOT FOUND"))
            else:
                print(f"{Fore.YELLOW}[UNKNOWN] {platform_name}: {url}")
                results.append((platform_name, url, "UNKNOWN"))

    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                for platform_name, url, status in results:
                    f.write(f"{status}: {platform_name}: {url}\n")
            print(f"{Fore.CYAN}[+] Results saved to {args.output}")
        except Exception as e:
            print(f"{Fore.RED}[!] Error saving results: {e}")

if __name__ == "__main__":
    main()
