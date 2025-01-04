import streamlit as st
import random
import time

# ゲームの状態を管理する変数
if 'game_started' not in st.session_state:
    st.session_state.game_started = False
if 'current_word_index' not in st.session_state:
    st.session_state.current_word_index = 0
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = 0
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0
if 'words' not in st.session_state:
    st.session_state.words = []

# ゲーム開始ボタンと途中中止ボタンを定義
st.markdown("<h1 style='color:white;'>PokeType!</h1>", unsafe_allow_html=True)
start_game_button = st.button('ゲーム開始')
stop_game_button = st.button('途中中止')

# HTMLとJSでゲームロジックを組み込む部分
game_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Typing Game</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: white;}
        .word { font-size: 30px; font-weight: bold; }
        .typed { color: gray; }
        .highlight { color: black; }
        #result { display: none; }
        #problem-info { font-size:20px; font-weight:bold;}
        #result-table {margin: 0 auto;}

        /* アイコンを回転させるアニメーション */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* ローディング用のアイコンのスタイル */
        .spinner {
            display: inline-block;
            width: 20px; /* アイコンの幅 */
            height: 20px; /* アイコンの高さ */
            border: 3px solid rgba(0, 0, 0, 0.1); /* 外側の薄い円 */
            border-top: 3px solid #3498db; /* 上部の濃い円 */
            border-radius: 50%; /* 円形にする */
            animation: spin 1s linear infinite; /* 回転アニメーション */
            margin-right: 8px; /* アイコンとテキストの間隔 */
        }
        #load {color: red;}

        /* フォーカス時にカスタムボーダーを使用する */
        *:focus {
        outline: none;
        box-shadow: 0 0 0 2px rgba(169, 169, 169, 0.3); /* 灰色のシャドウ */
        }
    </style>
