import pandas as pd
import numpy as np
import time 
import sys
import os
import random
import math
import datetime
from request.rakuten_rss import ind, rss , rss2 
from lib.ddeclient import DDEClient
from price_logger import ClientHolder 
from price_logger import LastNPerfTime
from multiprocessing import Process
from tkinter import messagebox

# csvファイルから指標やコードを編集
def ind():
	#indexes = pd.read_csv("TOPIX_weight_jp.csv")
	indexes = pd.read_csv("nf_indexes.csv")
	#indexes["コード"] = pd.to_numeric(indexes["コード"], errors='coerce')


	indexes_code = indexes["コード"].astype(int)
	shares_no = indexes["株数"].astype(int)
	for i,j in enumerate(indexes_code):
		indexes_code[i] = str(j) + ".T"
	

	indexes = indexes["純資産比率"].astype(float)
	return [indexes_code, indexes, shares_no]


def code_s(k):
	array = []
	weights = []
	count = 0
	
	
	# 以下csvファイルを都合いいようにエディット

	inde = ind()
	indexes_code, indexes, shares_no = inde[0], inde[1], inde[2]
	box = []
	# ddeを取得、格納、ウエイトをかけて計算
	
	for i,j in enumerate(indexes_code, start = k): 
		count += 1
		
		c = indexes_code[i]
		w = indexes[i]
		s = shares_no[i]
		weights.append(w)
		array.append(str(c))
		box.append(s)
		# 2142 ~ 2182 まで
		if k == 2142 and count ==29:
			break

		if count >= 126:
			break

	return [array, weights,box]

# コマンドラインの第二引数がonのとき、開場までの時間を計測してそこまで処理を停止する。
def stop_execute():
	now = datetime.datetime.now()
	currently = np.datetime64(now)
	year = now.year
	month = now.month
	day = now.day

	hour = now.hour
	minute = now.minute
	if  hour >= 15:
		print("今日は閉場です。")
		sys.exit()
	if (hour == 11 and minute > 30 ) or (hour==12 and minute <30):
		print("お昼休みです。")
		temp = pd.datetime(year, month, day, 12, 31)		
		temp = np.datetime64(temp)
		sleep_num = float(temp.astype("float64")-currently.astype("float64"))
		tim = sleep_num / 10 ** 6
		t = int(tim)
		print(t)
		#直前ではなく指定時刻の100秒後から開始する
		time.sleep(float(t)+100)
	elif hour < 9:
		temp = pd.datetime(year, month, day, 9, 0)		
		temp = np.datetime64(temp)
		sleep_num = float(temp.astype("float64")-currently.astype("float64"))
		tim = sleep_num / 10 ** 6
		t = int(tim)
		print(t)
		#直前ではなく指定時刻の50秒後から開始する
		time.sleep(float(t +50))
	else:
		pass
		



if __name__ == '__main__':
    args = sys.argv # コマンドライン引数として開始地点のインデックスを数字で入力する
    
    count = 0
    
	
	
	# 引数　0 →　0 ~ 125, 1 →　126 ~ 251, 2 →　252 ~ 377, 3 →　378 ~ 503, 4 →　504 ~ 629
	# 5 →　630 ~ 755, 6 →　756 ~ 881, 7 →　882 ~ 1007, 8 →　1008 ~ 1133, 9 →　1134 ~ 1259, 10 →　1260 ~ 1385
	# 11 →　1386 ~ 1511, 12 →　1512 ~ 1637, 13 →　1638 ~ 1763, 14 →　1764 ~ 1889, 15 →　1890 ~ 2015, 16 →　2016 ~ 2141, 17 →　2142 ~ 2182
    idx = int(args[1]) * 126
    if len(args) > 2:
        switch = args[2]
        if switch == "on":
            #止める
            stop_execute()
    #　idx : どのプロセスか示す指標,  code_s(idx)[0] ：　銘柄番号, code_s(idx)[1] : ウエイト       
    holder = ClientHolder(idx, code_s(idx)[0], code_s(idx)[1],code_s(idx)[2])
    #print(code_s(idx)[0], code_s(idx)[1])
    holder.get_prices_forever()

                      
