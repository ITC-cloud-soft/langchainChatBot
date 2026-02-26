"""
SSFlow 申請関連 共通ユーティリティ
"""
import json

# SSFlow FK_Flow → ARS Flow ID マッピング
CCFLOW_FLOW_MAPPING = {
    "001": 10, "002": 10, "003": 10, "004": 10, "005": 10,
    "006": 10, "007": 10, "008": 10, "009": 10,
}

# SSFlow FK_Flow → MainTblName マッピング（SSFlow DB WF_Flow.PTable より）
FK_FLOW_TO_TABLE = {
    "001": "TT_WF_MERCHANDISE_PLAN",
    "002": "TT_WF_ORDER",
    "003": "TT_WF_ORDER_UNPLANNED",
    "004": "TT_WF_ARRIVAL_UNPLANNED",
    "005": "TT_WF_ARRIVAL_RETURNS",
    "006": "TT_WF_MOVE_REQUEST",
    "007": "TT_WF_STOCK_ADJUSTMENT",
    "008": "TT_WF_PRICE_CHANGE",
    "009": "TT_WF_MREQ_ARRCORRECTION",
}


def build_maintblname_value(form_data: dict) -> str:
    """
    展開フィールド（COMMENT, AgentMode, content_* 等）から MainTblName_value JSON を組み立てる。
    組み立て済みの場合（MainTblName_value が存在し COMMENT がない）はそのまま返す。
    """
    if "MainTblName_value" in form_data and "COMMENT" not in form_data:
        return form_data["MainTblName_value"]

    summry_obj = {
        "AgentMode":        form_data.pop("AgentMode", "0"),
        "AutoApprovalMode": form_data.pop("AutoApprovalMode", "N"),
        "content": [
            {"name": "従業員氏名", "value": form_data.pop("content_name",    "")},
            {"name": "社員番号",   "value": form_data.pop("content_empno",   "")},
            {"name": "会社名称",   "value": form_data.pop("content_company", "")},
            {"name": "所属",       "value": form_data.pop("content_dept",    "")},
        ],
    }

    affiliation_obj = {
        "APPLICANT_AFFILIATION": {
            "COMPANY":    form_data.pop("AFFILIATION_COMPANY",    "00000"),
            "KAISHACODE": form_data.pop("AFFILIATION_KAISHACODE", ""),
            "BUSHOCODE":  form_data.pop("AFFILIATION_BUSHOCODE",  ""),
        }
    }

    tbl_value = {
        "COMMENT":          form_data.pop("COMMENT", ""),
        "SUMMRY":           json.dumps(summry_obj, ensure_ascii=False),
        "AFFILIATION_INFO": affiliation_obj,
        "UPLOAD_FILES":     form_data.pop("UPLOAD_FILES", "[]"),
    }
    return json.dumps(tbl_value, ensure_ascii=False)
