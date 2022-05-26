#!/usr/bin/env python
# coding: utf-8


import warnings
from tables import NaturalNameWarning


warnings.filterwarnings('ignore', category=NaturalNameWarning)


import asyncio
import pandas as pd
import numpy as np
import datetime
import os
from concurrent import futures
import pathlib
import sys
sys.path.append("..")
from lib.ddeclient import DDEClient

import time
from tkinter import messagebox


def stop_execute():
	now = datetime.datetime.now()
	currently = np.datetime64(now)
	year = now.year
	month = now.month
	day = now.day

	hour = now.hour
	minute = now.minute
	if  hour > 15:
		print("今日は閉場です。")
		sys.exit()
	if (hour == 11 and minute > 30 ) or (hour==12 and minute <30):
		print("お昼休みです。")
		temp = pd.datetime(year, month, day, 12, 30)		
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

class LastNPerfTime:
    def __init__(self, n):
        """
        過去n回の実行時間の合計を尺取り法で記録する
        """
        self.n = n
        self.count = 0
        self.sum_time = 0
        self.times = np.zeros(n)
        
        
    def start(self):
        """
        実行時間の計測を開始する
        """
        self.start_time = time.perf_counter() # timeより正確
        
    def end(self):
        """
        実行時間の計測を終了する
        """
        dtime = time.perf_counter() - self.start_time
        idx = self.count % self.n # self.nが2^xならここをビット論理積にできる
        time_n_before = self.times[idx]
        self.times[idx] = dtime
        #self.count += 1
        self.sum_time += (dtime - time_n_before)
        #print(dtime - time_n_before)
        
    def get_sum_time(self):
        """
        過去n回の実行時間を合計した値を返す
        """
        return self.sum_time
    
    def count_one(self):
        self.count += 1

class ClientHolder():
    def __init__(self, idx, codes, weights,shares_no,hdffoldername = "./data/"):
        """
        RSSサーバーに接続し、継続的に複数の銘柄の株価を取得する
        
        Parameters
        ----------
        idx: int
        ClientHolderにつける番号
        番号がかぶると同じファイルに書き込むことになる
        
        codes: array_like
        RSSサーバーにリクエストを送る銘柄のコード番号を格納したリスト
        
        """
        hdffilename = hdffoldername +  str(idx).zfill(3)+".hdf5"  # 文字列・数値をゼロパディング（ゼロ埋め）するzfill()
        
        self.idx = idx
        self.clients = {}
        self.activate = {}
        self.array=[]
        self.close_value = "現在値" #price_request_str
        self.codes = codes
        self.weights = weights
        self.shares_no = shares_no
        
        self.codes_attrsafe = 'code_' + np.array(codes).astype('object') # pandasを使ってhdfを作るとき、数字から始まる列名にできない
        
        # RSSサーバーに接続し、127個のDDEClientを作る
        self.connect_all()
        self.delete_count = 0
        # データ保存用のファイルを開く
        self.hdffilename = hdffilename
        self.store = pd.HDFStore(hdffilename)
        self.key_name = "classidx_" + str(self.idx) 
        
        self.firststep = True
        #self.checkbox = {0:65, 1:98, 2:80, 3:86, 4:250, 5:240, 6:360, 7:100, 8:660, 9:550, 10:2000, 11:270, 12:240,13:1680, 14:220, 15:250, 16:230, 17:270}
        
        
        
        
    def connect_all(self):
        """
        RSSサーバーに接続する
        """
        for code in self.codes:
            try:
                self.clients[code] = DDEClient("rss", code)
            except Exception as e:
                print(f"an error occurred at code: {code} while connecting server.")
                pass
            
        return
    
    

    
    
    def get_price(self, code):
        """
        1つの銘柄の株価を取得する
        """ 
        
           
        client = self.clients[code]
        store = self.store 
        if True:
            val =0
            try:
                val = client.request("現在値").decode("sjis")         
            except Exception :
                pass
                val = 0
            else:
                try:
                    val = float(val)
                except Exception as e:
                    val = 0
            if val != 0:
                store.put("pre_"+str(code),pd.DataFrame({"value":[val]}))
            
            
            if val == 0:
                
                
                try:
                    df = store.get("pre_"+str(code))
                    
                except:
                    pass
                else:
                    temp = df["value"]
                    val = float(temp.tail(1))
            
        return val 
        

    def get_price_a(self, code):
        client = self.clients[code]
        try:
            val = client.request("始値").decode("sjis")
        except Exception:
            val = 0
            pass
        else:
            val = float(val)
        return val
        
       
    
    
    def get_prices(self):
        """
        複数の銘柄の株価を取得し、保存する
        """
        
        prices = {}

        for i, code in enumerate(self.codes):     
            prices[self.codes_attrsafe[i]] = float(self.get_price(code))
        
        return prices

    def get_prices_a(self):
        """
        複数の銘柄の株価を取得し、保存する
        """
        
        prices = {}

        for i, code in enumerate(self.codes):     
            prices[self.codes_attrsafe[i]] = float(self.get_price(code))
        
        return prices

    def save(self, data_dict):
        """
        取得した株価を保存する
        """
        
        self.store.put(self.key_name, data_dict) 
         
        
        return
  
    
    
    def get_prices_forever(self):
        """
        継続的に株価を取得して保存し続ける
        """
        Firststep = True
        dde = DDEClient("RSS", "1306.T")
        count = 0
        i = int(self.idx) / 126
        a = datetime.datetime.now()
        a = a.microsecond
        prices= self.get_prices_a()
        v = self.calc(prices)
        with pd.HDFStore("./data/sum_init.hdf5") as store2:
            store2.put(self.key_name, pd.DataFrame({"初期値":[v]}))


        while True:
            try:
                prices= self.get_prices()
            except KeyboardInterrupt:
                break
            except Exception as e:
                raise Exception(e)
            else:
                v = self.calc(prices)
                
                try:
                    topix_etf = dde.request("現在値").decode("sjis")
                except:
                    topix_etf = None
                else:
                    topix_etf = float(topix_etf)
                
                now = datetime.datetime.now()
                if now.microsecond - a> 10**4:  
                    year = now.year
                    month = now.month
                    day = now.day
                    hour = now.hour
                    minute = now.minute
                    if hour >= 11 and hour < 12 and minute > 30:
                        print("OK")
                        stop_execute()
                        print("休憩中です。")                     
                    elif hour < 12:
                        pass 
                        
                    else:
                        pass


                
                
                dict = {"total": [v],"present":[now]}
                
                #dict.update(prices)
                
                
                data_dict = pd.DataFrame(dict)
                #print(data_dict)
                #辞書形式でhdf5ファイルに保存
                self.save(data_dict)
                
                
                    
                if v == 0:
                    print("no connected")
                else:
                    print('{:.2f}'.format(v)) #'{:.1f}'.format(num)
                
            
                
                
                

    def calc(self,prices):
        num = 0
        for i, code in enumerate(self.codes):
            val = prices[self.codes_attrsafe[i]]
            try:
                float(val)
            except Exception as e:
                pass
            shares = self.shares_no[i]
            ratio = self.weights[i]
            num += float(val)*float(shares)
        return num
    


if __name__ == '__main__':
    idx = int(sys.argv[1])
    foldername = sys.argv[2]
    codes = sys.argv[3:]
    holder = ClientHolder(idx, codes, foldername)
    
    holder.get_prices_forever()