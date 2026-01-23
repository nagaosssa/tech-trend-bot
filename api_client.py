import os
from openai import OpenAI
import json

class PerplexityClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API Key is missing. Please set it in .env or pass it to the constructor.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Load known tools
        try:
            with open("known_tools.json", "r", encoding="utf-8") as f:
                self.known_tools = json.load(f).get("known_tools", [])
        except FileNotFoundError:
            self.known_tools = []

    def get_proposals(self, user_goal):
        """
        Generates search queries and tool recommendations based on user goal.
        """
        system_prompt = """
        You are an expert digital consultant. Your goal is to help the user achieve their objective by providing:
        1. STRATEGIC SEARCH QUERIES: 3-5 specific, high-quality web search queries to find deep information, tutorials, or hidden gems.
        2. TOOL & SERVICE RECOMMENDATIONS: 3 specific tools, software, or services (SaaS, AI, etc.) that significantly improve efficiency for this goal.
        
        Return the response in the following JSON format ONLY:
        {
            "search_queries": [
                {"query": "query 1", "reason": "why this is useful"},
                ...
            ],
            "recommendations": [
                {"name": "Tool Name", "type": "SaaS/AI/Extension", "description": "Brief focused description", "reason": "Why it helps this specific user goal"},
                ...
            ],
            "summary_advice": "A brief strategic advice paragraph."
        }
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"My goal is: {user_goal}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model="sonar-pro",
                messages=messages
            )
            
            content = response.choices[0].message.content
            # Ensure we get clean JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(content[start:end])
            return json.loads(content)

        except Exception as e:
            return {"error": str(e)}

    def get_daily_trends(self, category="Dev Tools, PKM, Privacy Browsers, & Student Deals"):
        """
        Searches for trending tools/libraries in the specified category within the last 24h.
        Includes 3 distinct types (Alpha Trend, Power Tip, Hidden Gem).
        """
        known_tools_str = ", ".join(self.known_tools)
        
        system_prompt = f"""
        あなたは「テックトレンドスカウト」です。
        ユーザーのために、以下の3つの異なる視点で、合計で**ちょうど3つ**の有益な情報を提案してください。

        # ユーザーの「既知のツール」リスト:
        [{known_tools_str}]
        ※注意: これらのツールそのものを「新しい発見（Alpha Trend/Hidden Gem）」として提案してはいけません。
        ※例外: 「Power Tip」枠では、これらのツールのプラグインや拡張機能を提案してください。

        # 提案の3本柱（必ず各1つずつ含めること）:
        1. **Alpha Trend (最新トレンド)**:
           - 過去24〜48時間以内にGitHub Trending (英語) や Hacker Newsで火がついたばかりの「誰も知らない」ツール。
           - ターゲット: TypeScript, PHP, AWS, 新興AIツール。
        
        2. **Power Tip (活用術・拡張)**:
           - ユーザーの「既知のツール」（特にObsidian, Brave, Notion）を強化するプラグイン、拡張機能、または高度な設定。
           - 「Antygravity」や「Brave拡張」などのような、既存環境をパワーアップさせるもの。

        3. **Hidden Gem (隠れた名作)**:
           - リリースから時間は経っているが、ユーザーがまだ認知していないであろう「渋い」「便利」なツール。
           - Overleafのように実用的で、プロフェッショナルが愛用するもの。

        # 制約事項:
        - 結果は日本語で出力してください。
        - 各項目の `buzz_factor` には、それが「Alpha Trend」なのか「Power Tip」なのか「Hidden Gem」なのかを明記してください。

        以下のJSON形式のみで回答してください:
        {{
            "date": "今日の日付",
            "trends": [
                {{
                    "name": "ツール/トピック名",
                    "description": "概要（日本語）。なぜこれが有益か？",
                    "url": "URL",
                    "buzz_factor": "【Alpha Trend】 / 【Power Tip】 / 【Hidden Gem】 のいずれかを記載"
                }},
                ... (合計3つ)
            ],
            "one_line_summary": "今日の3カテゴリのハイライト要約（1文）"
        }}
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Find 3 'Alpha' tech trends/tools from GitHub Trending (English) or Hacker News related to {category} in the last 24h."}
        ]

        try:
            response = self.client.chat.completions.create(
                model="sonar-pro",
                messages=messages
            )
            
            content = response.choices[0].message.content
            # Ensure we get clean JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(content[start:end])
            return json.loads(content)

        except Exception as e:
            return {"error": str(e)}

