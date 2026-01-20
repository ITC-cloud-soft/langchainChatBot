/**
 * ARS Flow パラメータをFormily Schema形式に変換するユーティリティ
 */

export interface ARSParam {
  api_param_name: string;
  param_type: 'text' | 'option' | 'number' | 'date' | 'file';
  option?: Array<{
    option_label: string;
    option_value: string;
  }>;
  required?: boolean;
  default_value?: any;
}

export interface FormilySchema {
  type: string;
  properties: Record<string, any>;
}

/**
 * ARSパラメータをFormily Schema形式に変換
 */
export function convertARSToFormilySchema(arsParams: ARSParam[]): FormilySchema {
  const properties: Record<string, any> = {};
  
  arsParams.forEach(param => {
    const { api_param_name, param_type, option, required } = param;
    
    switch (param_type) {
      case 'text':
        properties[api_param_name] = {
          type: 'string',
          title: api_param_name,
          'x-component': 'Input',
          'x-decorator': 'FormItem',
          'x-component-props': {
            placeholder: `${api_param_name}を入力してください`,
          },
          'x-validator': required ? [{ required: true, message: `${api_param_name}は必須です` }] : undefined,
        };
        break;
        
      case 'number':
        properties[api_param_name] = {
          type: 'number',
          title: api_param_name,
          'x-component': 'NumberInput',
          'x-decorator': 'FormItem',
          'x-component-props': {
            placeholder: `${api_param_name}を入力してください`,
          },
          'x-validator': required ? [{ required: true, message: `${api_param_name}は必須です` }] : undefined,
        };
        break;
        
      case 'option':
        properties[api_param_name] = {
          type: 'string',
          title: api_param_name,
          'x-component': 'Select',
          'x-decorator': 'FormItem',
          enum: option?.map(opt => ({
            label: opt.option_label,
            value: opt.option_value,
          })) || [],
          'x-validator': required ? [{ required: true, message: `${api_param_name}を選択してください` }] : undefined,
        };
        break;
        
      case 'date':
        properties[api_param_name] = {
          type: 'string',
          title: api_param_name,
          'x-component': 'DatePicker',
          'x-decorator': 'FormItem',
          'x-validator': required ? [{ required: true, message: `${api_param_name}を選択してください` }] : undefined,
        };
        break;
        
      case 'file':
        properties[api_param_name] = {
          type: 'string',
          title: api_param_name,
          'x-component': 'Upload',
          'x-decorator': 'FormItem',
          'x-validator': required ? [{ required: true, message: `${api_param_name}をアップロードしてください` }] : undefined,
        };
        break;
        
      default:
        // デフォルトはテキスト入力
        properties[api_param_name] = {
          type: 'string',
          title: api_param_name,
          'x-component': 'Input',
          'x-decorator': 'FormItem',
        };
    }
  });
  
  return {
    type: 'object',
    properties,
  };
}

/**
 * メッセージからFlow情報を解析
 */
export interface FlowFormData {
  flowId: string;
  flowName: string;
  params: ARSParam[];
}

export function parseFlowParamMessage(message: string): FlowFormData | null {
  try {
    // Flow IDを抽出
    const flowIdMatch = message.match(/\*\*Flow ID\*\*:\s*(\d+)/);
    if (!flowIdMatch) return null;
    
    const flowId = flowIdMatch[1];
    
    // Flow名を抽出
    const nameMatch = message.match(/📋\s*\*\*(.+?)\*\*/);
    const flowName = nameMatch ? nameMatch[1] : `Flow ${flowId}`;
    
    // パラメータを解析
    const params: ARSParam[] = [];
    const lines = message.split('\n');
    
    let currentParam: Partial<ARSParam> | null = null;
    
    for (const line of lines) {
      // パラメータ定義行: - **ParamName** (type)
      const paramMatch = line.match(/^-\s*\*\*(.+?)\*\*\s*\((.+?)\)/);
      if (paramMatch) {
        // 前のパラメータを保存
        if (currentParam && currentParam.api_param_name) {
          params.push(currentParam as ARSParam);
        }
        
        // 新しいパラメータ
        currentParam = {
          api_param_name: paramMatch[1],
          param_type: paramMatch[2] as any,
          option: [],
        };
        continue;
      }
      
      // オプション行: - ラベル (値)
      if (currentParam && line.trim().startsWith('-') && !line.includes('**')) {
        const optMatch = line.match(/^\s*-\s*(.+?)\s*\((.+?)\)/);
        if (optMatch) {
          currentParam.option = currentParam.option || [];
          currentParam.option.push({
            option_label: optMatch[1],
            option_value: optMatch[2],
          });
        }
      }
    }
    
    // 最後のパラメータを保存
    if (currentParam && currentParam.api_param_name) {
      params.push(currentParam as ARSParam);
    }
    
    return { flowId, flowName, params };
  } catch (error) {
    console.error('Failed to parse flow param message:', error);
    return null;
  }
}

/**
 * メッセージがFlow参数フォームかどうかを判定
 */
export function isFlowParamMessage(message: string): boolean {
  return message.includes('**Flow ID**:') && 
         message.includes('パラメータを入力してください');
}
