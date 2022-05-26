import numpy as np

class Adjustor:
    def __init__(self, n=100, max_std=1.0e-3):
        """
        過去のETF価格と計算したNAV価格をもとに、
        計算したNAV価格にかけるべき係数を推定する
        
        Parameters
        ----------
        n : int
    　　過去何回分のデータを保存するか
        max_std : float
        調整した値を信用してもよいとする、
        計算したNAVのETF価格からの乖離率の標準偏差の最大値
        この値が小さいほど基準が厳しくなる
        """
        # パラメータ設定
        self.n = n
        self.max_std = max_std
        
        # 過去n回分のデータを保存するリングバッファ
        self.last_n_x = np.zeros(n, dtype=float) # 過去n回分の乖離率
        self.last_n_x_square = np.zeros(n, dtype=float) # 過去n回分の[乖離率の2乗]
        
        # 統計値
        self.moving_sum = 0.0 # 過去n回分の乖離率の合計
        self.moving_sum_square = 0.0 # 過去n回分の[乖離率の2乗]の合計
        self.data_count = 0 # Adjustor.feed()を呼び出した回数
        
        # 過去n回分の、有効と判定されたデータを保存するリングバッファ
        self.last_n_nav = np.zeros(n, dtype=float)
        self.last_n_etf = np.zeros(n, dtype=float)
        
        # 有効と判定されたデータの統計値
        self.sum_nav = 0.0
        self.sum_etf = 0.0
        
        # 計算したNAVに対する推定されたNAVの値の比
        self.estimated_coef = 1.0
        
    def feed(self, etf, nav):
        """
        ETF価格と計算したNAVを入力とし、
        過去に入力された値から真のNAV価格を推定する
        
        Parameters
        ----------
        etf : float
        ETF価格
        nav : float
        計算したNAV
        
        Returns
        -------
        is_valid : bool
        推定したNAV価格が信用に足るか　Trueなら信用できる値
        
        nav : float
        推定したNAV価格
        
        """
        
        # ETF価格に対するNAVの乖離率を求める
        x = nav / etf - 1
        
        # 過去n回分の乖離率の標準偏差を求める
        i = self.data_count % self.n # リングバッファのインデックス
        x_square = x * x
        
        # 毎回長さnの配列の標準偏差を求めると時間がかかるので、
        # 前回の呼び出し時に計算した[平均値]と[二乗した値の平均値]に、
        # [今回の値 - n回前の値]　をそれぞれ足して今回の[平均値]と[二乗した値の平均値]を求める
        self.moving_sum += (x - self.last_n_x[i])
        self.moving_sum_square += (x_square - self.last_n_x_square[i])
        
        # 乖離率を保存
        self.last_n_x[i] = x
        self.last_n_x_square[i] = x_square
        
        self.data_count += 1
        
        if self.data_count > 1:
            # 分散の公式から分散を求める
            moving_average = self.moving_sum / self.n
            variance = self.moving_sum_square / self.n - moving_average * moving_average
            
            # 標準偏差を求める
            assert variance > -1.0e8
            if variance <= 0:
                # 同じ値がn個連続でフィードされた場合など
                # 数値誤差で分散が0以下になることがある
                moving_std = 0
            else:
                moving_std = np.sqrt(variance)
            
            # 標準偏差が一定以下ならば過去の乖離率に異常値がないとする
            is_valid = moving_std < self.max_std
        else:
            # 最初の呼び出しのとき
            is_valid = False
        

        # 有効と判定されたETF価格、NAVのうち過去n回分の値の合計を求める
        self.sum_etf += etf - self.last_n_etf[i]
        self.sum_nav += nav - self.last_n_nav[i]

        # 値を保存
        self.last_n_etf[i] = etf
        self.last_n_nav[i] = nav

        # 合計値の比を実際のNAVとフィードされたNAVとの比と推定する
        self.estimated_coef = self.sum_etf / self.sum_nav
            
        # 推定された比を用いてNAV価格を調整
        adjusted_nav = nav * self.estimated_coef
        
        # 今回のフィードで急に乖離率が大きく変わった場合
        # 異常値と判定する
        if is_valid and (moving_std > 0):
            coef_sigma = (1 / (x + 1) - self.estimated_coef) / moving_std
            if np.abs(coef_sigma) > 3: # 3シグマ以上で異常値とする
                is_valid = False
        
        return is_valid, adjusted_nav