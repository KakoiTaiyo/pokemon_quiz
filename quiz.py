import streamlit as st
import pandas as pd
import requests
import random
import json
import sqlite3

# データベースに接続
conn = sqlite3.connect('users.db')
c = conn.cursor()

# データベースにテーブルを作成する
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        score INTEGER DEFAULT 0,
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        keyword TEXT
    )
''')

# データを表示する関数
def show_data():
    c.execute('SELECT name, score FROM users')
    data = c.fetchall()
    for d in data:
        st.sidebar.write(f"ユーザー名: {d[0]}, スコア: {d[1]}")

# ユーザーを追加する関数
def add_user(name, keyword=None):
    try:
        if keyword:
            c.execute('INSERT INTO users (name, keyword) VALUES (?, ?)', (name, keyword))
        else:
            c.execute('INSERT INTO users (name) VALUES (?)', (name,))
        conn.commit()
        st.sidebar.write(f'{name} さんが追加されました。')
    except sqlite3.IntegrityError:
        st.sidebar.write(f'{name} さんはすでに登録されています。')

# 直近に利用した同じ合言葉のユーザー(max5人)を表示する関数
def show_recent_users(keyword):
    c.execute('SELECT name, score FROM users WHERE keyword = ? ORDER BY score DESC, last_used DESC LIMIT 5', (keyword,))
    data = c.fetchall()
    st.sidebar.write("### 同じ合言葉のユーザー")
    if data:
        # データをDataFrameに変換
        df = pd.DataFrame(data, columns=["ユーザー", "スコア"])
        # インデックスを1から始める
        df.index = df.index + 1
        # 表形式で表示
        st.sidebar.table(df)
    else:
        st.sidebar.write("該当するユーザーがいません。")

# ユーザーの追加
st.sidebar.write("ユーザー名を追加してクイズに参加するとスコアが記録されます。  \n合言葉を入力すると、同じ合言葉を入力したユーザーのスコアが表示されます。")
name = st.sidebar.text_input('ユーザー名')
keyword = st.sidebar.text_input('合言葉（任意）')
if st.sidebar.button('ユーザーを追加'):
    if name:
        add_user(name, keyword)
        st.session_state.current_user = name
    else:
        st.sidebar.warning("名前を入力してください。")

# 現在のユーザーを初期化
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
# 現在のユーザーのスコアを表示
if st.session_state.current_user is not None:
    c.execute('SELECT score FROM users WHERE name = ?', (st.session_state.current_user,))
    score = c.fetchone()[0]
    st.sidebar.write(f' {st.session_state.current_user} さんの前回のスコアは {score} です。')

if keyword:
    show_recent_users(keyword)

# データの表示
# show_data()

# セッション状態の初期化
if 'quiz_count' not in st.session_state:
    st.session_state.quiz_count = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'answer_disabled' not in st.session_state:
    st.session_state.answer_disabled = False
if 'pokemon_names' not in st.session_state:
    st.session_state.pokemon_names = []

# 回答ボタンを連続で押せなくする関数
def disable_answer():
    st.session_state.answer_disabled = True
# スタートボタンを切り替える関数
def toggle_quiz_started():
    st.session_state.quiz_started = not st.session_state.quiz_started
# スタートボタンを押した時のコールバック用の関数
def quiz_start():
    toggle_quiz_started()
    st.session_state.pokemon_names = get_random_pokemon_names()
    reset_quiz()

# PokeAPIからポケモンのデータを取得する関数
def get_pokemon_data(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# ランダムなポケモン5匹の名前を取得する関数
def get_random_pokemon_names(count=5):
    url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        all_pokemon = data['results']
        random_pokemon = random.sample(all_pokemon, count)
        return [pokemon['name'] for pokemon in random_pokemon]
    else:
        return []

# 日本語のポケモン名を取得する関数
def get_japanese_name(english_name):
    url = f"https://pokeapi.co/api/v2/pokemon-species/{english_name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for name_info in data['names']:
            if name_info['language']['name'] == 'ja-Hrkt':
                return name_info['name']
    return None

# ポケモンの見た目の画像のURLを取得する関数
def get_pokemon_sprites(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        pokemon_sprites_url = data["sprites"]["front_default"]
        return pokemon_sprites_url
    else:
        return None

# 全特性の日本語と英語の対応を取得する関数
def get_ability_translation():
    with open('all.json', 'r' ,encoding='utf-8') as f:
        return json.load(f)

# 回答と回答権を戻す関数
def reset_quiz():
    st.session_state.user_answer_types = []
    st.session_state.user_answer_abilities = []
    st.session_state.answer_disabled = False

st.title("ポケモンクイズ")
st.write("ランダムで表示されるポケモンのタイプと特性を当ててみてください！  \nタイプと特性を両方正解で１ポイント！  \n全５問のスコアが記録されます！")

if not st.session_state.quiz_started:
    st.button("スタート", on_click=quiz_start)
else:
    if st.session_state.pokemon_names:
        # ポケモンの日本語名を取得
        japanese_pokemon_name = get_japanese_name(st.session_state.pokemon_names[st.session_state.quiz_count])
        # ポケモンの画像のURLを取得
        pokemon_sprites_url = get_pokemon_sprites(st.session_state.pokemon_names[st.session_state.quiz_count])
        if japanese_pokemon_name:
            st.write(f"### {st.session_state.quiz_count + 1}問目: **{japanese_pokemon_name}**")
            st.image(pokemon_sprites_url)

            # ポケモンデータの取得
            pokemon_data = get_pokemon_data(st.session_state.pokemon_names[st.session_state.quiz_count])
            if pokemon_data:
                # ポケモンのタイプ
                pokemon_types = [t['type']['name'] for t in pokemon_data['types']]
                # ポケモンの特性
                pokemon_abilities = [a['ability']['name'] for a in pokemon_data['abilities']]
                
                # タイプの日本語と英語の対応表
                type_translation = {'ノーマル': 'normal', 'ほのお': 'fire', 'みず': 'water', 'くさ': 'grass', 'でんき': 'electric', 'こおり': 'ice', 
                                    'かくとう': 'fighting', 'どく': 'poison', 'じめん': 'ground', 'ひこう': 'flying', 'エスパー': 'psychic', 'むし': 'bug', 
                                    'いわ': 'rock', 'ゴースト': 'ghost', 'ドラゴン': 'dragon', 'あく': 'dark', 'はがね': 'steel', 'フェアリー': 'fairy'}
                # 特性の日本語と英語の対応表を取得
                ability_translation = get_ability_translation()

                # ユーザーの回答入力
                user_answer_japanese_types = st.multiselect(
                    "このポケモンのタイプは何でしょう？",
                    list(type_translation.keys())
                )
                user_answer_japanese_abilities = st.multiselect(
                    f"このポケモンの特性は何でしょう？(ヒント：特性は {len(set(pokemon_abilities))} つ)",
                    list(ability_translation.keys())
                )

                # 日本語のタイプと特性を英語に変換
                user_answer_types = [type_translation[ja_type] for ja_type in user_answer_japanese_types]
                user_answer_abilities = [ability_translation[ja_ability] for ja_ability in user_answer_japanese_abilities]

                # 回答を提出　コールバック関数で連続押下を禁止
                if st.button("回答を提出", on_click=disable_answer, disabled=st.session_state.answer_disabled):
                    types_correct = set(user_answer_types) == set(pokemon_types)
                    abilities_correct = set(user_answer_abilities) == set(pokemon_abilities)

                    partial_types_correct = set(user_answer_types).issubset(set(pokemon_types))
                    partial_abilities_correct = set(user_answer_abilities).issubset(set(pokemon_abilities))

                    # 正解のタイプと特性を日本語に変換
                    type_translation_reversed = {v: k for k, v in type_translation.items()}
                    ability_translation_reversed = {v: k for k, v in ability_translation.items()}
                    correct_japanese_types = [type_translation_reversed[en_type] for en_type in pokemon_types]
                    correct_japanese_abilities = [ability_translation_reversed[en_ability] for en_ability in pokemon_abilities]

                    if types_correct and abilities_correct:
                        st.success(f"正解です！ {japanese_pokemon_name} のタイプは {', '.join(correct_japanese_types)} で、特性は {', '.join(correct_japanese_abilities)} です。")
                        st.session_state.score += 1
                    else:
                        st.error(f"不正解です。正解は、タイプは {', '.join(correct_japanese_types)} で、特性は {', '.join(correct_japanese_abilities)} でした。")
                    #     if not user_answer_japanese_types:
                    #         st.warning("タイプが回答されていません。")
                    #     else:
                    #         if not types_correct:
                    #             if partial_types_correct:
                    #                 st.error(f"不十分です。 {japanese_pokemon_name} のタイプは {', '.join(user_answer_japanese_types)} だけではありません。")
                    #             else:
                    #                 st.error(f"タイプが不正解です。 {japanese_pokemon_name} のタイプは {', '.join(user_answer_japanese_types)} ではありません。")
                    #         else:
                    #             st.success(f"タイプは正解です！ {japanese_pokemon_name} のタイプは {', '.join(user_answer_japanese_types)} です。")

                    #     if not user_answer_japanese_abilities:
                    #         st.warning("特性が回答されていません。")
                    #     else:
                    #         if not abilities_correct:
                    #             if partial_abilities_correct:
                    #                 st.error(f"不十分です。 {japanese_pokemon_name} の特性は {', '.join(user_answer_japanese_abilities)} だけではありません。")
                    #             else:
                    #                 st.error(f"特性が不正解です。 {japanese_pokemon_name} の特性は {', '.join(user_answer_japanese_abilities)} ではありません。")
                    #         else:
                    #             st.success(f"特性は正解です！ {japanese_pokemon_name} の特性は {', '.join(user_answer_japanese_abilities)} です。")                        

                    st.session_state.quiz_count += 1

                    if st.session_state.quiz_count >= 5:
                        st.write(f"#####  あなたの最終スコアは {st.session_state.score} / 5 です。")
                        c.execute('UPDATE users SET score = ? WHERE name = ?', (st.session_state.score, name))
                        conn.commit()
                        st.session_state.quiz_count = 0
                        st.session_state.score = 0
                        st.button("終了", on_click=toggle_quiz_started)
                    else:
                        st.write(f"#####  現在のスコアは {st.session_state.score} / {st.session_state.quiz_count} です。")
                        # ボタンが押されたとき、クイズをリセット
                        st.button("次へ", on_click=reset_quiz)

                    

            else:
                st.warning("ポケモンデータの取得に失敗しました。再試行してください。")
            
        else:
            st.warning("ポケモンデータの取得に失敗しました。再試行してください。")
    else:
        st.warning("ポケモンデータの取得に失敗しました。再試行してください。")


# データベースをクローズする
conn.close()
