"""
Novu統合テスト実行スクリプト

すべてのテストを実行し、包括的なレポートを生成します。
"""
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
NOVU_INTEGRATION_ROOT = PROJECT_ROOT / "novu-integration"


class TestRunner:
    """テスト実行クラス"""
    
    def __init__(self):
        self.results = {
            "backend": {},
            "frontend": {},
            "e2e": {},
            "summary": {}
        }
        self.start_time = datetime.now()
    
    def run_backend_tests(self):
        """バックエンドテストを実行"""
        print("\n" + "="*80)
        print("🔧 バックエンドテスト実行中...")
        print("="*80)
        
        try:
            # Pytestを実行
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(BACKEND_ROOT / "tests" / "test_novu_integration.py"),
                    "-v",
                    "--tb=short",
                    "--json-report",
                    "--json-report-file=backend_test_report.json"
                ],
                cwd=str(BACKEND_ROOT),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            self.results["backend"]["returncode"] = result.returncode
            self.results["backend"]["stdout"] = result.stdout
            self.results["backend"]["stderr"] = result.stderr
            
            # JSONレポートを読み込む
            report_file = BACKEND_ROOT / "backend_test_report.json"
            if report_file.exists():
                with open(report_file, 'r', encoding='utf-8') as f:
                    self.results["backend"]["report"] = json.load(f)
            
            if result.returncode == 0:
                print("✅ バックエンドテスト: 成功")
            else:
                print("❌ バックエンドテスト: 失敗")
                print(f"\n出力:\n{result.stdout}")
                if result.stderr:
                    print(f"\nエラー:\n{result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ バックエンドテスト: タイムアウト")
            self.results["backend"]["error"] = "Timeout"
            return False
        except Exception as e:
            print(f"❌ バックエンドテスト: エラー - {str(e)}")
            self.results["backend"]["error"] = str(e)
            return False
    
    def run_frontend_tests(self):
        """フロントエンドテストを実行"""
        print("\n" + "="*80)
        print("🎨 フロントエンドテスト実行中...")
        print("="*80)
        
        try:
            # Vitestを実行
            result = subprocess.run(
                [
                    "npm",
                    "run",
                    "test:unit",
                    "--",
                    "src/tests/novu"
                ],
                cwd=str(FRONTEND_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
                shell=True
            )
            
            self.results["frontend"]["returncode"] = result.returncode
            self.results["frontend"]["stdout"] = result.stdout
            self.results["frontend"]["stderr"] = result.stderr
            
            if result.returncode == 0:
                print("✅ フロントエンドテスト: 成功")
            else:
                print("❌ フロントエンドテスト: 失敗")
                print(f"\n出力:\n{result.stdout}")
                if result.stderr:
                    print(f"\nエラー:\n{result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ フロントエンドテスト: タイムアウト")
            self.results["frontend"]["error"] = "Timeout"
            return False
        except Exception as e:
            print(f"❌ フロントエンドテスト: エラー - {str(e)}")
            self.results["frontend"]["error"] = str(e)
            return False
    
    def run_e2e_tests(self):
        """E2Eテストを実行"""
        print("\n" + "="*80)
        print("🔗 E2Eテスト実行中...")
        print("="*80)
        
        try:
            # E2Eテストスクリプトを実行
            result = subprocess.run(
                [
                    sys.executable,
                    str(NOVU_INTEGRATION_ROOT / "tests" / "e2e_integration_test.py")
                ],
                cwd=str(NOVU_INTEGRATION_ROOT / "tests"),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            self.results["e2e"]["returncode"] = result.returncode
            self.results["e2e"]["stdout"] = result.stdout
            self.results["e2e"]["stderr"] = result.stderr
            
            # JSONレポートを読み込む
            for report_file in (NOVU_INTEGRATION_ROOT / "tests").glob("novu_test_report_*.json"):
                with open(report_file, 'r', encoding='utf-8') as f:
                    self.results["e2e"]["report"] = json.load(f)
                break
            
            print(result.stdout)
            
            if result.returncode == 0:
                print("✅ E2Eテスト: 成功")
            else:
                print("❌ E2Eテスト: 失敗")
                if result.stderr:
                    print(f"\nエラー:\n{result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("❌ E2Eテスト: タイムアウト")
            self.results["e2e"]["error"] = "Timeout"
            return False
        except Exception as e:
            print(f"❌ E2Eテスト: エラー - {str(e)}")
            self.results["e2e"]["error"] = str(e)
            return False
    
    def generate_coverage_report(self):
        """カバレッジレポートを生成"""
        print("\n" + "="*80)
        print("📊 カバレッジレポート生成中...")
        print("="*80)
        
        # バックエンドカバレッジ
        try:
            print("\n🔧 バックエンドカバレッジ...")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(BACKEND_ROOT / "tests" / "test_novu_integration.py"),
                    "--cov=api.adapters.novu_adapter",
                    "--cov=api.services.notification_service",
                    "--cov-report=html:coverage_backend",
                    "--cov-report=json:coverage_backend.json",
                    "--cov-report=term"
                ],
                cwd=str(BACKEND_ROOT),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print(result.stdout)
            
            # カバレッジデータを読み込む
            coverage_file = BACKEND_ROOT / "coverage_backend.json"
            if coverage_file.exists():
                with open(coverage_file, 'r', encoding='utf-8') as f:
                    self.results["backend"]["coverage"] = json.load(f)
            
        except Exception as e:
            print(f"⚠️  バックエンドカバレッジ生成エラー: {str(e)}")
        
        # フロントエンドカバレッジ
        try:
            print("\n🎨 フロントエンドカバレッジ...")
            result = subprocess.run(
                [
                    "npm",
                    "run",
                    "test:coverage",
                    "--",
                    "src/tests/novu"
                ],
                cwd=str(FRONTEND_ROOT),
                capture_output=True,
                text=True,
                timeout=300,
                shell=True
            )
            
            print(result.stdout)
            
        except Exception as e:
            print(f"⚠️  フロントエンドカバレッジ生成エラー: {str(e)}")
    
    def generate_final_report(self):
        """最終レポートを生成"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # サマリーを計算
        backend_passed = self.results["backend"].get("returncode") == 0
        frontend_passed = self.results["frontend"].get("returncode") == 0
        e2e_passed = self.results["e2e"].get("returncode") == 0
        
        all_passed = backend_passed and frontend_passed and e2e_passed
        
        self.results["summary"] = {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": duration,
            "backend_passed": backend_passed,
            "frontend_passed": frontend_passed,
            "e2e_passed": e2e_passed,
            "all_passed": all_passed
        }
        
        # レポートファイルに保存
        report_file = NOVU_INTEGRATION_ROOT / "tests" / f"full_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        # コンソール出力
        print("\n" + "="*80)
        print("📋 最終テストレポート")
        print("="*80)
        print(f"開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"終了時刻: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"実行時間: {duration:.2f}秒")
        print()
        print("テスト結果:")
        print(f"  🔧 バックエンド: {'✅ 成功' if backend_passed else '❌ 失敗'}")
        print(f"  🎨 フロントエンド: {'✅ 成功' if frontend_passed else '❌ 失敗'}")
        print(f"  🔗 E2E: {'✅ 成功' if e2e_passed else '❌ 失敗'}")
        print()
        print(f"総合結果: {'✅ すべて成功' if all_passed else '❌ 一部失敗'}")
        print()
        print(f"📄 詳細レポート: {report_file}")
        print("="*80)
        
        return all_passed
    
    def run_all(self):
        """すべてのテストを実行"""
        print("="*80)
        print("🚀 Novu統合テスト実行開始")
        print("="*80)
        print(f"開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # テスト実行
        backend_success = self.run_backend_tests()
        frontend_success = self.run_frontend_tests()
        e2e_success = self.run_e2e_tests()
        
        # カバレッジレポート生成
        self.generate_coverage_report()
        
        # 最終レポート生成
        all_passed = self.generate_final_report()
        
        return all_passed


def main():
    """メイン実行"""
    runner = TestRunner()
    all_passed = runner.run_all()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
