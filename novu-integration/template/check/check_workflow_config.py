"""
ワークフローの設定を確認するスクリプト

ボタンURLが正しく設定されているか確認します。
"""

import requests
import os
import json

NOVU_API_KEY = os.getenv("NOVU_API_KEY", "c47cfb7a083c4e27f9d1b523a20ed59f")
NOVU_API_URL = os.getenv("NOVU_API_URL", "http://localhost:3000")


def get_workflow_by_id(workflow_id: str):
    """ワークフローIDで詳細を取得"""
    
    url = f"{NOVU_API_URL}/v1/workflows/{workflow_id}"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 取得失敗: {response.status_code}")
            print(f"   エラー: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def list_all_workflows():
    """すべてのワークフローを取得"""
    
    url = f"{NOVU_API_URL}/v1/workflows"
    
    headers = {
        "Authorization": f"ApiKey {NOVU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ 取得失敗: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def check_workflow_buttons(workflow_data):
    """ワークフローのボタン設定を確認"""
    
    workflow = workflow_data.get('data', {})
    name = workflow.get('name', 'N/A')
    workflow_id = workflow.get('_id', 'N/A')
    identifier = workflow.get('triggers', [{}])[0].get('identifier', 'N/A')
    
    print(f"\n{'='*60}")
    print(f"ワークフロー: {name}")
    print(f"{'='*60}")
    print(f"ID: {workflow_id}")
    print(f"識別子: {identifier}")
    print(f"ステータス: {'Active' if workflow.get('active') else 'Inactive'}")
    
    # ステップを確認
    steps = workflow.get('steps', [])
    
    if not steps:
        print("\n⚠️  ステップが見つかりません")
        return
    
    for i, step in enumerate(steps, 1):
        template = step.get('template', {})
        step_type = template.get('type', 'unknown')
        
        print(f"\n📋 ステップ {i}: {step_type}")
        
        if step_type == 'in_app':
            # In-App通知の詳細を表示
            subject = template.get('subject', 'N/A')
            content = template.get('content', 'N/A')
            
            print(f"   Subject: {subject}")
            print(f"   Content: {content[:50]}..." if len(content) > 50 else f"   Content: {content}")
            
            # CTA（ボタン）設定を確認
            cta = template.get('cta', {})
            
            if cta:
                print(f"\n   🔘 CTA設定が見つかりました:")
                print(f"   {json.dumps(cta, indent=6, ensure_ascii=False)}")
                
                # ボタンを解析
                action = cta.get('action', {})
                buttons = action.get('buttons', [])
                
                if buttons:
                    print(f"\n   ✅ ボタン設定:")
                    for btn in buttons:
                        btn_type = btn.get('type', 'unknown')
                        label = btn.get('content', 'N/A')
                        url = btn.get('url', 'N/A')
                        print(f"      • {btn_type.upper()}: '{label}' → {url}")
                else:
                    print(f"\n   ⚠️  ボタンが設定されていません")
                
                # Redirect URLを確認
                redirect_data = cta.get('data', {})
                redirect_url = redirect_data.get('url')
                if redirect_url:
                    print(f"\n   🔗 Redirect URL: {redirect_url}")
            else:
                print(f"\n   ❌ CTA設定が見つかりません（ボタンなし）")


def main():
    print("=" * 60)
    print("Novu ワークフロー設定確認ツール")
    print("=" * 60)
    
    # すべてのワークフローを取得
    print("\n🔍 ワークフロー一覧を取得中...")
    
    result = list_all_workflows()
    
    if not result:
        print("❌ ワークフローの取得に失敗しました")
        return
    
    workflows = result.get('data', [])
    
    print(f"\n✅ {len(workflows)} 件のワークフローが見つかりました")
    
    # 各ワークフローの詳細を確認
    for workflow_summary in workflows:
        workflow_id = workflow_summary.get('_id')
        
        # 詳細を取得
        workflow_data = get_workflow_by_id(workflow_id)
        
        if workflow_data:
            check_workflow_buttons(workflow_data)
    
    print("\n" + "=" * 60)
    print("確認完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
