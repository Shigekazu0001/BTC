import configparser
import time
import pandas as pd
import datetime
import requests
from coincheck import Coincheck
from pprint import pprint

conf = configparser.ConfigParser()
conf.read('config.ini')
ACCESS_KEY = conf['coincheck']['access_key']
SECRET_KEY = conf['coincheck']['secret_key']

coincheck = Coincheck(ACCESS_KEY, SECRET_KEY)
# 変数
i = 0
df = pd.DataFrame()
df1 = pd.DataFrame()
# 0で買い、1で売る
sell_buy_switch = 0
Buy_price = 0
Sell_price = 0
Bet = 0
Sell_second = 0
First_F = 0
NOW_JPY = 0
NOW_BTC = 0
Falling_Sign = 0

# 定数
interval_sec = 1
interval = 1
long = 3000
short = 1200
duration = long
second = 60
hour = 3600

# 買うときに使うやつ
Buy_flag = 0
Touched_Flag = 0
N = 180
M = 3600
Touched_BB_Vaulue = 0
Better_count = 0
N_Check_Value = []
#データ系########################################################################################


def Get_Nowmoney():
    try:
        f = open('Now_money.txt')
        Nowmoney = f.readlines()
        f.close()
        Nowmoney = float(Nowmoney[0])
        return Nowmoney
    except(PermissionError):
        print("PermissionError")
        time.sleep(10)
        Get_Nowmoney()


def Get_data(duration, df):

    global sell_buy_switch
    global Sell_second
    i = len(df)
    pro_size = 10
    while i <= duration:
        j = i/duration
        j = round(j, 1)*10
        j = int(j)
        pro_bar = ('=' * j) + (' ' * (pro_size - j))
        print('\r[{0}] {1}%'.format(pro_bar, j / pro_size * 100.), end='')
        df = df_append(df)
        i = len(df)

    if(i > duration):
        try:
            df = df_append(df)
        except(TypeError):
            print("最初のTypeError")
            time.sleep(600)
            df = df_append(df)

        if sell_buy_switch == 1:
            Sell_second += 1
        elif sell_buy_switch == 0:
            Sell_second = 0

    return df


def df_append(df):
    list = coincheck.order_books()
    To_buy = int(list['asks'][0][0].replace('.', ''))
    To_sell = int(list['bids'][0][0].replace('.', ''))
    To_buy = To_buy/10
    To_sell = To_sell/10
    df = df.append(
        {'Look_buy_time': To_buy, 'Look_sell_time': To_sell}, ignore_index=True)
    return df


def save_money(df):
    global Bet
    global Buy_price
    global Sell_price
    global Sell_second

    rate = Bet/Buy_price
    mouke = rate*Sell_price
    difference = mouke-Bet
    dt_now = datetime.datetime.now()
    Selled_time = dt_now.strftime('%Y/%m/%d/ %H:%M:%S')
    print("今回の取引の儲けは"+str(difference)+"円です")
    df1 = pd.DataFrame([[Buy_price, Sell_price, rate, mouke, difference, Sell_second, Selled_time]], columns=[
        '買値', '売値', 'レート', '現在の金額', '儲け', '売却時間', '売り時刻'])
    df1.to_csv(r"data.csv", mode='a', header=False, index=False)
    f = open('Now_money.txt', "w")
    f.write(str(mouke))
    f.close()


def Corecting_data(df):
    df.to_csv(r"Corected_data.csv", mode='w', header=False, index=False)

#決済系########################################################################################


def NOW_BTC_JPY(NOW_BTC, NOW_JPY):
    a = coincheck.balance()
    NOW_BTC = a['btc']
    NOW_JPY = a['jpy']
    return NOW_BTC, NOW_JPY


def To_Buy(NOW_JPY):
    params = {
        'pair': 'btc_jpy',
        'order_type': 'market_buy',
        'market_buy_amount': NOW_JPY
    }
    r = coincheck.order(params)
    print("\n")
    # print(type(r['success']))
    print('entry', r['success'])

    if r['success']:
        mudamudamuda = 1
    else:
        print('error', r['error'])
        print('amount', r['amount'])

    return r['success']


def To_Sell(NOW_BTC):

    params = {
        'pair': 'btc_jpy',
        'order_type': 'market_sell',
        'amount': NOW_BTC
    }
    r = coincheck.order(params)
    # print("\n")
    #print('entry', r['success'])

#まとめ系########################################################################################


def TO_SELL_SET():
    global Falling_Sign
    global Buy_flag
    global Sell_price
    global NOW_BTC
    global NOW_JPY

    To_Sell(NOW_BTC)
    Sell_price = coincheck.ask_rate[1]
    print(
        "\r"+str(Sell_price)+'円で売却しました                 差額:'+str(Sell_price-Buy_price)+"円")
    save_money(df)
    NOW_BTC, NOW_JPY = NOW_BTC_JPY(NOW_BTC, NOW_JPY)
    sell_buy_switch = 0
    Falling_Sign = 0
    Buy_flag = 0

    return sell_buy_switch


