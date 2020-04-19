#!/usr/bin/env python3

import re
import os
import argparse
import requests
from Crypto.Cipher import AES
from multiprocessing import Pool

def get_args():
	parser = argparse.ArgumentParser(description="A m3u8 Downloader.")
	parser.add_argument("url", help="The URL to the m3u8.")
	parser.add_argument("name", help="The video's name.")
	parser.add_argument("-n", default=10, help="The number of threads used to download ts files.")
	parser.add_argument("-s", action="store_true", help="Don't delete ts files.")
	return parser.parse_args()

def get_ts(output_dir, ts_url, key, iv):
	print(f"开始下载ts文件: {ts_url}")

	# 下载ts文件
	with requests.get(ts_url) as response:
		data = response.content

	# 解密ts文件
	cipher = AES.new(key, AES.MODE_CBC, iv)
	data = cipher.decrypt(data)

	# 保存ts文件
	ts_fname = f"{output_dir}/{os.path.basename(ts_url)}"
	with open(ts_fname, "wb") as ts:
		ts.write(data)

def main():
	# 读取参数
	args = get_args()

	# 创建进程池
	pool = Pool(args.n)

	# 创建输出目录
	output_dir = os.path.abspath(args.name)
	if os.path.isdir(output_dir):
		while True:
			overwrite = input(f"输出目录{output_dir}已存在, 是否要覆盖? [y/N] ")
			if overwrite == "Y" or overwrite == "y":
				break
			elif overwrite == "N" or overwrite == "n" or overwrite == "":
				print("请重新指定name参数后重试.")
				exit(1)
			else:
				continue
	else:
		os.makedirs(output_dir)

	# 下载m3u8文件
	index_fname = f"{output_dir}/{args.name}.m3u8"
	with requests.get(args.url) as response:
		with open(index_fname, "w") as m3u8:
			m3u8.write(response.text)

	# 解析m3u8文件, 下载ts文件
	with open(index_fname, "r") as m3u8:
		for line in m3u8.readlines():
			line = line.strip()
			if re.match("^#.*$", line):
				res = re.search("^#EXT-X-KEY:METHOD=(.*),URI=\"(.*)\"(,IV=0x)?(.*)?$", line)
				if not res:
					continue
				assert res.group(1) == "AES-128", f"暂不支持的Method: {res.group(1)}"
				with requests.get(res.group(2)) as response:
					key = response.content
				assert len(key) == 16, f"KEY的长度不为16: {len(key)}"
				iv = res.group(4) if res.group(4) else "00" * 16
				iv = bytes.fromhex(iv)
			elif re.match("^.*\.ts$", line):
				ts_prefix = re.compile("\d+\.ts$").sub("", line, 1)
				ts_url = f"{os.path.dirname(args.url)}/{os.path.basename(line)}"
				pool.apply_async(get_ts, args=(output_dir, ts_url, key, iv))
	pool.close()
	pool.join()

	# 合并ts文件
	ts_files = [fname for fname in os.listdir(output_dir) if re.match(f"^{ts_prefix}\d+\.ts$", fname)]
	ts_index = lambda fname: int(re.findall(f"{ts_prefix}(\d+)\.ts", fname)[0])
	ts_merged_fname = f"{output_dir}/{args.name}.ts"
	with open(ts_merged_fname, 'wb') as ofile:
		for fname in sorted(ts_files, key=ts_index):
			fname = f"{output_dir}/{fname}"
			print(f"开始合并ts文件: {fname}")
			with open(fname, 'rb') as ifile:
				while True:
					chunk = ifile.read(65536)
					if not chunk:
						break
					ofile.write(chunk)
			if not args.s:
				os.remove(fname)


if __name__ == "__main__":
	main()
