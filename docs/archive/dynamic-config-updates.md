# 動的設定更新機能の実装計画

## 概要

このドキュメントでは、チャットボットシステムのTOML設定ファイルに対する動的設定更新機能の実装計画を説明します。アプリケーションの再起動なしで設定を動的に更新し、変更をリアルタイムに反映させる機能を提供します。

## 動的設定更新の基本方針

1. **イベントドリブンアプローチ**: 設定ファイルの変更を監視し、変更が検出されたら自動的に設定を再読み込み
2. **設定のホットリロード**: アプリケーションの再起動なしで設定を更新
3. **変更通知**: 設定の変更を関連コンポーネントに通知
4. **ロールバック機能**: 不正な設定変更を検出した場合に自動的にロールバック
5. **変更履歴**: 設定変更の履歴を記録

## 動的設定更新機能の設計

### 設定監視マネージャークラス

```python
# config_watcher.py
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import logging
from datetime import datetime

class ConfigFileEventHandler(FileSystemEventHandler):
    """設定ファイルの変更を監視するイベントハンドラ"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        """ファイルが変更されたときに呼び出される"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() == '.toml':
                self.logger.info(f"Config file modified: {file_path}")
                self.callback(str(file_path))

class ConfigWatcher:
    """設定ファイルの変更を監視するクラス"""
    
    def __init__(self, config_path: str, callback: Callable[[str], None]):
        self.config_path = Path(config_path)
        self.callback = callback
        self.observer = Observer()
        self.logger = logging.getLogger(__name__)
        self.is_watching = False
        self.last_modified = 0
        self.debounce_interval = 1.0  # デバウンス間隔（秒）
        self.timer = None
    
    def start_watching(self):
        """設定ファイルの監視を開始"""
        try:
            # 親ディレクトリを監視
            watch_dir = self.config_path.parent
            event_handler = ConfigFileEventHandler(self._on_file_changed)
            self.observer.schedule(event_handler, str(watch_dir), recursive=False)
            self.observer.start()
            self.is_watching = True
            self.logger.info(f"Started watching config file: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to start watching config file: {e}")
    
    def stop_watching(self):
        """設定ファイルの監視を停止"""
        if self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            self.logger.info("Stopped watching config file")
    
    def _on_file_changed(self, file_path: str):
        """ファイル変更イベントを処理"""
        current_time = time.time()
        
        # デバウンス処理
        if self.timer is not None:
            self.timer.cancel()
        
        self.timer = threading.Timer(self.debounce_interval, self._process_file_change, [file_path])
        self.timer.start()
    
    def _process_file_change(self, file_path: str):
        """ファイル変更を処理"""
        try:
            # 変更されたファイルが対象の設定ファイルか確認
            if Path(file_path) == self.config_path:
                self.logger.info(f"Processing config file change: {file_path}")
                self.callback(file_path)
        except Exception as e:
            self.logger.error(f"Error processing config file change: {e}")
```

### 設定更新マネージャークラス

