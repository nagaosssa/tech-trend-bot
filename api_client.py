import os
import json
import google.generativeai as genai

def _format_api_error(e):
    error_str = str(e)
    if '401' in error_str or '403' in error_str or 'API_KEY_INVALID' in error_str:
        return "認証エラー: APIキーが無効または権限がありません。"
    elif '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
        return "レート制限 (429): APIリクエストが多すぎます。"
    elif '500' in error_str or '503' in error_str:
        return "サーバーエラー: Gemini APIが一時的に利用できません。"
    
    if len(error_str) > 300:
        error_str = error_str[:300] + '...'
    return f"APIエラー: {error_str}"

class GeminiTrendClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API Key is missing. Please set it in .env.")
        
        genai.configure(api_key=self.api_key)
        
        try:
            with open("known_tools.json", "r", encoding="utf-8") as f:
                self.known_tools = json.load(f).get("known_tools", [])
        except FileNotFoundError:
            self.known_tools = []
            
    def get_available_models(self):
        """APIから利用可能なモデル一覧を取得し、最適な順にソートして返す"""
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # 'models/' プレフィックスを削除して扱う
                    name = m.name.replace('models/', '')
                    models.append(name)
            
            # Typescriptコードを参考に優先順位付け（1.5-flash > 1.5-pro > ほか）
            def score(name):
                # 最新のモデル（2.0や1.5）を優先するロジック
                if '2.0-flash' in name: return 4
                if '1.5-flash' in name: return 3
                if '1.5-pro' in name: return 2
                return 0
                
            # 非推奨モデルの除外
            models = [m for m in models if "gemini-1.0" not in m and m != "gemini-pro"]
            models.sort(key=score, reverse=True)
            return models
        except Exception as e:
            print(f"Warning: Failed to list models: {e}")
            # フォールバック
            return ['gemini-1.5-flash', 'gemini-1.5-pro']

    def get_daily_trends(self, category="Dev Tools", target_languages=None):
        known_tools_str = ", ".join(self.known_tools)
        targets_str = f"ターゲット: {target_languages}" if target_languages else "ターゲット: TypeScript, PHP, AWS, 新興AIツール"
        
        system_prompt = f"""
        あなたは「テックトレンドスカウト」です。
        ユーザーのために、以下の3つの異なる視点で、合計で**ちょうど3つ**の有益な情報を提案してください。

        # ユーザーの「既知のツール」リスト:
        [{known_tools_str}]
        ※注意: これらのツールを「新しい発見（Alpha Trend/Hidden Gem）」として提案しないでください。
        ※例外: 「Power Tip」枠では、これらのツールのプラグインや拡張機能を提案してください。

        # 提案の3本柱（必ず各1つずつ含めること）:
        1. **Alpha Trend (最新トレンド)**: 過去24〜48時間以内にGitHub Trending等で話題になった新ツール。{targets_str}
        2. **Power Tip (活用術・拡張)**: 既知のツールを強化するプラグイン・設定。
        3. **Hidden Gem (隠れた名作)**: プロが愛用するがあまり知られていないツール。

        以下のJSON形式のみで回答してください:
        {{
            "date": "今日の日付",
            "trends": [
                {{
                    "name": "ツール/トピック名",
                    "description": "概要（日本語）。なぜこれが有益か？",
                    "url": "URL",
                    "buzz_factor": "【Alpha Trend】 / 【Power Tip】 / 【Hidden Gem】 のいずれかを記載"
                }}
            ],
            "one_line_summary": "今日の3カテゴリのハイライト要約"
        }}
        """

        prompt = f"{system_prompt}\n\n上記の指示に従い、{category}分野におけるトレンドと情報を検索・生成してください。"
        
        models_to_try = self.get_available_models()
        last_error = None
        
        for model_name in models_to_try:
            print(f"Trying model: {model_name}")
            try:
                # ツールにGoogle検索をセット。モデルによってはサポートされない可能性があるため、エラー時は次のモデルへ
                model = genai.GenerativeModel(
                    model_name=model_name
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                    )
                )
                
                content = response.text
                content = content.replace('```json', '').replace('```', '').strip()
                return json.loads(content)

            except Exception as e:
                print(f"Failed with model {model_name}: {e}")
                last_error = e
                # エラーが起きてもループを継続し、次のモデルでリトライする
                
        return {"error": _format_api_error(last_error) if last_error else "All models failed."}
