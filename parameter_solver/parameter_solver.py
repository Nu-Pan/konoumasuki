
from sympy import *
from typing import Dict, List, Any
from sympy.plotting import plot

'''
# sympy ヘルパ
'''

def makesym() -> Symbol:
    '''
    シンボルを生成する。
    シンボル名は後で更新するので適当でいい。
    '''
    return Symbol('undef')

def Lerp( min_value: Symbol, max_value: Symbol, ratio: Symbol ) -> Symbol:
    '''
    区間 [min_value, max_value] 中の比率 ratio の値を返す。
    ratio は区間 [0.0, 1.0] に従う。
    '''
    length = max_value - min_value
    return length * ratio + min_value

def clamp( min_value: Symbol, max_value: Symbol, value: Symbol ) -> Symbol:
    '''
    value を区間 [min_value, max_value] にクランプする。
    '''
    return Piecewise( 
        (min_value, value < min_value),
        (max_value, value > max_value),
        (value, true )
    )

'''
# リーフパラメータ定義
入力として与えるべきパラメータ。
'''

# ウマ娘基礎ステータス
スピード = makesym()
スタミナ = makesym()
パワー = makesym()
根性 = makesym()
賢さ = makesym()
脚質補正 = makesym()
バ場適正補正 = makesym()
距離適性補正 = makesym()
やる気補正 = makesym()

# スキル補正
スキル補正賢さ = makesym()
スキル補正スタミナ = makesym()
スキル補正パワー = makesym()
スキル補正根性 = makesym()
スキル補正スピード = makesym()
スキル補正速度 = makesym()

# コース関連
バ場状態パラ補正 = makesym()
レース基準速度 = makesym()
基本速度補正 = makesym() # コース適正のこと
レース距離 = makesym()
バ場状態体力消費速度補正 = makesym()

# レース中動的変化
傾斜角 = makesym()
ポジションキープ補正 = makesym()
前のウマ娘との距離差 = makesym()
ブロック補正 = makesym()
ブロックしているウマ娘の現在速度 = makesym()
ウマ状態補正 = makesym()
現在レーン距離 = makesym()
最大レーン距離 = makesym()
順位 = makesym()
現在速度 = makesym()

# 他
育成モード補正 = makesym()

'''
# ルートパラメータ定義
計算式の左辺にしか存在しないパラメータ。
'''

基礎目標速度 = makesym()
通常目標速度 = makesym()
ポジションキープ目標速度 = makesym()
スパート目標速度 = makesym()
スタミナ切れ目標速度 = makesym()
被ブロック目標速度 = makesym()
加速度 = makesym()
初期体力上限 = makesym()
体力消耗速度 = makesym()
レーン変更目標速度 = makesym()
レーン変更加速度 = makesym()
レーン変更実際速度 = makesym()

'''
# sympy シンボル名更新
python 上と sympy 上で変数名を一致させる。
'''

base_locals = locals()
locals().update([
    (k, Symbol(k))
    for k in base_locals
    if type(base_locals[k]) is Symbol
])

'''
# ノードパラメータ定義
リーフパラメータとノードパラメータをつなぐ中間パラメータ。
'''

# ウマ娘基礎パラメータ
補正スピード = スピード * やる気補正 * 基本速度補正 + バ場状態パラ補正 + 育成モード補正 + スキル補正スピード
補正賢さ = 賢さ * やる気補正 * 脚質補正 + 育成モード補正 + スキル補正賢さ
補正スタミナ = スタミナ * やる気補正 + バ場状態パラ補正 + 育成モード補正 + スキル補正スタミナ
補正パワー = パワー * やる気補正 + バ場状態パラ補正 + 育成モード補正 + スキル補正パワー
補正根性 = 根性 * やる気補正 + バ場状態パラ補正 + 育成モード補正 + スキル補正根性

# 速度関係
レース基準速度 = 20 - ( 2000 - レース距離 ) * 0.001
賢さランダム補正上限 = ( 補正賢さ / 5500 ) * log( 補正賢さ * 0.1 )
賢さランダム補正下限 = 賢さランダム補正上限 - 0.65
賢さランダム補正 = ( 賢さランダム補正下限 + 賢さランダム補正上限 ) / 2 # 本当は一様乱数なんだけど、めんどいので期待値でお茶を濁す
上り坂補正 = - abs( 100 * tan( 傾斜角 * 0.017453 ) ) * 200 / 補正パワー
下り坂補正 = 0.3 + abs( 100 * tan( 傾斜角 * 0.017453 ) ) / 10.0
坂補正 = Piecewise( (下り坂補正, 傾斜角 < 0), (上り坂補正, 傾斜角 >= 0) )

# 体力関係
体力消耗速度補正 = ( 現在速度 - レース基準速度 + 12 ) ** 2 / 144
体力消耗速度スパート補正 = 1 + 200 / sqrt( 600 * 補正根性 )

# レーン変更関係
レーン変更スタート補正 = 1.0 + 0.05 * ( 現在レーン距離 / 最大レーン距離 )
レーン変更順位補正 = 1.0 + 0.001 * 順位
レーン変更内側移動補正 = - ( 1.0 + 現在レーン距離 )

'''
# ルートパラメータ式定義
ルートパラメータの計算式。
solve の対象なので Eq にしている。
'''
equations = [
Eq(
    基礎目標速度,
    sqrt( 500 * 補正スピード ) * 距離適性補正 * 0.002 + レース基準速度 * ( 脚質補正 + 賢さランダム補正 )
),
Eq(
    通常目標速度,
    基礎目標速度 + 坂補正
),
Eq(
    ポジションキープ目標速度,
    基礎目標速度 * ポジションキープ補正 + 坂補正
),
Eq(
    スパート目標速度,
    1.05 * ( 基礎目標速度 + 0.01 * レース基準速度 ) + sqrt( 500 * 補正スピード ) * 距離適性補正 * 0.002
),
Eq(
    スタミナ切れ目標速度,
    レース基準速度 * 0.85 + sqrt( 補正根性 * 200 ) * 0.001
),
Eq(
    被ブロック目標速度,
    Lerp( 0.988, 1.0, 前のウマ娘との距離差 / ブロック補正 ) * ブロックしているウマ娘の現在速度
),
Eq(
    加速度,
    脚質補正 * 0.0006 * sqrt( 補正パワー * 500 ) * バ場適正補正
),
Eq(
    初期体力上限,
    レース距離 + 脚質補正 * 0.8 * 補正スタミナ
),
Eq(
    体力消耗速度,
    20 * 体力消耗速度補正 * バ場状態体力消費速度補正 * ウマ状態補正 * 体力消耗速度スパート補正
),
Eq(
    レーン変更目標速度,
    0.02 * ( 0.3 + 0.001 * 補正パワー ) * レーン変更スタート補正 * レーン変更順位補正
),
Eq(
    レーン変更加速度,
    0.02 * 1.5 
),
Eq(
    レーン変更実際速度,
    clamp( 0, 0.6, 現在速度 + スキル補正速度 ) * レーン変更内側移動補正
)
]

# ↓みたいな感じで解く
# solve(equations, スピード)