```python
# config_updater.py
import os
import copy
from typing import Dict, Any, List, Optional, Callable, Set
from pathlib import Path
import json
import logging
from datetime import datetime
from dataclasses import dataclass, field

from config_watcher import ConfigWatcher
from config_validation import ValidationResult
from config_models import ChatbotConfig

@dataclass
class ConfigChange:
    """設定変更を表すデータクラス"""
    timestamp: datetime
    section: str
    field: str
    old_value: Any
    new_value: Any
    user: str = "system"
    description: str = ""

@dataclass
class ConfigUpdateResult:
    """設定更新結果を表すデータクラス"""
    success: bool
    message: str
    changes: List[ConfigChange] = field(default_factory=list)
    validation_result: Optional[ValidationResult] = None

class ConfigUpdater:
    """設定を動的に更新するクラス"""
    
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.current_config = None
        self.backup_config = None
        self.change_history: List[ConfigChange] = []
        self.subscribers: Dict[str, List[Callable[[ConfigChange], None]]] = {}
        self.logger = logging.getLogger(__name__)
        self.watcher = ConfigWatcher(str(self.config_path), self._on_config_file_changed)
        self.lock = threading.RLock()
        self.max_history_size = 100
        
        # 設定の初期読み込み
        self._load_config()
    
    def start(self):
        """設定監視を開始"""
        self.watcher.start_watching()
    
    def stop(self):
        """設定監視を停止"""
        self.watcher.stop_watching()
    
    def _load_config(self):
        """設定ファイルを読み込む"""
        try:
            # 設定ファイルの読み込みロジックを実装
            # ここでは仮の実装
            self.current_config = ChatbotConfig()
            self.backup_config = copy.deepcopy(self.current_config)
            self.logger.info("Config loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            raise
    
    def _save_config(self):
        """設定をファイルに保存"""
        try:
            # 設定ファイルの保存ロジックを実装
            # ここでは仮の実装
            self.logger.info("Config saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            raise
    
    def _on_config_file_changed(self, file_path: str):
        """設定ファイルが変更されたときに呼び出される"""
        with self.lock:
            try:
                # バックアップを作成
                self.backup_config = copy.deepcopy(self.current_config)
                
                # 新しい設定を読み込む
                new_config = self._load_config_from_file(file_path)
                
                # 変更を検出
                changes = self._detect_changes(self.backup_config, new_config)
                
                if changes:
                    # 変更を適用
                    self.current_config = new_config
                    
                    # 変更履歴に追加
                    for change in changes:
                        self._add_to_history(change)
                    
                    # 変更を通知
                    self._notify_subscribers(changes)
                    
                    self.logger.info(f"Config updated with {len(changes)} changes")
                else:
                    self.logger.info("Config file changed but no actual changes detected")
            except Exception as e:
                self.logger.error(f"Error handling config file change: {e}")
                # エラーが発生した場合はバックアップから復元
                self._restore_from_backup()
    
    def _load_config_from_file(self, file_path: str) -> ChatbotConfig:
        """ファイルから設定を読み込む"""
        # 実際の実装ではTOMLファイルを読み込んでChatbotConfigオブジェクトを返す
        # ここでは仮の実装
        return ChatbotConfig()
    
    def _detect_changes(self, old_config: ChatbotConfig, new_config: ChatbotConfig) -> List[ConfigChange]:
        """2つの設定間の変更を検出"""
        changes = []
        
        # 各セクションを比較
        for section_name in old_config.__dict__:
            old_section = getattr(old_config, section_name)
            new_section = getattr(new_config, section_name)
            
            # セクション内の各フィールドを比較
            for field_name in old_section.__dict__:
                old_value = getattr(old_section, field_name)
                new_value = getattr(new_section, field_name)
                
                if old_value != new_value:
                    change = ConfigChange(
                        timestamp=datetime.now(),
                        section=section_name,
                        field=field_name,
                        old_value=old_value,
                        new_value=new_value,
                        user="system",
                        description=f"Config file changed"
                    )
                    changes.append(change)
        
        return changes
    
    def _add_to_history(self, change: ConfigChange):
        """変更を履歴に追加"""
        self.change_history.append(change)
        
        # 履歴サイズが最大値を超えた場合は古いものを削除
        if len(self.change_history) > self.max_history_size:
            self.change_history = self.change_history[-self.max_history_size:]
    
    def _notify_subscribers(self, changes: List[ConfigChange]):
        """変更をサブスクライバーに通知"""
        for change in changes:
            key = f"{change.section}.{change.field}"
            if key in self.subscribers:
                for callback in self.subscribers[key]:
                    try:
                        callback(change)
                    except Exception as e:
                        self.logger.error(f"Error notifying subscriber for {key}: {e}")
    
    def _restore_from_backup(self):
        """バックアップから設定を復元"""
        if self.backup_config is not None:
            self.current_config = copy.deepcopy(self.backup_config)
            self._save_config()
            self.logger.info("Config restored from backup")
        else:
            self.logger.error("No backup available to restore from")
    
    def update_config(self, section: str, field: str, value: Any, user: str = "api", description: str = "") -> ConfigUpdateResult:
        """設定を更新"""
        with self.lock:
            try:
                # 現在の値を取得
                old_value = self._get_config_value(section, field)
                
                # バックアップを作成
                self.backup_config = copy.deepcopy(self.current_config)
                
                # 設定を更新
                if not self._set_config_value(section, field, value):
                    return ConfigUpdateResult(
                        success=False,
                        message=f"Failed to update {section}.{field}"
                    )
                
                # 変更を検出
                new_value = self._get_config_value(section, field)
                if old_value == new_value:
                    return ConfigUpdateResult(
                        success=True,
                        message=f"No change needed for {section}.{field}"
                    )
                
                # 変更オブジェクトを作成
                change = ConfigChange(
                    timestamp=datetime.now(),
                    section=section,
                    field=field,
                    old_value=old_value,
                    new_value=new_value,
                    user=user,
                    description=description
                )
                
                # 変更履歴に追加
                self._add_to_history(change)
                
                # 設定を保存
                self._save_config()
                
                # 変更を通知
                self._notify_subscribers([change])
                
                return ConfigUpdateResult(
                    success=True,
                    message=f"Successfully updated {section}.{field}",
                    changes=[change]
                )
            except Exception as e:
                # エラーが発生した場合はバックアップから復元
                self._restore_from_backup()
                return ConfigUpdateResult(
                    success=False,
                    message=f"Error updating {section}.{field}: {str(e)}"
                )
    
    def _get_config_value(self, section: str, field: str) -> Any:
        """設定値を取得"""
        section_obj = getattr(self.current_config, section, None)
        if section_obj is not None:
            return getattr(section_obj, field, None)
        return None
    
    def _set_config_value(self, section: str, field: str, value: Any) -> bool:
        """設定値を設定"""
        try:
            section_obj = getattr(self.current_config, section, None)
            if section_obj is not None:
                setattr(section_obj, field, value)
                return True
            return False
        except Exception:
            return False
    
    def subscribe_to_changes(self, section: str, field: str, callback: Callable[[ConfigChange], None]):
        """設定変更をサブスクライブ"""
        key = f"{section}.{field}"
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)
    
    def unsubscribe_from_changes(self, section: str, field: str, callback: Callable[[ConfigChange], None]):
        """設定変更のサブスクライブを解除"""
        key = f"{section}.{field}"
        if key in self.subscribers and callback in self.subscribers[key]:
            self.subscribers[key].remove(callback)
    
    def get_change_history(self, section: Optional[str] = None, field: Optional[str] = None, 
                          limit: Optional[int] = None) -> List[ConfigChange]:
        """変更履歴を取得"""
        history = self.change_history
        
        # セクションでフィルタリング
        if section is not None:
            history = [change for change in history if change.section == section]
        
        # フィールドでフィルタリング
        if field is not None:
            history = [change for change in history if change.field == field]
        
        # 件数で制限
        if limit is not None:
            history = history[-limit:]
        
        return history
    
    def rollback_to_timestamp(self, timestamp: datetime) -> ConfigUpdateResult:
        """指定したタイムスタンプまで設定をロールバック"""
        with self.lock:
            try:
                # 指定したタイムスタンプ以前の最新の変更を取得
                changes_to_rollback = []
                for change in reversed(self.change_history):
                    if change.timestamp <= timestamp:
                        break
                    changes_to_rollback.append(change)
                
                if not changes_to_rollback:
                    return ConfigUpdateResult(
                        success=True,
                        message="No changes to rollback"
                    )
                
                # バックアップを作成
                self.backup_config = copy.deepcopy(self.current_config)
                
                # 変更をロールバック
                for change in reversed(changes_to_rollback):
                    self._set_config_value(change.section, change.field, change.old_value)
                
                # 設定を保存
                self._save_config()
                
                # ロールバックを履歴に記録
                rollback_change = ConfigChange(
                    timestamp=datetime.now(),
                    section="system",
                    field="rollback",
                    old_value="current",
                    new_value=f"rollback_to_{timestamp.isoformat()}",
                    user="system",
                    description=f"Rolled back {len(changes_to_rollback)} changes"
                )
                self._add_to_history(rollback_change)
                
                return ConfigUpdateResult(
                    success=True,
                    message=f"Successfully rolled back {len(changes_to_rollback)} changes",
                    changes=[rollback_change]
                )
            except Exception as e:
                # エラーが発生した場合はバックアップから復元
                self._restore_from_backup()
                return ConfigUpdateResult(
                    success=False,
                    message=f"Error rolling back: {str(e)}"
                )
    
    def export_config(self, export_path: str, format: str = "toml") -> bool:
        """設定をエクスポート"""
        try:
            export_file = Path(export_path)
            
            if format.lower() == "toml":
                # TOML形式でエクスポート
                pass
            elif format.lower() == "json":
                # JSON形式でエクスポート
                config_dict = self.current_config.dict()
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Config exported to {export_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, import_path: str, format: str = "toml") -> ConfigUpdateResult:
        """設定をインポート"""
        with self.lock:
            try:
                import_file = Path(import_path)
                
                if not import_file.exists():
                    return ConfigUpdateResult(
                        success=False,
                        message=f"Import file not found: {import_path}"
                    )
                
                # バックアップを作成
                self.backup_config = copy.deepcopy(self.current_config)
                
                # 設定をインポート
                if format.lower() == "toml":
                    # TOML形式からインポート
                    new_config = self._load_config_from_file(str(import_file))
                elif format.lower() == "json":
                    # JSON形式からインポート
                    with open(import_file, 'r', encoding='utf-8') as f:
                        config_dict = json.load(f)
                    new_config = ChatbotConfig(**config_dict)
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                # 変更を検出
                changes = self._detect_changes(self.current_config, new_config)
                
                # 設定を更新
                self.current_config = new_config
                
                # 変更履歴に追加
                for change in changes:
                    self._add_to_history(change)
                
                # 設定を保存
                self._save_config()
                
                # 変更を通知
                self._notify_subscribers(changes)
                
                return ConfigUpdateResult(
                    success=True,
                    message=f"Successfully imported config from {import_path}",
                    changes=changes
                )
            except Exception as e:
                # エラーが発生した場合はバックアップから復元
                self._restore_from_backup()
                return ConfigUpdateResult(
                    success=False,
                    message=f"Error importing config: {str(e)}"
                )
```