</head>
<body>
    <div id="game-container" tabindex="0">
        <div id="problem-info">
            <span>問題 <span id="current-problem">1</span> / <span id="total-problems">10</span></span>
        </div>
        <br>
        <span id = "loadIcon" class="spinner"></span>
        <span id = "load">ポケモン取得中</span>
        <div id="countdown" style="font-size: 50px;"></div>
        <div id="word-display" class="word"></div>
        <div id="poke-image"></div>
        <div id="typed-display" class="word"></div>
        <div id="stats">
            <p>経過時間: <span id="time-elapsed">0</span>秒</p>
            <p>ミスタイプ数: <span id="mistakes">0</span></p>
        </div>
        <div id="result" style="display:none; margin: 0 auto;">
            <h2 style="background-color: #197f5c; color: white;">結果</h2>
            <p>総経過時間: <span id="final-time"></span>秒</p>
            <p>総ミスタイプ数: <span id="final-mistakes"></span></p>
            <table id="result-table">
                <thead>
                    <tr>
                        <th>単語</th>
                        <th>完了時間</th>
                        <th>ミスタイプ数</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- 結果がここに追加されます -->
                </tbody>
            </table>
            <div id="poke-images-container" style="text-align: center; margin-top: 20px;">
                <!-- ポケモン画像がここに追加されます -->
            </div>
        </div>
    </div>
    <script>
        let currentWordIndex = 0;
        let startTime = 0;
        let mistakes = 0;
        let words = [];
        let images = [];
        let Japaneses = [];
        let timer;
        let elapsedTime = 0;
        let wordStats = []; // 各単語のステータスを格納する配列
        let wordStartTime = []; // 各単語が出題された時刻を記録

        // ランダムなポケモンを10匹取得する関数
        async function getRandomPokemon() {
            const pokemonList = [];
            
            // 10回繰り返してランダムなポケモンを取得
            for (let i = 0; i < 10; i++) {
                const randomId = Math.floor(Math.random() * 898) + 1;

                try {
                    const response = await fetch(`https://pokeapi.co/api/v2/pokemon/${randomId}/`);
                    const data = await response.json();

                    const pokemonName = data.name;
                    const pokemonJapaneseName = await getPokemonJapaneseName(data.species.url);
                    const pokemonImage = data.sprites.front_default;

                    pokemonList.push({ 
                        name: pokemonName, 
                        japaneseName: pokemonJapaneseName, 
                        image: pokemonImage 
                    });

                    words.push(pokemonName);  // pokemonNameをwordsに追加
                    images.push(pokemonImage); // pokemonImageをimagesに追加
                    Japaneses.push(pokemonJapaneseName);

                } catch (error) {
                    console.error(`ポケモンID ${randomId} の情報取得に失敗しました:`, error);
                }
            }
            // すべてのポケモンのデータが取得できた後にゲームを開始
            fetchWords(); // ゲーム開始
        }

        // 日本語名を取得する関数
        async function getPokemonJapaneseName(speciesUrl) {
            try {
                const speciesResponse = await fetch(speciesUrl);
                const speciesData = await speciesResponse.json();
                const names = speciesData.names;
                const japaneseName = names.find(name => name.language.name === 'ja');
                return japaneseName ? japaneseName.name : '名前なし';
            } catch (error) {
                console.error('日本語名の取得に失敗しました:', error);
                return '名前なし';
            }
        }

        // POKEMON画像を表示する関数
        function displayPokemonImage() {
            // 画像を表示するためのHTMLを生成
            const pokeImageDiv = document.getElementById('poke-image');
            pokeImageDiv.innerHTML = '';  // 以前の画像を消去

            // images配列の最初の画像を取得
            const img = document.createElement('img');
            img.src = images[currentWordIndex];  // 現在の単語に対応する画像
            img.alt = 'Pokemon Image';
            img.style.width = '150px';  // 画像サイズを指定（必要に応じて変更）

            // divに画像を追加
            pokeImageDiv.appendChild(img);
        }
        
        // ゲーム開始時に単語リストを取得
        async function fetchWords() {
            currentWordIndex = 0;

            // 単語リストの長さに合わせてwordStatsを初期化
            wordStats = words.map(() => ({ mistakes: 0, finishTime: null }));
            wordStartTime = new Array(words.length).fill(null); // 各単語の表示時刻を初期化

            startGame();
        }

        function startGame() {
            document.getElementById('load').style.display = 'none';
            document.getElementById('loadIcon').style.display = 'none';
            document.getElementById('countdown').style.display = 'block';
            let countdown = 3;
            let countdownInterval = setInterval(function() {
                document.getElementById('countdown').innerText = countdown;
                countdown--;
                if (countdown < 0) {
                    clearInterval(countdownInterval);
                    startTime = Date.now();
                    document.getElementById('countdown').style.display = 'none';
                    showWord();
                    startTimer();  // ゲーム開始と同時に経過時間をカウント開始
                }
            }, 1000);
        }

        function showWord() {
            if (currentWordIndex < words.length) {
                document.getElementById('word-display').innerText = words[currentWordIndex];
                document.getElementById('typed-display').innerText = '';
                displayPokemonImage();
                updateProblemInfo();  // 現在の問題番号と総問題数を更新
                wordStartTime[currentWordIndex] = Date.now(); // 単語が表示された時刻を記録
                startTyping();
            } else {
                endGame();
            }
        }

        function startTyping() {
            // フォーカスを入力エリアに移動
            document.getElementById('game-container').click();
            document.getElementById('game-container').focus();
            document.addEventListener('keydown', handleKeyPress);
        }

        function handleKeyPress(event) {
            const currentWord = words[currentWordIndex];
            const typedText = document.getElementById('typed-display').innerText;

            // currentWordIndex がwordStatsの範囲内であることを確認
            if (currentWordIndex >= wordStats.length) {
                console.error('currentWordIndexがwordStatsの範囲外です');
                return;
            }

            // ミスタイプ処理
            if (event.key !== currentWord[typedText.length]) {
                mistakes++;
                wordStats[currentWordIndex].mistakes++; // ミスタイプ数を更新
                document.getElementById('mistakes').innerText = mistakes;

                // 画面を赤くする
                document.body.style.backgroundColor = 'red';
                
                // ミスタイプ音を鳴らす
                new Audio('https://www.soundjay.com/buttons/sounds/button-09a.wav').play();  

                // 一定時間後に背景色を元に戻す
                setTimeout(() => {
                    document.body.style.backgroundColor = '';  // 背景色を元に戻す
                }, 300);  // 0.3秒後に元に戻す
            }

            // 正しい文字を追加
            if (event.key === currentWord[typedText.length]) {
                document.getElementById('typed-display').innerText = typedText + event.key;
            }

            // 単語を完全に入力した場合
            if (typedText.length + 1 === currentWord.length) {
                wordStats[currentWordIndex].finishTime = Math.floor((Date.now() - wordStartTime[currentWordIndex]) / 1000); // タイプ完了時間を記録
                currentWordIndex++;
                showWord();
            }
        }

        function startTimer() {
            timer = setInterval(function() {
                // 経過時間を更新
                elapsedTime = Math.floor((Date.now() - startTime) / 1000);
                document.getElementById('time-elapsed').innerText = elapsedTime; // 時間を表示
            }, 1000);  // 毎秒経過時間を更新
        }

        function updateProblemInfo() {
            // 現在の問題番号と総問題数を更新
            document.getElementById('current-problem').innerText = currentWordIndex + 1;
            document.getElementById('total-problems').innerText = words.length;
        }

        function displayPokemonResultImages() {
            const pokeImagesContainer = document.getElementById('poke-images-container');
            pokeImagesContainer.innerHTML = '';  // 以前の画像を消去

            // 4個ずつの2行で表示
            let row = document.createElement('div');
            row.style.display = 'flex';
            row.style.justifyContent = 'center';
            row.style.marginBottom = '10px';  // 行間を調整

            // images 配列を4個ずつ分けて表示
            for (let i = 0; i < images.length; i++) {
                if (i % 4 === 0 && i !== 0) {
                    // 4個ごとに新しい行を追加
                    pokeImagesContainer.appendChild(row);
                    row = document.createElement('div');
                    row.style.display = 'flex';
                    row.style.justifyContent = 'center';
                    row.style.marginBottom = '10px';
                }

                // 画像を作成
                const imgContainer = document.createElement('div');
                imgContainer.style.margin = '0 10px';  // 画像間の余白

                const img = document.createElement('img');
                img.src = images[i];
                img.alt = 'Pokemon Image';
                img.style.width = '100px';  // 画像サイズを指定

                // 名前フォーマット: 英名/日本語名
                const name = document.createElement('p');
                name.innerText = `${words[i]} / ${Japaneses[i]}`;  // 英名/日本語名を表示

                imgContainer.appendChild(img);
                imgContainer.appendChild(name);

                row.appendChild(imgContainer);
            }

            // 最後の行を追加
            pokeImagesContainer.appendChild(row);
        }

        function endGame() {
            clearInterval(timer);
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            document.getElementById('time-elapsed').innerText = elapsed;
            document.getElementById('final-time').innerText = elapsed;
            document.getElementById('final-mistakes').innerText = mistakes;

            // 結果画面に各単語のステータスを表示
            const resultTable = document.getElementById('result-table');
            words.forEach((word, index) => {
                const row = resultTable.insertRow();
                const wordCell = row.insertCell(0);
                const timeCell = row.insertCell(1);
                const mistakesCell = row.insertCell(2);

                wordCell.innerText = word;
                timeCell.innerText = wordStats[index].finishTime ? wordStats[index].finishTime + 's' : '未完了';
                mistakesCell.innerText = wordStats[index].mistakes;
            });

            // ポケモン画像を表示
            displayPokemonResultImages();  // 結果表示後に画像を表示

            document.getElementById('result').style.display = 'block';
        }

        getRandomPokemon();  // POKEAPIからポケモンを10匹取得してゲームを開始
    
    </script>
</body>
</html>
"""

# StreamlitでHTMLを表示
if start_game_button:
    st.session_state.game_started = True
    st.session_state.words = []  # ゲーム開始時に単語リストを初期化
    st.components.v1.html(game_html, height=1400)

# ゲームが開始されていない場合は何も表示しない
if not st.session_state.game_started:
    st.write("ゲームを開始するには、ボタンを押してください。")
