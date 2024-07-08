import streamlit as st
import requests
import random
import json


# # ユーザー名: スコア
# # ユーザー辞書の初期化
# if 'users' not in st.session_state:
#     st.session_state.users = {}

# # ユーザー名を入力
# username = st.sidebar.text_input("ユーザー名を入力してください")

# if st.sidebar.button('追加する'):
#     if username:
#         if username not in st.session_state.users:
#             st.session_state.users[username] = 0
#             st.sidebar.success(f"ようこそ{username}さん！")
#         else :
#             st.sidebar.success(f"{username}さんはすでに登録されています")
#         st.sidebar.write(f"あなたのスコアは{st.session_state.users[username]}です")
#     else:
#         st.sidebar.error("ユーザー名が入力されていません")
        

# PokeAPIからポケモンのデータを取得する関数
def get_pokemon_data(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# ランダムなポケモンの名前を取得する関数
def get_random_pokemon_name():
    url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        all_pokemon = data['results']
        random_pokemon = random.choice(all_pokemon)
        return random_pokemon['name']
    else:
        return None

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
    # url = "https://pokeapi.co/api/v2/ability?limit=307"
    # response = requests.get(url)
    # if response.status_code == 200:
    #     data = response.json()
    #     abilities = data['results']
    #     ability_translation = {}
    #     for ability in abilities:
    #         ability_response = requests.get(ability['url'])
    #         if ability_response.status_code == 200:
    #             ability_data = ability_response.json()
    #             english_name = ability_data['name']
    #             for name_info in ability_data['names']:
    #                 if name_info['language']['name'] == 'ja-Hrkt':
    #                     japanese_name = name_info['name']
    #                     ability_translation[japanese_name] = english_name
    #     return ability_translation
    # else:
    #     return {}
    with open('all.json', 'r') as f:
        return json.load(f)

st.title("ポケモンクイズ")
st.write("ランダムなポケモンのタイプと特性を当ててみてください！")

# セッション状態にポケモンの名前が保存されていない場合、新しいポケモンを取得
if 'pokemon_name' not in st.session_state or st.session_state.pokemon_name is None:
    st.session_state.pokemon_name = get_random_pokemon_name()

# セッション状態に特性の翻訳が保存されていない場合、取得して保存
# if 'ability_translation' not in st.session_state:
#     st.session_state.ability_translation = get_ability_translation()

# リセットボタンが押されたとき、新しいポケモンを取得
if st.button("新しいクイズを表示"):
    st.session_state.pokemon_name = get_random_pokemon_name()
    st.session_state.user_answer_types = []
    st.session_state.user_answer_abilities = []

# セッション状態からポケモンの名前を取得
pokemon_name = st.session_state.get('pokemon_name')
# ポケモンの画像のURLを取得
pokemon_sprites_url = get_pokemon_sprites(pokemon_name)

if pokemon_name:
    japanese_pokemon_name = get_japanese_name(pokemon_name)
    if japanese_pokemon_name:
        st.write(f"### ポケモン名: **{japanese_pokemon_name}**")
        st.image(pokemon_sprites_url)

        # ポケモンデータの取得
        pokemon_data = get_pokemon_data(pokemon_name)
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
                "このポケモンの特性は何でしょう？",
                list(ability_translation.keys())
            )

            # 日本語のタイプと特性を英語に変換
            user_answer_types = [type_translation[ja_type] for ja_type in user_answer_japanese_types]
            user_answer_abilities = [ability_translation[ja_ability] for ja_ability in user_answer_japanese_abilities]

            if st.button("回答を確認"):
                types_correct = set(user_answer_types) == set(pokemon_types)
                abilities_correct = set(user_answer_abilities) == set(pokemon_abilities)
                
                if types_correct and abilities_correct:
                    st.success(f"正解です！ {japanese_pokemon_name} のタイプは {', '.join(user_answer_japanese_types)} で、特性は {', '.join(user_answer_japanese_abilities)} です。")
                else:
                    if not types_correct:
                        st.error(f"タイプが不正解です。 {japanese_pokemon_name} のタイプは {', '.join(user_answer_japanese_types)} ではありません。")
                    if not abilities_correct:
                        st.error(f"特性が不正解です。 {japanese_pokemon_name} の特性は {', '.join(user_answer_japanese_abilities)} ではありません。")
        else:
            st.error("ポケモンデータの取得に失敗しました。再試行してください。")
        
    else:
        st.error("ポケモンの日本語名の取得に失敗しました。再試行してください。")
else:
    st.error("ポケモンデータの取得に失敗しました。再試行してください。")