### 設定更新APIエンドポイント

```python
# api/routes/config.py
from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from config_updater import ConfigUpdater, ConfigUpdateResult, ConfigChange

router = APIRouter()
config_updater = ConfigUpdater()

# 設定更新リクエストモデル
class ConfigUpdateRequest(BaseModel):
    section: str = Field(..., description="設定セクション名")
    field: str = Field(..., description="設定フィールド名")
    value: Any = Field(..., description="設定値")
    description: str = Field("", description="変更の説明")

# 設定更新レスポンスモデル
class ConfigUpdateResponse(BaseModel):
    success: bool
    message: str
    changes: List[Dict[str, Any]] = []

# 設定取得レスポンスモデル
class ConfigGetResponse(BaseModel):
    section: str
    field: str
    value: Any

# 変更履歴レスポンスモデル
class ChangeHistoryResponse(BaseModel):
    timestamp: datetime
    section: str
    field: str
    old_value: Any
    new_value: Any
    user: str
    description: str

@router.post("/update", response_model=ConfigUpdateResponse)
async def update_config(request: ConfigUpdateRequest):
    """設定を更新"""
    try:
        result = config_updater.update_config(
            section=request.section,
            field=request.field,
            value=request.value,
            user="api",
            description=request.description
        )
        
        return ConfigUpdateResponse(
            success=result.success,
            message=result.message,
            changes=[
                {
                    "timestamp": change.timestamp.isoformat(),
                    "section": change.section,
                    "field": change.field,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "user": change.user,
                    "description": change.description
                }
                for change in result.changes
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get/{section}/{field}", response_model=ConfigGetResponse)
async def get_config(section: str, field: str):
    """設定値を取得"""
    try:
        value = config_updater._get_config_value(section, field)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Config {section}.{field} not found")
        
        return ConfigGetResponse(
            section=section,
            field=field,
            value=value
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ChangeHistoryResponse])
async def get_change_history(
    section: Optional[str] = None,
    field: Optional[str] = None,
    limit: Optional[int] = None
):
    """変更履歴を取得"""
    try:
        history = config_updater.get_change_history(section, field, limit)
        
        return [
            ChangeHistoryResponse(
                timestamp=change.timestamp,
                section=change.section,
                field=change.field,
                old_value=change.old_value,
                new_value=change.new_value,
                user=change.user,
                description=change.description
            )
            for change in history
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rollback/{timestamp}")
async def rollback_config(timestamp: str):
    """指定したタイムスタンプまで設定をロールバック"""
    try:
        target_timestamp = datetime.fromisoformat(timestamp)
        result = config_updater.rollback_to_timestamp(target_timestamp)
        
        return ConfigUpdateResponse(
            success=result.success,
            message=result.message,
            changes=[
                {
                    "timestamp": change.timestamp.isoformat(),
                    "section": change.section,
                    "field": change.field,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "user": change.user,
                    "description": change.description
                }
                for change in result.changes
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_config(
    export_path: str,
    format: str = "toml"
):
    """設定をエクスポート"""
    try:
        success = config_updater.export_config(export_path, format)
        if success:
            return {"success": True, "message": f"Config exported to {export_path}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to export config")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_config(
    import_path: str,
    format: str = "toml"
):
    """設定をインポート"""
    try:
        result = config_updater.import_config(import_path, format)
        
        return ConfigUpdateResponse(
            success=result.success,
            message=result.message,
            changes=[
                {
                    "timestamp": change.timestamp.isoformat(),
                    "section": change.section,
                    "field": change.field,
                    "old_value": change.old_value,
                    "new_value": change.new_value,
                    "user": change.user,
                    "description": change.description
                }
                for change in result.changes
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 設定変更のサブスクライバー実装例

```python
# subscribers.py
from typing import Dict, Any
from config_updater import ConfigChange, ConfigUpdater
import logging

