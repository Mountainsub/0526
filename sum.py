import pandas as pd
import numpy as np
import time 
import sys
import os
import ctypes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import datetime

from lib.ddeclient import DDEClient
from price_logger import ClientHolder 
from price_logger import LastNPerfTime
from init import keisan

class plot_time:
    def __init__(self):
        self.hdffilename = "./data/sum.hdf5"
        self.store = pd.HDFStore(self.hdffilename)
        self.key_name2 = "timecase"

    

    def hozon2(self, data_dict):
        #print("OK")
        self.store.append(self.key_name2, data_dict)
      

        
def read_latest_total(filename):
    with pd.HDFStore(filename) as store:
        temp =store.get(object_pass)                    
    end = temp.tail(1)
    v = float(end["total"])
    return v


if __name__ == "__main__":
    
    # コマンドライン上の出力文字に色を付ける
    ENABLE_PROCESSED_OUTPUT = 0x0001
    ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    MODE = ENABLE_PROCESSED_OUTPUT + ENABLE_WRAP_AT_EOL_OUTPUT + ENABLE_VIRTUAL_TERMINAL_PROCESSING
    
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    kernel32.SetConsoleMode(handle, MODE)

    
    calc = 0
    
    object_pass = "value"
    dde = DDEClient("rss", "1306.T")
    
    st = pd.HDFStore("./data/sum.hdf5")
    

    currently = datetime.datetime.now()
    year = currently.year
    month = currently.month
    day = currently.day        
    price = 0
    total_interest = 0
    holder = plot_time()
    max_fail_count = 2
    num_shares = 8039808130 # syokiti -> num_shares に名前変更
    num_files = 18 # hdfファイルの数
    while True:
        fatal_fail_count = 0 # max_fail_count以上データ取得に失敗したファイルの数
        calc = 0
        for i in range(num_files):
            idx = i *126
            object_pass = "classidx_"+ str(idx)
            filename = "./data/"+str(idx).zfill(3)+".hdf5"
            for j in range(max_fail_count):
                try:
                    v = read_latest_total(filename)
                    print(i, '{:.2f}'.format(v))
                    break
                except Exception as e: # except: だとKeyboardInterrupt等もキャッチしてしまう
                    # 更新中に取得した場合など値の取得を誤ったとき
                    # 取得をやりなおす
                    v = 0
                    if j == max_fail_count - 1:
                        fatal_fail_count += 1
                    now = datetime.datetime.now()
                    print(i, "attention", now)
            calc += v
        #print(calc)
       
        if fatal_fail_count > 0:
            print("一部のファイルで値の取得に失敗しました")
        
        now = datetime.datetime.now()
        total = calc
        calc /=  num_shares
        if (now.hour == 11 and now.minute > 38) or (now.hour == 12 and now.minute < 28):
            temp = st.get("consequence")
            topix = float(temp["topix"].tail(1))
            st.append("consequence",pd.DataFrame({"time":[str(now)], "calc":[calc],"topix":[topix], "topix_a":[topix], "topix_b":[topix],"topix_c":[topix], "topix_d":[topix],"total":[total]}), index=False)
            print("昼休み中")
            continue
        else:
            pass
        topix = dde.request("現在値").decode("sjis")
        topix_a = dde.request("最良売気配値").decode("sjis")
        topix_b = dde.request("最良買気配値").decode("sjis")
        topix_c = dde.request("最良売気配数量").decode("sjis")
        topix_d = dde.request("最良買気配数量").decode("sjis")
        calc *= 1.0303316552005348
        print("取得時刻:"+str(now),"計算値:" + str(calc))
        
        # 格納する値、左から順に　現在時刻、計算したトピックス、取得したトピックスの指標、、ここまでの利益総額、取得に失敗した回数
        data_dict = {"time":[str(now)], "calc":[calc],"topix":[topix], "topix_a":[topix_a], "topix_b":[topix_b],"topix_c":[topix_c], "topix_d":[topix_d],"total":[total]}
        st.append("consequence",pd.DataFrame(data_dict), index=False)

        #1.0303316552005348
        """
        下編集中
        temp = pd.datetime(year, month, day, 14, 58)
        if now > temp:
            
            print("end") 
        
        # 売り
        if calc > topix_a:
            if inventory >= admissible_M:
                continue
            else:
                order = "buy"
                quantity = inventory
                inventory += quantity 
        elif calc < topix_b:
            if inventory <= float(topix_d):
                continue
            else:
                order = "sell"
                order_p = topix_a
                quantity = inventory
                inventory -= quantity
        else:
            if inventory >= admissible_M:
                order_p = topix_a
                order = "sell"
                order_q = admissible_M - admissible_m 
                inventory -= order_q
            else:
                order_q = admissible_M - admissible_m
                order  = "buy"
                order_p= topix_b
                inventory += order_q
                if 



        # 買い
        if topix_d > :
            ddffg
        """
        