def Initialize():
    global i
    global df
    global df1
    global First_F
    i = 0
    df = pd.DataFrame()
    df1 = pd.DataFrame()
    First_F = 0

#判定系########################################################################################


def Judgement(sell_buy_switch, i, long):

    global Buy_price
    global Sell_price
    global Sell_second
    global First_F
    global NOW_BTC
    global NOW_JPY
    global Falling_Sign
    global Buy_flag
    global Touched_Flag
    global N
    global M
    global Touched_BB_Vaulue
    global Better_count
    global N_Check_Value
    fucking_flag = 0

    # BB買うとき用
    df['BSMA'] = df['Look_buy_time'].rolling(window=duration).mean()
    df['Bstd'] = df['Look_buy_time'].rolling(window=duration).std()
    df['B-2σ'] = df['BSMA'] - 2.0*df['Bstd']
    B2σ = df['B-2σ'].iloc[-1]
    B2σ = int(B2σ)
    # BB売るとき用
    df['SSMA'] = df['Look_sell_time'].rolling(window=duration).mean()
    df['Sstd'] = df['Look_sell_time'].rolling(window=duration).std()
    df['S+2σ'] = df['SSMA'] + 2.0*df['Sstd']
    S2σ = df['S+2σ'].iloc[-1]
    S2σ = int(S2σ)
    # GX買うとき用
    df["B_LONG_M"] = df['Look_buy_time'].rolling(window=long).mean()
    df["B_SHORT_M"] = df['Look_buy_time'].rolling(window=short).mean()

    if First_F == 0:
        df["P_or_M__B"] = df["B_LONG_M"].iloc[-1] - df["B_SHORT_M"].iloc[-1]
        NOW_BTC, NOW_JPY = NOW_BTC_JPY(NOW_BTC, NOW_JPY)
        First_F = 1
    else:
        df["P_or_M__B"][len(df)-1] = df["B_LONG_M"].iloc[-1] - \
            df["B_SHORT_M"].iloc[-1]

    try:

        if sell_buy_switch == 0:

            if Touched_Flag == 0:  # ボリバンタッチのときにフラグ
                if (df['Look_buy_time'].iloc[-1] < df['B-2σ'].iloc[-1]):
                    Touched_Flag = 1
                    Touched_BB_Vaulue = df['Look_buy_time'].iloc[-1]

            elif Touched_Flag == 1:
                if Better_count >= M:
                    N_Check_Value.append(
                        df['Look_buy_time'].iloc[-1])  # 第n回目のチェックの数値の代入

                    if N_Check_Value[-1] > Touched_BB_Vaulue:  # 最初値よりも安いかチェック（高くなってたら初期化）

                        Touched_Flag = Better_count = Touched_BB_Vaulue = 0
                        N_Check_Value = []
                    else:  # とりあえず最初より下がってる時
                        if len(N_Check_Value) == 1:  # 一回目のチェックで値段が下がってたらもう一回データを取得するためにカウントを0にする
                            Better_count = 0
                        elif len(N_Check_Value) > 1:
                            # タッチしたときの値よりも小さくて、n-1週目の数よりn週目の数が大きい時、買いの動き
                            if N_Check_Value[-1] > N_Check_Value[-2]:

                                if df["P_or_M__B"][len(df)-1] < 0:  # ショートのほうが上のとき
                                    Buy_flag = 1
                                else:
                                    Buy_flag = 0

                                if To_Buy(NOW_JPY):  # 購入手続き

                                    Buy_price = coincheck.ask_rate[0]
                                    print("\r"+str(Buy_price)+'円で購入しました')
                                    NOW_BTC, NOW_JPY = NOW_BTC_JPY(
                                        NOW_BTC, NOW_JPY)

                                    Touched_Flag = Better_count = Touched_BB_Vaulue = 0
                                    N_Check_Value = []
                                    sell_buy_switch = 1

                            # すっごい低くなってるからもっかい
                            elif N_Check_Value[-1] <= N_Check_Value[-2]:
                                Better_count = 0

                else:
                    Better_count += 1

        elif sell_buy_switch == 1:

            if Buy_flag == 0:
                Falling_Sign = 1

            elif Buy_flag == 1:

                if Falling_Sign == 0:
                    # 今-昔マイナス出てるとき
                    if df['Look_sell_time'].iloc[-1]-Buy_price < 0:  # ○
                        Falling_Sign = 1
                    else:
                        Falling_Sign = 0
                elif Falling_Sign == 1:
                    Falling_Sign = 1

            # 上昇時
            if Falling_Sign == 0:  # いくらでも上がっていい
                if ((df['S+2σ'].iloc[-1] < df['Look_sell_time'].iloc[-1]) and (Buy_price < df['Look_sell_time'].iloc[-1])):  # ○
                    sell_buy_switch = TO_SELL_SET()
                    print("上昇売りやで")

            # 下落時
            elif Falling_Sign == 1:

                if Sell_second >= 0 and Sell_second <= 43200:  # 12時間は流ス

                    if df['Look_sell_time'].iloc[-1]-Buy_price > 3000:  # ちょっと怖い時、2000以上の儲けで売る
                        # sell_buy_switch = TO_SELL_SET()
                        # print("下落売りやで")
                        if Touched_Flag == 0:  # ボリバンタッチのときにフラグ
                            if df['Look_sell_time'].iloc[-1]-Buy_price > 3000:
                                Touched_Flag = 1
                                Touched_BB_Vaulue = df['Look_buy_time'].iloc[-1]

                        elif Touched_Flag == 1:
                            if Better_count >= N:
                                N_Check_Value.append(
                                    df['Look_buy_time'].iloc[-1])  # 第n回目のチェックの数値の代入

                                # 最初値よりも低くなってたら初期化
                                if N_Check_Value[-1] < Touched_BB_Vaulue:

                                    Touched_Flag = Better_count = Touched_BB_Vaulue = 0
                                    N_Check_Value = []

                                else:  # とりあえず最初より上がってる時
                                    # 一回目のチェックで値段が下がってたらもう一回データを取得するためにカウントを0にする
                                    if len(N_Check_Value) == 1:
                                        Better_count = 0
                                    elif len(N_Check_Value) > 1:
                                        # タッチしたときの値よりも小さくて、n-1週目の数よりn週目の数が大きい時、買いの動き
                                        if N_Check_Value[-1] < N_Check_Value[-2]:

                                            # if To_Buy(NOW_JPY):#購入手続き
                                            sell_buy_switch = TO_SELL_SET()
                                            print("下落売りやで")

                                            Touched_Flag = Better_count = Touched_BB_Vaulue = 0
                                            N_Check_Value = []

                                        # すっごい高くなってるからもっかい
                                        elif N_Check_Value[-1] >= N_Check_Value[-2]:
                                            Better_count = 0

                            else:
                                Better_count += 1

                elif Sell_second > 43200 and Sell_second <= 86400:  # 24時間から損切りはじめ
                    if df['Look_sell_time'].iloc[-1]-Buy_price > -50000:
                        sell_buy_switch = TO_SELL_SET()

                elif Sell_second > 86400:
                    sell_buy_switch = TO_SELL_SET()

                if df['Look_sell_time'].iloc[-1]-Buy_price < -Buy_price*0.03:  # 買ったときより突然20万下がったら損切り
                    sell_buy_switch = TO_SELL_SET()
                    print("エゲツない値下げが起こっとるでぇ…")
                    time.sleep(10800)
                    fucking_flag = 1

        Now_price(df, sell_buy_switch, i, B2σ, S2σ,
                  len(N_Check_Value), Falling_Sign)
        if fucking_flag == 1:
            Initialize()
        return sell_buy_switch

    except(TypeError):
        print("ugogo")
        time.sleep(600)
        Judgement(sell_buy_switch, i, long)