class ConfigSubscribers:
    """設定変更のサブスクライバーを管理するクラス"""
    
    def __init__(self, config_updater: ConfigUpdater):
        self.config_updater = config_updater
        self.logger = logging.getLogger(__name__)
        self._register_subscribers()
    
    def _register_subscribers(self):
        """各種サブスクライバーを登録"""
        # LLM設定の変更を監視
        self.config_updater.subscribe_to_changes(
            "llm", "model_name", self._on_llm_model_changed
        )
        self.config_updater.subscribe_to_changes(
            "llm", "temperature", self._on_llm_temperature_changed
        )
        self.config_updater.subscribe_to_changes(
            "llm", "max_tokens", self._on_llm_max_tokens_changed
        )
        
        # Qdrant設定の変更を監視
        self.config_updater.subscribe_to_changes(
            "qdrant", "host", self._on_qdrant_host_changed
        )
        self.config_updater.subscribe_to_changes(
            "qdrant", "port", self._on_qdrant_port_changed
        )
        
        # CORS設定の変更を監視
        self.config_updater.subscribe_to_changes(
            "cors", "origins", self._on_cors_origins_changed
        )
    
    def _on_llm_model_changed(self, change: ConfigChange):
        """LLMモデルが変更されたときに呼び出される"""
        self.logger.info(f"LLM model changed from {change.old_value} to {change.new_value}")
        # LLMクライアントを再初期化するなどの処理を実装
        # 例: llm_client.reload_model(change.new_value)
    
    def _on_llm_temperature_changed(self, change: ConfigChange):
        """LLMのtemperatureが変更されたときに呼び出される"""
        self.logger.info(f"LLM temperature changed from {change.old_value} to {change.new_value}")
        # LLMクライアントの設定を更新するなどの処理を実装
        # 例: llm_client.update_temperature(change.new_value)
    
    def _on_llm_max_tokens_changed(self, change: ConfigChange):
        """LLMのmax_tokensが変更されたときに呼び出される"""
        self.logger.info(f"LLM max_tokens changed from {change.old_value} to {change.new_value}")
        # LLMクライアントの設定を更新するなどの処理を実装
        # 例: llm_client.update_max_tokens(change.new_value)
    
    def _on_qdrant_host_changed(self, change: ConfigChange):
        """Qdrantホストが変更されたときに呼び出される"""
        self.logger.info(f"Qdrant host changed from {change.old_value} to {change.new_value}")
        # Qdrantクライアントを再初期化するなどの処理を実装
        # 例: qdrant_client.reconnect(change.new_value, qdrant_client.port)
    
    def _on_qdrant_port_changed(self, change: ConfigChange):
        """Qdrantポートが変更されたときに呼び出される"""
        self.logger.info(f"Qdrant port changed from {change.old_value} to {change.new_value}")
        # Qdrantクライアントを再初期化するなどの処理を実装
        # 例: qdrant_client.reconnect(qdrant_client.host, change.new_value)
    
    def _on_cors_origins_changed(self, change: ConfigChange):
        """CORSオリジンが変更されたときに呼び出される"""
        self.logger.info(f"CORS origins changed from {change.old_value} to {change.new_value}")
        # FastAPIアプリケーションのCORS設定を更新するなどの処理を実装
        # 例: app.add_middleware(CORSMiddleware, allow_origins=change.new_value)
