import os
import requests
import re
import base64
import cv2
from datetime import datetime

FOFA_EMAIL = 'ittnxpfh9@gmail.com'
FOFA_KEY = '493bca542ade43fed47fff733a4242af'

os.makedirs('rtp', exist_ok=True)
os.makedirs('txt_files', exist_ok=True)

files = os.listdir('rtp')
files_name = [os.path.splitext(file)[0] for file in files]
provinces_isps = [name for name in files_name if name.count('_') == 1]

print(f"本次查询：{provinces_isps}的组播节目")

keywords = []

for province_isp in provinces_isps:
    try:
        with open(f'rtp/{province_isp}.txt', 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
        
        if lines and "rtp://" in lines[0]:
            mcast = lines[0].split("rtp://")[1].split(" ")[0]
            keywords.append(province_isp + "_" + mcast)
    except FileNotFoundError:
        print(f"文件 '{province_isp}.txt' 不存在. 跳过此文件.")

def get_fofa_results(province, org):

    query = f'"udpxy" && country="CN" && region="{province}" && org="{org}"'
    query_base64 = base64.b64encode(query.encode('utf-8')).decode('utf-8')
    api_url = f"https://fofa.info/api/v1/search/all?email={FOFA_EMAIL}&key={FOFA_KEY}&qbase64={query_base64}&size=100"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", [])
        return [result[0] for result in results]
    except requests.RequestException as e:
        print(f"Fofa API 请求失败: {e}")
        return []

for keyword in keywords:
    province, isp, mcast = keyword.split("_")
    
    if province == "北京" and isp == "联通":
        isp_en = "cucc"
        org = "China Unicom Beijing Province Network"
    elif isp == "联通":
        isp_en = "cucc"
        org = "CHINA UNICOM China169 Backbone"
    elif isp == "电信":
        org = "Chinanet"
        isp_en = "ctcc"
    elif isp == "移动":
        org = "China Mobile communications corporation"
        isp_en = "cmcc"
    else:
        continue

    current_time = datetime.now()
    result_urls = get_fofa_results(province, org)
    print(f"{current_time} 查询运营商 : {province}{isp} ，结果 URLs : {result_urls}")

    valid_ips = []
    for url in result_urls:
        video_url = f"{url}/rtp/{mcast}"
        cap = cv2.VideoCapture(video_url)
        
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"{current_time} {video_url} 的分辨率为 {width}x{height}")

            if width > 0 and height > 0:
                valid_ips.append(url)
            cap.release()
        else:
            print(f"{current_time} {video_url} 无效")
    
    if valid_ips:
        rtp_filename = f'rtp/{province}_{isp}.txt'
        with open(rtp_filename, 'r', encoding='utf-8') as file:
            data = file.read()
        txt_filename = f'txt_files/{province}{isp}.txt'
        
        with open(txt_filename, 'w', encoding='utf-8') as new_file:
            for url in valid_ips:
                new_data = data.replace("rtp://", f"{url}/rtp/")
                new_file.write(new_data)

        print(f'已生成播放列表，保存至 {txt_filename}')

print('节目表制作完成！ 文件输出在 txt_files 目录下！')
