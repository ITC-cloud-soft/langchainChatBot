"""
設定ファイルの変更を監視する機能

このモジュールでは、TOML設定ファイルの変更を監視し、変更が検出されたら自動的に設定を再読み込みする機能を提供します。
"""

import os
import time
import threading
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from api.core.config_manager import ConfigManager, ConfigChange as ConfigManagerChange

logger = logging.getLogger(__name__)


class ConfigFileEventHandler(FileSystemEventHandler):
    """設定ファイルの変更を監視するイベントハンドラ"""
    
    def __init__(self, callback: Callable[[str], None]):
        """
        イベントハンドラを初期化
        
        Args:
            callback: ファイル変更時に呼び出されるコールバック関数
        """
        self.callback = callback
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        """
        ファイルが変更されたときに呼び出される
        
        Args:
            event: ファイルシステムイベント
        """
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() == '.toml':
                self.logger.info(f"Config file modified: {file_path}")
                self.callback(str(file_path))


class ConfigWatcher:
    """設定ファイルの変更を監視するクラス"""
    
    def __init__(self, config_path: str, callback: Callable[[str], None]):
        """
        設定監視クラスを初期化
        
        Args:
            config_path: 監視する設定ファイルのパス
            callback: ファイル変更時に呼び出されるコールバック関数
        """
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
        """
        ファイル変更イベントを処理
        
        Args:
            file_path: 変更されたファイルのパス
        """
        current_time = time.time()
        
        # デバウンス処理
        if self.timer is not None:
            self.timer.cancel()
        
        self.timer = threading.Timer(self.debounce_interval, self._process_file_change, [file_path])
        self.timer.start()
    
    def _process_file_change(self, file_path: str):
        """
        ファイル変更を処理
        
        Args:
            file_path: 変更されたファイルのパス
        """
        try:
            # 変更されたファイルが対象の設定ファイルか確認
            if Path(file_path) == self.config_path:
                self.logger.info(f"Processing config file change: {file_path}")
                self.callback(file_path)
        except Exception as e:
            self.logger.error(f"Error processing config file change: {e}")


@dataclass
class ConfigChange:
    """設定変更を表すデータクラス"""
    timestamp: float
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
    changes: List[ConfigChange] = None
    validation_result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.changes is None:
            self.changes = []