```

## 動的設定更新の使用例

### 基本的な使用方法

```python
# main.py
from config_updater import ConfigUpdater
from subscribers import ConfigSubscribers
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)

# 設定更新マネージャーの初期化
config_updater = ConfigUpdater("config.toml")

# サブスクライバーの登録
subscribers = ConfigSubscribers(config_updater)

# 設定監視を開始
config_updater.start()

try:
    # メインアプリケーションのループ
    while True:
        # メイン処理
        pass
except KeyboardInterrupt:
    # 終了処理
    config_updater.stop()
```

### 設定変更のプログラムからの更新

```python
# update_config_example.py
from config_updater import ConfigUpdater

# 設定更新マネージャーの初期化
config_updater = ConfigUpdater("config.toml")

# 設定を更新
result = config_updater.update_config(
    section="llm",
    field="temperature",
    value=0.8,
    user="admin",
    description="Increase temperature for more creative responses"
)

if result.success:
    print(f"Config updated successfully: {result.message}")
    for change in result.changes:
        print(f"  - {change.section}.{change.field}: {change.old_value} -> {change.new_value}")
else:
    print(f"Failed to update config: {result.message}")
```

### 設定変更の監視

```python
# monitor_config_example.py
from config_updater import ConfigUpdater, ConfigChange

