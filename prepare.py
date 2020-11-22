#!/usr/bin/env python3

import json

def main():
    video_dict_list = []
    while True:
        name = input("Name: ")
        key_url = input("Key url: ")
        ts0_url = input("ts0_url: ")
        if not name and not key_url and not ts0_url:
            break
        video_dict = {
                "name": name,
                "key_url": key_url,
                "ts0_url": ts0_url
            }
        video_dict_list.append(video_dict)
    with open("index.json", "w") as ofile:
        json.dump(video_dict_list, ofile, indent='\t')
        print(json.dumps(video_dict_list, indent='\t'))

if __name__ == "__main__":
    main()