#表示系########################################################################################


def Now_price(df, sell_buy_switch, i, B2σ, S2σ, Touched_Flag, Falling_Sign):

    if sell_buy_switch == 0:
        if i % 2 == 0:
            print("\r現在の価格は%s円 そして%s円以下なら購入 また%s週目" %
                  (df['Look_buy_time'].iloc[-1], B2σ, Touched_Flag), end='')

        elif i % 2 == 1:
            print("\r現在の価格は%s円 そして%s円以下なら購入 また%s週目 " %
                  (df['Look_buy_time'].iloc[-1], B2σ, Touched_Flag), end='')

    elif sell_buy_switch == 1:
        if i % 2 == 0:
            print("\r現在の価格は%s円 そして%s円以上なら売却 またFalling_Sing=%s" %
                  (df['Look_sell_time'].iloc[-1], S2σ, Falling_Sign), end='')

        elif i % 2 == 1:
            print("\r現在の価格は%s円 そして%s円以上なら売却 またFalling_Sing=%s " %
                  (df['Look_sell_time'].iloc[-1], S2σ, Falling_Sign), end='')


#ほんへ###################################################################################
try:
    while True:
        try:
            i += 1
            # データ追加
            Bet = Get_Nowmoney()
            df = Get_data(duration, df)
            Get_Nowmoney()
            # データ20集めるまで動きません
            if len(df) < duration:
                continue

            sell_buy_switch = Judgement(sell_buy_switch, i, long)

        except(ConnectionResetError):
            print("ConnectionResetError")
            time.sleep(600)
        except(requests.exceptions.ConnectionError):
            print("requests.exceptions.ConnectionError")
            time.sleep(30)
            # Initialize()

except(KeyboardInterrupt):
    Corecting_data(df)