def on_llm_temperature_changed(change: ConfigChange):
    print(f"LLM temperature changed: {change.old_value} -> {change.new_value}")

# 設定更新マネージャーの初期化
config_updater = ConfigUpdater("config.toml")

# 特定の設定変更を監視
config_updater.subscribe_to_changes("llm", "temperature", on_llm_temperature_changed)

# 設定監視を開始
config_updater.start()

try:
    # 監視を続ける
    while True:
        pass
except KeyboardInterrupt:
    # 終了処理
    config_updater.stop()
```

## テスト計画

### ユニットテスト

1. **設定監視のテスト**
   - ファイル変更の検出
   - デバウンス処理
   - エラーハンドリング

2. **設定更新のテスト**
   - 設定値の更新
   - 変更の検出
   - バックアップと復元

3. **変更履歴のテスト**
   - 変更履歴の記録
   - 履歴の取得とフィルタリング
   - 履歴サイズの制限

4. **ロールバック機能のテスト**
   - 特定のタイムスタンプへのロールバック
   - ロールバックの履歴記録
   - エラー時の復元

5. **サブスクライバー機能のテスト**
   - サブスクライバーの登録と解除
   - 変更通知の送信
   - エラーハンドリング

### 統合テスト

1. **設定ファイル変更のテスト**
   - ファイル変更からの自動更新
   - 複数の変更の検出
   - 不正な設定ファイルの処理

2. **API経由の設定更新テスト**
   - APIエンドポイント経由の更新
   - バリデーションエラーの処理
   - レスポンスの形式

3. **エクスポート/インポートのテスト**
   - 設定のエクスポート
   - 設定のインポート
   - 異なるフォーマット間の変換

4. **エンドツーエンドテスト**
   - 設定変更からアプリケーションへの反映までの流れ
   - エラー発生時の回復
   - パフォーマンスの評価

## 実装スケジュール

1. **設定監視機能の実装**: 1日
2. **設定更新機能の実装**: 2日
3. **変更履歴機能の実装**: 1日
4. **ロールバック機能の実装**: 1日
5. **サブスクライバー機能の実装**: 1日
6. **APIエンドポイントの実装**: 1日
7. **テストの実装**: 2日
8. **ドキュメントの更新**: 0.5日

**合計**: 9.5日