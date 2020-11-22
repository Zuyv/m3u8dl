#!/usr/bin/env python3

import os
import re
import json
import requests
from http import HTTPStatus
from Crypto.Cipher import AES
from concurrent.futures import ThreadPoolExecutor

class Video():
    def __init__(self, name, key_url, ts0_url):
        url_pattern = r"https://vod\.study\.163\.com/video/(\d+)/hls/key\?token=([0-9a-f]+)"
        self.name = name
        self.params = {}
        self.params["id"], self.params["token"] = re.fullmatch(url_pattern, key_url).groups()
        self.ts0_url_prefix, = re.fullmatch(r"(https://.*)\d+\.ts", ts0_url).groups()
        self.ts0_fname, = re.fullmatch(r"https://.*/(.*\d+\.ts)", ts0_url).groups()
        index, = re.fullmatch(r".*?(\d+)\.ts", self.ts0_fname).groups()
        assert int(index) == 0, f"{index}"

    def get_max_ts_index(self):
        def ts_exist(index, retry=0):
            url = f"{self.ts0_url_prefix}{index}.ts"
            assert retry <= 3
            try:
                with requests.get(url, timeout=60) as response:
                    if response.status_code == HTTPStatus.OK:
                        return True
                    elif response.status_code == HTTPStatus.NOT_FOUND:
                        return False
                    assert 0
            except:
                return ts_exist(index, retry + 1)

        step = 500
        l_index = 0
        h_index = 1000
        while ts_exist(h_index):
            h_index += step
        while True:
            m_index = (l_index + h_index) // 2
            if ts_exist(m_index):
                if m_index == h_index - 1:
                    return m_index
                l_index = m_index
            else:
                if m_index == l_index + 1:
                    return l_index
                h_index = m_index

    def get_ts_file(self, index, fname_prefix="", retry=0):
        url = f"{self.ts0_url_prefix}{index}.ts"
        ts_fname = f"{fname_prefix}{index}.ts"

        if retry > 3:
            return HTTPStatus.REQUEST_TIMEOUT

        try:
            with requests.get(url, timeout=60) as response:
                if not response:
                    return response.status_code
                assert response.status_code == HTTPStatus.OK
                data = response.content
                if self.cipher:
                    data = self.cipher.decrypt(data)
        except requests.exceptions.RequestException as exception:
            print(f"{exception}\nretry = {retry}, url = {url}")
            return self.get_ts_file(index, retry + 1)

        with open(ts_fname, "wb") as ts_file:
            ts_file.write(data)

        print(f"Download complete: {self.name} [No. {index}]")
        return response.status_code

    def get_video(self, thread=1):
        assert type(thread) == int and thread >= 1
        key_url= "https://vod.study.163.com/eds/api/v1/vod/hls/key"
        executor = ThreadPoolExecutor(thread)
        max_ts_index = self.get_max_ts_index()

        with requests.get(key_url, params=self.params) as response:
            key = response.content
            assert len(key) == 16
            self.cipher = AES.new(key, AES.MODE_CBC, b"\x00" * 16)

        for index in range(max_ts_index + 1):
            executor.submit(self.get_ts_file, index, f"{self.name}_")
        executor.shutdown()

        with open(f"{self.name}.ts", "wb") as ofile:
            for i in range(max_ts_index + 1):
                fname = f"{self.name}_{i}.ts"
                with open(fname, "rb") as ifile:
                    while True:
                        chunk = ifile.read(65536)
                        if not chunk:
                            break
                        ofile.write(chunk)
                os.remove(fname)

