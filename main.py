#!/usr/bin/env python3

import json
from video import Video

def main():
    with open("index.json", "r") as ifile:
        video_dict_list = json.load(ifile)
    for video_dict in video_dict_list:
        video = Video(video_dict["name"], video_dict["key_url"], video_dict["ts0_url"])
        video.get_video(10)

if __name__ == "__main__":
    main()