class ConfigUpdater:
    """設定を動的に更新するクラス"""
    
    def __init__(self, config_path: str = "config.toml"):
        """
        設定更新クラスを初期化
        
        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config_manager = ConfigManager(str(self.config_path))
        self.backup_config = None
        self.change_history: List[ConfigChange] = []
        self.subscribers: Dict[str, List[Callable[[ConfigChange], None]]] = {}
        self.logger = logging.getLogger(__name__)
        self.watcher = ConfigWatcher(str(self.config_path), self._on_config_file_changed)
        self.lock = threading.RLock()
        self.max_history_size = 100
        
        # 設定監視を開始
        self.watcher.start_watching()
    
    def stop(self):
        """設定監視を停止"""
        self.watcher.stop_watching()
    
    def _on_config_file_changed(self, file_path: str):
        """
        設定ファイルが変更されたときに呼び出される
        
        Args:
            file_path: 変更されたファイルのパス
        """
        with self.lock:
            try:
                # バックアップを作成
                self.backup_config = self.config_manager.get_config()
                
                # 新しい設定を読み込む
                new_config = self.config_manager.reload_config()
                
                # 変更を検出
                changes = self._detect_changes(self.backup_config, new_config)
                
                if changes:
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
    
    def _detect_changes(self, old_config, new_config) -> List[ConfigChange]:
        """
        2つの設定間の変更を検出
        
        Args:
            old_config: 変更前の設定
            new_config: 変更後の設定
            
        Returns:
            検出された変更のリスト
        """
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
                        timestamp=time.time(),
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
        """
        変更を履歴に追加
        
        Args:
            change: 追加する変更
        """
        self.change_history.append(change)
        
        # 履歴サイズが最大値を超えた場合は古いものを削除
        if len(self.change_history) > self.max_history_size:
            self.change_history = self.change_history[-self.max_history_size:]
    
    def _notify_subscribers(self, changes: List[ConfigChange]):
        """
        変更をサブスクライバーに通知
        
        Args:
            changes: 通知する変更のリスト
        """
        for change in changes:
            key = f"{change.section}.{change.field}"
            if key in self.subscribers:
                for callback in self.subscribers[key]:
                    try:
                        callback(change)
                    except Exception as e:
                        self.logger.error(f"Error notifying subscriber for {key}: {e}")
    
    def _restore_from_backup(self):
        """
        バックアップから設定を復元
        """
        if self.backup_config is not None:
            self.config_manager.save_config(self.backup_config)
            self.logger.info("Config restored from backup")
        else:
            self.logger.error("No backup available to restore from")
    
    def update_config(self, section: str, field: str, value: Any, user: str = "api", description: str = "") -> ConfigUpdateResult:
        """
        設定を更新
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            value: 設定値
            user: 更新ユーザー
            description: 変更の説明
            
        Returns:
            更新結果
        """
        with self.lock:
            try:
                # 現在の値を取得
                old_value = self._get_config_value(section, field)
                
                # バックアップを作成
                self.backup_config = self.config_manager.get_config()
                
                # 設定を更新
                result = self.config_manager.set_value(section, field, value, user, description)
                
                if not result.success:
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
                
                # ConfigManagerの変更を取得
                if result.changes:
                    change = result.changes[0]
                    # 変更履歴に追加
                    self._add_to_history(change)
                    
                    # 変更を通知
                    self._notify_subscribers([change])
                    
                    return ConfigUpdateResult(
                        success=True,
                        message=f"Successfully updated {section}.{field}",
                        changes=[change]
                    )
                else:
                    return ConfigUpdateResult(
                        success=True,
                        message=f"Successfully updated {section}.{field}"
                    )
            except Exception as e:
                # エラーが発生した場合はバックアップから復元
                self._restore_from_backup()
                return ConfigUpdateResult(
                    success=False,
                    message=f"Error updating {section}.{field}: {str(e)}"
                )
    
    def _get_config_value(self, section: str, field: str) -> Any:
        """
        設定値を取得
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            
        Returns:
            設定値
        """
        return self.config_manager.get_value(section, field)
    
    def subscribe_to_changes(self, section: str, field: str, callback: Callable[[ConfigChange], None]):
        """
        設定変更をサブスクライブ
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            callback: 変更通知時に呼び出されるコールバック関数
        """
        key = f"{section}.{field}"
        if key not in self.subscribers:
            self.subscribers[key] = []
        self.subscribers[key].append(callback)
    
    def unsubscribe_from_changes(self, section: str, field: str, callback: Callable[[ConfigChange], None]):
        """
        設定変更のサブスクライブを解除
        
        Args:
            section: 設定セクション名
            field: 設定フィールド名
            callback: 解除するコールバック関数
        """
        key = f"{section}.{field}"
        if key in self.subscribers and callback in self.subscribers[key]:
            self.subscribers[key].remove(callback)
    
    def get_change_history(self, section: Optional[str] = None, field: Optional[str] = None, 
                          limit: Optional[int] = None) -> List[ConfigChange]:
        """
        変更履歴を取得
        
        Args:
            section: フィルタリングするセクション名
            field: フィルタリングするフィールド名
            limit: 取得する履歴の最大数
            
        Returns:
            変更履歴のリスト
        """
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
    
    def rollback_to_timestamp(self, timestamp: float) -> ConfigUpdateResult:
        """
        指定したタイムスタンプまで設定をロールバック
        
        Args:
            timestamp: ロールバック先のタイムスタンプ
            
        Returns:
            ロールバック結果
        """
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
                self.backup_config = self.config_manager.get_config()
                
                # 変更をロールバック
                for change in reversed(changes_to_rollback):
                    self.config_manager.set_value(change.section, change.field, change.old_value, "system", f"Rollback to {timestamp}")
                
                # 設定を保存
                self.config_manager.save_config()
                
                # ロールバックを履歴に記録
                rollback_change = ConfigChange(
                    timestamp=time.time(),
                    section="system",
                    field="rollback",
                    old_value="current",
                    new_value=f"rollback_to_{timestamp}",
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
        """
        設定をエクスポート
        
        Args:
            export_path: エクスポート先のパス
            format: エクスポート形式（'toml'または'json'）
            
        Returns:
            エクスポートが成功したかどうか
        """
        return self.config_manager.export_config(export_path, format)
    
    def import_config(self, import_path: str, format: str = "toml") -> ConfigUpdateResult:
        """
        設定をインポート
        
        Args:
            import_path: インポート元のパス
            format: インポート形式（'toml'または'json'）
            
        Returns:
            インポート結果
        """
        with self.lock:
            try:
                # バックアップを作成
                self.backup_config = self.config_manager.get_config()
                
                # 設定をインポート
                result = self.config_manager.import_config(import_path, format, merge=False)
                
                if not result.success:
                    return ConfigUpdateResult(
                        success=False,
                        message=f"Failed to import config from {import_path}"
                    )
                
                # 新しい設定を取得
                new_config = self.config_manager.get_config()
                
                # 変更を検出
                changes = self._detect_changes(self.backup_config, new_config)
                
                # 変更履歴に追加
                for change in changes:
                    self._add_to_history(change)
                
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


# グローバル設定更新マネージャーインスタンス
config_updater = ConfigUpdater()