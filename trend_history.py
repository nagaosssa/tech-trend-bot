"""
トレンド履歴管理モジュール

処理の肝:
- ツール名をキーに通知済みかどうかを判定
- retention_days（デフォルト7日）より古いエントリは自動削除
- JSONファイルベースでシンプルに永続化

採用理由: DBセットアップ不要、小規模データに最適
注意点: ファイル破損リスクあり（1日1回の書き込みなので許容範囲）
"""

import json
import os
from datetime import datetime, timedelta


class TrendHistory:
    def __init__(self, path="trend_history.json", retention_days=7):
        """
        Args:
            path: 履歴ファイルのパス
            retention_days: 履歴を保持する日数（デフォルト7日）
        """
        self.path = path
        self.retention_days = retention_days
        self.history = []
        self.load()
    
    def load(self):
        """履歴ファイルを読み込む"""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = data.get("history", [])
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load history file: {e}")
                self.history = []
        else:
            self.history = []
        
        # 読み込み時に古いエントリを削除
        self.cleanup()
    
    def save(self):
        """履歴をファイルに保存"""
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"history": self.history}, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error: Failed to save history file: {e}")
    
    def is_duplicate(self, name: str) -> bool:
        """
        指定されたツール名が履歴に存在するかチェック
        
        Args:
            name: チェックするツール名
        
        Returns:
            True: 重複（既に通知済み）
            False: 新規
        """
        # 大文字小文字を無視して比較
        name_lower = name.lower()
        for entry in self.history:
            if entry.get("name", "").lower() == name_lower:
                return True
        return False
    
    def add(self, name: str, url: str = ""):
        """
        履歴にエントリを追加
        
        Args:
            name: ツール名
            url: ツールのURL
        """
        entry = {
            "name": name,
            "url": url,
            "notified_at": datetime.now().isoformat()
        }
        self.history.append(entry)
        self.save()
    
    def cleanup(self):
        """retention_daysより古いエントリを削除"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        original_count = len(self.history)
        
        new_history = []
        for entry in self.history:
            try:
                notified_at = datetime.fromisoformat(entry.get("notified_at", ""))
                if notified_at > cutoff:
                    new_history.append(entry)
            except ValueError:
                # 日付パースに失敗した場合は削除
                pass
        
        self.history = new_history
        
        removed = original_count - len(self.history)
        if removed > 0:
            print(f"Cleaned up {removed} old history entries.")
            self.save()
    
    def get_history(self) -> list:
        """現在の履歴を取得"""
        return self.history
