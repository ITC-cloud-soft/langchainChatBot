/**
 * Flow実行結果の検出と解析ユーティリティ
 */

export interface ParsedFlowResult {
  isFlowResult: boolean;
  flowId?: string;
  success?: boolean;
  resultData?: any;
  error?: string;
  rawContent?: string;
}

/**
 * メッセージがFlow実行結果かどうかを判定
 */
export function isFlowResultMessage(content: string): boolean {
  // ✅ **Flow X 実行成功!** または ❌ **Flow X** 実行失敗 のパターンを検出
  const successPattern = /✅\s*\*\*Flow\s+\d+\s+実行成功!\*\*/;
  const failurePattern = /❌\s*\*\*Flow\s+\d+\*\*\s+実行失敗/;
  
  return successPattern.test(content) || failurePattern.test(content);
}

/**
 * Flow実行結果メッセージを解析
 */
export function parseFlowResultMessage(content: string): ParsedFlowResult {
  if (!isFlowResultMessage(content)) {
    return { isFlowResult: false, rawContent: content };
  }

  // 成功パターンのマッチング
  const successPattern = /✅\s*\*\*Flow\s+(\d+)\s+実行成功!\*\*/;
  const successMatch = content.match(successPattern);

  if (successMatch) {
    const flowId = successMatch[1];
    
    // ### 📋 で始まるセクションを探す
    const flowNamePattern = /###\s+📋\s+(.+)/;
    const flowNameMatch = content.match(flowNamePattern);
    
    // ステップ情報を抽出
    const stepPattern = /\*\*ステップ\s+(\d+):\s+(.+?)\*\*\s+(✅|❌)/g;
    const steps: any[] = [];
    let stepMatch;
    
    while ((stepMatch = stepPattern.exec(content)) !== null) {
      const stepNumber = stepMatch[1];
      const stepName = stepMatch[2];
      const isSuccess = stepMatch[3] === '✅';
      
      steps.push({
        number: stepNumber,
        name: stepName,
        result: isSuccess ? 'success' : 'error',
      });
    }

    // 詳細データのJSON部分を抽出
    const jsonPattern = /```json\s*\n([\s\S]*?)\n```/;
    const jsonMatch = content.match(jsonPattern);
    let resultData = null;
    
    if (jsonMatch) {
      try {
        resultData = JSON.parse(jsonMatch[1]);
      } catch (e) {
        console.error('Failed to parse flow result JSON:', e);
      }
    }

    return {
      isFlowResult: true,
      flowId,
      success: true,
      resultData,
      rawContent: content,
    };
  }

  // 失敗パターンのマッチング
  const failurePattern = /❌\s*\*\*Flow\s+(\d+)\*\*\s+実行失敗:\s*(.+)/;
  const failureMatch = content.match(failurePattern);

  if (failureMatch) {
    const flowId = failureMatch[1];
    const error = failureMatch[2];

    return {
      isFlowResult: true,
      flowId,
      success: false,
      error,
      rawContent: content,
    };
  }

  return { isFlowResult: false, rawContent: content };
}

/**
 * Markdown形式のFlow結果から構造化データを抽出
 */
export function extractStructuredFlowResult(content: string): any {
  const result: any = {
    flows: [],
  };

  // Flow名を抽出
  const flowNamePattern = /###\s+📋\s+(.+)/g;
  let flowMatch;
  
  while ((flowMatch = flowNamePattern.exec(content)) !== null) {
    const flowName = flowMatch[1].trim();
    const flow: any = {
      name: flowName,
      steps: [],
    };

    // このFlowのステップを抽出
    const stepPattern = /\*\*ステップ\s+(\d+):\s+(.+?)\*\*\s+(✅|❌)([\s\S]*?)(?=\*\*ステップ|\n\n<details>|$)/g;
    let stepMatch;
    
    while ((stepMatch = stepPattern.exec(content)) !== null) {
      const stepNumber = parseInt(stepMatch[1]);
      const stepName = stepMatch[2].trim();
      const isSuccess = stepMatch[3] === '✅';
      const stepContent = stepMatch[4];

      const step: any = {
        number: stepNumber,
        name: stepName,
        result: isSuccess ? 'success' : 'error',
      };

      // WorkIDを抽出
      const workIdMatch = stepContent.match(/WorkID:\s*`([^`]+)`/);
      if (workIdMatch) {
        step.workId = workIdMatch[1];
      }

      // FK_Nodeを抽出
      const fkNodeMatch = stepContent.match(/FK_Node:\s*`([^`]+)`/);
      if (fkNodeMatch) {
        step.fkNode = fkNodeMatch[1];
      }

      // エラーコードを抽出
      const errorCodeMatch = stepContent.match(/エラーコード:\s*`([^`]+)`/);
      if (errorCodeMatch) {
        step.errorCode = errorCodeMatch[1];
      }

      // エラーメッセージを抽出
      const errorMsgMatch = stepContent.match(/エラーメッセージ:\s*(.+)/);
      if (errorMsgMatch) {
        step.errorMessage = errorMsgMatch[1].trim();
      }

      // 実行時刻を抽出
      const timeMatch = stepContent.match(/実行時刻:\s*(.+)/);
      if (timeMatch) {
        step.timestamp = timeMatch[1].trim();
      }

      flow.steps.push(step);
    }

    result.flows.push(flow);
  }

  // 詳細データのJSONを抽出
  const jsonPattern = /```json\s*\n([\s\S]*?)\n```/;
  const jsonMatch = content.match(jsonPattern);
  
  if (jsonMatch) {
    try {
      result.detailData = JSON.parse(jsonMatch[1]);
    } catch (e) {
      console.error('Failed to parse detail JSON:', e);
    }
  }

  return result;
}
