import argparse
import requests
import time
import sys

def set(url, value):
    put_req = requests.put(url, json=args.value)
    time.sleep(1)
    get_req = requests.get(url)

    return get_req.json() == value

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("switch", help="Switch name")
    parser.add_argument("value", type=int, help="Switch value")
    parser.add_argument("--address", "-a", help="Controller IP address", default="rpi")
    parser.add_argument("--port", "-p", help="Controller port", default=5000)
    parser.add_argument("--retries", type=int, help="Number of retries", default=3)
    parser.add_argument("--delay", type=int, help="Delay between retries (s)", default=10)
    args = parser.parse_args()

    url = f"http://{args.address}:{args.port}/api/switch/{args.switch}"

    for i in range(args.retries - 1):
        if set(url, args.value):
            sys.exit(0)

        print("Retrying...", file=sys.stderr)
        time.sleep(args.delay)

    if not set(url, args.value):
        print(f"Failed to set {args.switch} to value {args.value}", file=sys.stderr)
        sys.exit(1)
