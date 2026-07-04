"""Classical BaZi book sub-agent debate layer.

Each downloaded PDF source is represented as a low-risk sub-agent. The agents
encode auditable methodology cards and debate priorities; they do not claim
page-level quotation until OCR or manual edition review is complete.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def U(value: str) -> str:
    """Decode ASCII-safe unicode escape text into runtime Chinese strings."""
    try:
        return value.encode("ascii").decode("unicode_escape")
    except UnicodeEncodeError:
        return value


SANMING_TONGHUI_VOLUME_SUBAGENTS: tuple[dict[str, Any], ...] = tuple(
    {
        "agent_id": f"subagent_sanming_tonghui_juan_{volume}",
        "parent_agent_ids": [
            "book_sanming_tonghui_juan_1_agent",
            "book_sanming_tonghui_juan_9_agent",
        ],
        "source_id": f"san_ming_tong_hui_juan_{volume}_ia",
        "volume": volume,
        "book": U("\u4e09\u547d\u901a\u4f1a\u5377") + str(volume),
        "local_file": f"san_ming_tong_hui_juan_{volume}_ia.pdf",
        "role": U("\u5377\u7ea7\u8d44\u6599\u5b50\u667a\u80fd\u4f53\uff0c\u8d1f\u8d23\u672c\u5377\u6765\u6e90\u8986\u76d6\u3001\u540e\u7eedOCR\u6821\u52d8\u627f\u63a5\u548c\u6761\u6587\u89c4\u5219\u5347\u7ea7\u5165\u53e3\u3002"),
        "current_status": "downloaded_source_agent_pending_ocr_review",
        "promotion_rule": U("\u5b8c\u6210OCR\u6216\u4eba\u5de5\u6821\u52d8\u540e\uff0c\u624d\u80fd\u628a\u672c\u5377\u5177\u4f53\u6761\u6587\u63d0\u5347\u4e3a\u53ef\u5f15\u7528\u89c4\u5219\u3002"),
    }
    for volume in range(1, 13)
)


def _book(
    agent_id: str,
    source_id: str,
    title: str,
    book: str,
    school: str,
    primary_layers: list[str],
    fields: list[str],
    stance: str,
    challenge: str,
    rules: list[str],
    calibration_questions: list[str],
    sub_agents: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "source_id": source_id,
        "title": U(title),
        "book": U(book),
        "school": U(school),
        "primary_layers": [U(item) for item in primary_layers],
        "fields": fields,
        "stance": U(stance),
        "challenge": U(challenge),
        "rules": [U(item) for item in rules],
        "calibration_questions": [U(item) for item in calibration_questions],
        "sub_agents": sub_agents,
    }


BOOK_AGENT_DEFINITIONS: tuple[dict[str, Any], ...] = (
    _book(
        "book_sanming_tonghui_juan_1_agent",
        "bazi_sanming_tonghui",
        "\u4e09\u547d\u901a\u4f1a\u603b\u7eb2\u5b50\u667a\u80fd\u4f53",
        "\u4e09\u547d\u901a\u4f1a\u5168\u5341\u4e8c\u5377",
        "\u4e09\u547d\u7efc\u5408\u6cd5",
        ["\u6574\u4f53\u547d\u76d8", "\u683c\u5c40\u5341\u795e", "\u5927\u8fd0\u6d41\u5e74"],
        ["pattern_analysis", "ten_god_distribution", "major_luck"],
        "\u56db\u67f1\u3001\u6708\u4ee4\u3001\u5341\u795e\u3001\u683c\u5c40\u548c\u5c81\u8fd0\u5fc5\u987b\u5408\u53c2\uff0c\u4e0d\u80fd\u7528\u5355\u70b9\u5f3a\u5f31\u76f4\u63a5\u4e0b\u65ad\u3002",
        "\u51e1\u662f\u53ea\u8bb2\u559c\u5fcc\u3001\u4e0d\u8bf4\u660e\u547d\u76d8\u5c42\u7ea7\u548c\u5c81\u8fd0\u627f\u63a5\u7684\u5224\u65ad\uff0c\u90fd\u5e94\u964d\u6743\u3002",
        ["\u5148\u5b9a\u56db\u67f1\u6574\u4f53\uff0c\u518d\u5b9a\u6708\u4ee4\u4e3b\u6c14\u548c\u683c\u5c40\u4e3b\u7ebf\u3002", "\u795e\u715e\u3001\u7eb3\u97f3\u548c\u6742\u9879\u53ea\u4f5c\u8f85\u52a9\uff0c\u4e0d\u538b\u8fc7\u56db\u67f1\u4e3b\u7ebf\u3002", "\u5927\u8fd0\u662f\u627f\u63a5\u539f\u5c40\uff0c\u6d41\u5e74\u662f\u89e6\u53d1\u539f\u5c40\uff0c\u6d41\u6708\u662f\u843d\u5b9e\u8282\u594f\u3002"],
        ["\u91cd\u5927\u5347\u5b66\u3001\u6362\u73af\u5883\u6216\u5bb6\u5ead\u7ed3\u6784\u53d8\u5316\u5206\u522b\u53d1\u751f\u5728\u54ea\u4e9b\u5e74\u4efd\uff1f"],
        SANMING_TONGHUI_VOLUME_SUBAGENTS,
    ),
    _book(
        "book_sanming_tonghui_juan_9_agent",
        "bazi_sanming_tonghui",
        "\u4e09\u547d\u901a\u4f1a\u5e94\u671f\u5b50\u667a\u80fd\u4f53",
        "\u4e09\u547d\u901a\u4f1a\u5168\u5341\u4e8c\u5377",
        "\u4e09\u547d\u7efc\u5408\u5e94\u671f\u6cd5",
        ["\u6d41\u5e74\u89e6\u53d1", "\u6d41\u6708\u843d\u4e8b", "\u8f85\u52a9\u7b26\u53f7"],
        ["classical_layered_methodology", "school_debate", "major_luck"],
        "\u5e74\u3001\u6708\u5224\u65ad\u8981\u628a\u5e72\u652f\u3001\u5341\u795e\u3001\u5211\u51b2\u5408\u5bb3\u548c\u539f\u5c40\u5bab\u4f4d\u4e00\u8d77\u770b\uff0c\u4e0d\u80fd\u590d\u7528\u56fa\u5b9a\u5957\u8bdd\u3002",
        "\u82e5\u5e74\u5ea6\u548c\u6708\u5ea6\u6ca1\u6709\u72ec\u7acb\u8ba1\u7b97\u5e72\u652f\u5173\u7cfb\uff0c\u53ea\u80fd\u4f5c\u4e3a\u4f4e\u53ef\u4fe1\u63d0\u793a\u3002",
        ["\u6bcf\u4e00\u5e74\u5fc5\u987b\u5355\u72ec\u5224\u65ad\u5929\u5e72\u3001\u5730\u652f\u3001\u85cf\u5e72\u3001\u5408\u51b2\u5211\u5bb3\u3002", "\u6bcf\u4e00\u6708\u5fc5\u987b\u91cd\u65b0\u7ed1\u5b9a\u8282\u6c14\u8fb9\u754c\u548c\u6708\u67f1\u6765\u6e90\u3002", "\u540c\u4e00\u795e\u715e\u6216\u7b26\u53f7\u9700\u8981\u539f\u5c40\u3001\u5927\u8fd0\u3001\u6d41\u5e74\u540c\u5411\u65f6\u624d\u63d0\u9ad8\u6743\u91cd\u3002"],
        ["\u54ea\u4e9b\u5e74\u4efd\u53ea\u662f\u538b\u529b\u5927\uff0c\u54ea\u4e9b\u5e74\u4efd\u771f\u6b63\u53d1\u751f\u7ed3\u679c\u6027\u4e8b\u4ef6\uff1f"],
        SANMING_TONGHUI_VOLUME_SUBAGENTS,
    ),
    _book("book_li_xuzhong_luoluzi_agent", "li_xu_zhong_ming_shu_luo_lu_zi_ia", "\u674e\u865a\u4e2d\u73de\u742d\u5b50\u5b50\u667a\u80fd\u4f53", "\u674e\u865a\u4e2d\u547d\u4e66\u3001\u73de\u742d\u5b50\u4e09\u547d\u6d88\u606f\u8d4b\u6ce8", "\u65e9\u671f\u4e09\u547d\u6e90\u6d41\u6cd5", ["\u6e90\u6d41\u8fb9\u754c", "\u4eba\u751f\u9636\u6bb5", "\u5927\u8fd0\u9636\u6bb5"], ["nayin_growth_profile", "major_luck", "classical_layered_methodology"], "\u65e9\u671f\u4e09\u547d\u6750\u6599\u7528\u4e8e\u89c2\u5bdf\u4eba\u751f\u9636\u6bb5\u548c\u6e90\u6d41\u8fb9\u754c\uff0c\u4e0d\u80fd\u76f4\u63a5\u66ff\u4ee3\u540e\u4e16\u5b50\u5e73\u683c\u5c40\u6cd5\u3002", "\u82e5\u53e4\u6cd5\u7b26\u53f7\u4e0e\u5b50\u5e73\u7ed3\u6784\u51b2\u7a81\uff0c\u5e94\u4fdd\u7559\u4e3a\u65c1\u8bc1\uff0c\u800c\u4e0d\u662f\u5f3a\u884c\u8986\u76d6\u4e3b\u65ad\u3002", ["\u6362\u5927\u8fd0\u65f6\u4f18\u5148\u89c2\u5bdf\u8eab\u4efd\u3001\u73af\u5883\u3001\u5bb6\u5ead\u8d23\u4efb\u548c\u5b66\u4e60\u9636\u6bb5\u53d8\u5316\u3002", "\u7eb3\u97f3\u3001\u957f\u751f\u9636\u6bb5\u53ea\u5728\u4e0e\u56db\u67f1\u4e3b\u7ebf\u540c\u5411\u65f6\u63d0\u9ad8\u63d0\u793a\u6743\u91cd\u3002", "\u53e4\u6cd5\u8bed\u8a00\u8fdb\u5165\u73b0\u4ee3\u5206\u6790\u524d\u8981\u5148\u8f6c\u6362\u6210\u53ef\u9a8c\u8bc1\u7684\u7ed3\u6784\u5b57\u6bb5\u3002"], ["\u6362\u8fd0\u524d\u540e\u662f\u5426\u51fa\u73b0\u8f6c\u5b66\u3001\u642c\u5bb6\u3001\u5347\u5b66\u8def\u5f84\u6539\u53d8\u6216\u5bb6\u5ead\u8d23\u4efb\u53d8\u5316\uff1f"]),
    _book("book_tianbu_zhenyuan_agent", "tian_bu_zhen_yuan_ren_ming_bu_ia", "\u5929\u6b65\u771f\u539f\u4eba\u547d\u90e8\u5b50\u667a\u80fd\u4f53", "\u5929\u6b65\u771f\u539f\u4eba\u547d\u90e8", "\u661f\u547d\u5386\u53f2\u6bd4\u8f83\u6cd5", ["\u661f\u547d\u65c1\u8bc1", "\u5386\u53f2\u8fb9\u754c", "\u4e8b\u4ef6\u6821\u51c6"], ["classical_layered_methodology", "data_validation_analysis"], "\u661f\u547d\u548c\u5b87\u5b99\u8bba\u6750\u6599\u53ea\u4f5c\u5386\u53f2\u6bd4\u8f83\uff0c\u4e0d\u76f4\u63a5\u51b3\u5b9a\u8d22\u5b98\u5a5a\u80b2\u7b49\u7ed3\u8bba\u3002", "\u5982\u679c\u67d0\u4e2a\u5224\u65ad\u53ea\u6765\u81ea\u661f\u547d\u65c1\u8bc1\u800c\u6ca1\u6709\u56db\u67f1\u3001\u5c81\u8fd0\u652f\u6301\uff0c\u5e94\u6807\u4e3a\u4f4e\u53ef\u4fe1\u3002", ["\u5386\u53f2\u661f\u547d\u6846\u67b6\u4e0e\u53ef\u6267\u884c\u516b\u5b57\u89c4\u5219\u5206\u5f00\u3002", "\u53ea\u6709\u4e0e\u56db\u67f1\u3001\u5927\u8fd0\u3001\u6d41\u5e74\u540c\u5411\u65f6\u624d\u8fdb\u5165\u65c1\u8bc1\u3002", "\u6240\u6709\u65c1\u8bc1\u5fc5\u987b\u56de\u5230\u660e\u786e\u5e74\u4efd\u4e8b\u4ef6\u4e0a\u6821\u51c6\u3002"], ["\u65c1\u8bc1\u662f\u5426\u80fd\u88ab\u660e\u786e\u5e74\u4efd\u4e8b\u4ef6\u652f\u6301\uff1f"]),
    _book("book_ziping_zhenquan_agent", "zi_ping_zhen_quan_nlc", "\u5b50\u5e73\u771f\u8be0\u5b50\u667a\u80fd\u4f53", "\u5b50\u5e73\u771f\u8be0", "\u5b50\u5e73\u683c\u5c40\u7528\u795e\u6cd5", ["\u6574\u4f53\u547d\u76d8", "\u683c\u5c40\u7528\u795e", "\u5927\u8fd0\u627f\u63a5"], ["pattern_analysis", "hengmen_pattern_analysis", "useful_god_analysis"], "\u4ee5\u6708\u4ee4\u7acb\u683c\uff0c\u4ee5\u6210\u683c\u3001\u7834\u683c\u3001\u7528\u795e\u4fdd\u62a4\u6765\u5b9a\u4e3b\u7ebf\uff0c\u4e0d\u4ee5\u65e5\u4e3b\u5f3a\u5f31\u4e00\u9524\u5b9a\u97f3\u3002", "\u82e5\u5f3a\u5f31\u6276\u6291\u4e0e\u683c\u5c40\u7528\u795e\u51b2\u7a81\uff0c\u5e94\u5148\u68c0\u67e5\u6708\u4ee4\u3001\u900f\u5e72\u548c\u4fdd\u62a4\u673a\u5236\u3002", ["\u6708\u4ee4\u662f\u683c\u5c40\u5165\u53e3\uff0c\u900f\u5e72\u548c\u901a\u6839\u51b3\u5b9a\u683c\u5c40\u662f\u5426\u80fd\u7528\u3002", "\u7528\u795e\u4e0d\u53ea\u770b\u51fa\u73b0\uff0c\u66f4\u8981\u770b\u662f\u5426\u88ab\u4fdd\u62a4\u3001\u662f\u5426\u88ab\u5c81\u8fd0\u7834\u574f\u3002", "\u5927\u8fd0\u6d41\u5e74\u5148\u770b\u662f\u5426\u6210\u5c31\u6216\u7834\u574f\u539f\u5c40\u683c\u5c40\u3002"], ["\u4eba\u751f\u5173\u952e\u4e0a\u5347\u671f\u662f\u5426\u5bf9\u5e94\u683c\u5c40\u7528\u795e\u88ab\u5c81\u8fd0\u6276\u8d77\uff1f"]),
    _book("book_yuanhai_ziping_agent", "yuan_hai_zi_ping_zi_ping_zhen_quan_v1_ntl", "\u6e0a\u6d77\u5b50\u5e73\u5b50\u667a\u80fd\u4f53", "\u6e0a\u6d77\u5b50\u5e73\u5b50\u5e73\u771f\u8be0 v.1", "\u6e0a\u6d77\u5b50\u5e73\u7efc\u5408\u6cd5", ["\u56db\u67f1\u7ed3\u6784", "\u5341\u795e\u7c7b\u8c61", "\u5c81\u8fd0\u5e94\u671f"], ["ten_god_distribution", "hidden_stem_profile", "major_luck"], "\u91cd\u89c6\u56db\u67f1\u5bab\u4f4d\u3001\u5341\u795e\u7c7b\u8c61\u548c\u5c81\u8fd0\u5f15\u52a8\uff0c\u9002\u5408\u628a\u62bd\u8c61\u7ed3\u6784\u843d\u5230\u4eba\u4e8b\u4e3b\u9898\u3002", "\u82e5\u53ea\u7ed9\u5409\u51f6\u4e0d\u8bf4\u660e\u5341\u795e\u548c\u5bab\u4f4d\u843d\u70b9\uff0c\u5224\u65ad\u4e0d\u591f\u53ef\u590d\u6838\u3002", ["\u5e74\u3001\u6708\u3001\u65e5\u3001\u65f6\u5206\u522b\u5bf9\u5e94\u4e0d\u540c\u4eba\u4e8b\u8303\u56f4\uff0c\u4e0d\u80fd\u6df7\u7528\u3002", "\u5341\u795e\u7c7b\u8c61\u5fc5\u987b\u7ed3\u5408\u6240\u5728\u67f1\u4f4d\u548c\u5c81\u8fd0\u5f15\u52a8\u3002", "\u85cf\u5e72\u88ab\u900f\u51fa\u6216\u88ab\u5c81\u8fd0\u5f15\u52a8\u65f6\uff0c\u6f5c\u4f0f\u4e3b\u9898\u624d\u660e\u663e\u6210\u4e8b\u3002"], ["\u54ea\u51e0\u5e74\u540c\u5b66\u3001\u7236\u6bcd\u3001\u8001\u5e08\u3001\u670b\u53cb\u5173\u7cfb\u53d8\u5316\u6700\u660e\u663e\uff1f"]),
    _book("book_shenfeng_tongkao_agent", "shen_feng_tong_kao_nlc", "\u795e\u5cf0\u901a\u8003\u5b50\u667a\u80fd\u4f53", "\u795e\u5cf0\u901a\u8003", "\u75c5\u836f\u901a\u5173\u6cd5", ["\u547d\u5c40\u75c5\u836f", "\u901a\u5173\u5236\u5316", "\u5c81\u8fd0\u4fee\u590d"], ["strength_analysis", "useful_god_analysis", "element_counts"], "\u547d\u5c40\u5148\u627e\u75c5\uff0c\u518d\u627e\u836f\uff1b\u5c81\u8fd0\u4e0d\u662f\u5355\u770b\u559c\u5fcc\uff0c\u800c\u662f\u770b\u80fd\u5426\u6cbb\u75c5\u3001\u901a\u5173\u3001\u5236\u5316\u3002", "\u82e5\u67d0\u8fd0\u770b\u4f3c\u559c\u795e\u4f46\u4e0d\u80fd\u89e3\u51b3\u547d\u5c40\u4e3b\u8981\u77db\u76fe\uff0c\u4e0d\u80fd\u76f4\u63a5\u5224\u4e3a\u597d\u3002", ["\u8fc7\u65fa\u3001\u8fc7\u5f31\u3001\u5bd2\u70ed\u71e5\u6e7f\u3001\u51b2\u514b\u963b\u585e\u90fd\u53ef\u80fd\u662f\u75c5\u3002", "\u836f\u8981\u5bf9\u75c5\uff0c\u901a\u5173\u8981\u80fd\u8ba9\u4e94\u884c\u6d41\u52a8\u3002", "\u5c81\u8fd0\u6cbb\u75c5\u5219\u4e8b\u987a\uff0c\u5c81\u8fd0\u52a0\u75c5\u5219\u538b\u529b\u663e\u3002"], ["\u538b\u529b\u5e74\u4efd\u7684\u95ee\u9898\u662f\u8eab\u4f53\u72b6\u6001\u3001\u5b66\u4e1a\u5361\u987f\u3001\u5173\u7cfb\u51b2\u7a81\u8fd8\u662f\u76ee\u6807\u6df7\u4e71\uff1f"]),
    _book("book_ditiansui_agent", "di_tian_sui_ji_yao_nlc", "\u6ef4\u5929\u9ad3\u8f91\u8981\u5b50\u667a\u80fd\u4f53", "\u6ef4\u5929\u9ad3\u8f91\u8981", "\u6c14\u52bf\u6d41\u901a\u6cd5", ["\u4e94\u884c\u6c14\u52bf", "\u6e05\u6d4a\u7eaf\u6742", "\u6d41\u901a\u65ad\u70b9"], ["image_symbol_analysis", "useful_god_analysis", "strength_analysis"], "\u91cd\u770b\u5168\u5c40\u6c14\u52bf\u662f\u5426\u6e05\u3001\u662f\u5426\u6d41\u901a\u3001\u662f\u5426\u6709\u65ad\u70b9\uff1b\u597d\u574f\u4e0d\u53ea\u5728\u67d0\u4e00\u4e2a\u4e94\u884c\u51fa\u73b0\u3002", "\u82e5\u5224\u65ad\u53ea\u8bf4\u67d0\u4e94\u884c\u559c\u5fcc\uff0c\u5374\u4e0d\u8bf4\u660e\u6c14\u52bf\u5982\u4f55\u6d41\u52a8\uff0c\u5e94\u8981\u6c42\u91cd\u7b97\u3002", ["\u5148\u770b\u6c14\u52bf\u53bb\u5411\uff0c\u518d\u770b\u7528\u795e\u843d\u70b9\u3002", "\u6e05\u800c\u6709\u60c5\u5219\u5bb9\u6613\u6210\u4e8b\uff0c\u6742\u800c\u963b\u585e\u5219\u591a\u53cd\u590d\u3002", "\u6d41\u5e74\u6d41\u6708\u8981\u5224\u65ad\u662f\u5728\u758f\u901a\uff0c\u8fd8\u662f\u5728\u5236\u9020\u65b0\u7684\u963b\u65ad\u3002"], ["\u987a\u5229\u5e74\u4efd\u662f\u5426\u8868\u73b0\u4e3a\u8282\u594f\u987a\u3001\u963b\u529b\u5c11\uff0c\u800c\u4e0d\u662f\u5355\u70b9\u597d\u8fd0\uff1f"]),
    _book("book_qiongtong_baojian_agent", "qiong_tong_bao_jian_ping_zhu_nlc", "\u7a77\u901a\u5b9d\u9274\u8bc4\u6ce8\u5b50\u667a\u80fd\u4f53", "\u7a77\u901a\u5b9d\u9274\u8bc4\u6ce8", "\u8c03\u5019\u6708\u4ee4\u6cd5", ["\u6708\u4ee4\u6c14\u5019", "\u5bd2\u6696\u71e5\u6e7f", "\u5b66\u4e60\u72b6\u6001"], ["tiaohou_analysis", "useful_god_analysis", "pattern_analysis"], "\u51fa\u751f\u6708\u4ee4\u7684\u5bd2\u6696\u71e5\u6e7f\u4f1a\u5f71\u54cd\u53d1\u6325\u72b6\u6001\uff1b\u5bf9\u5b66\u4e1a\u5c24\u5176\u8981\u770b\u7cbe\u795e\u3001\u8010\u529b\u548c\u8282\u594f\u3002", "\u7ed3\u6784\u770b\u4f3c\u5e73\u8861\u4f46\u8c03\u5019\u5931\u8861\u65f6\uff0c\u4e0d\u80fd\u5ffd\u7565\u7761\u7720\u3001\u60c5\u7eea\u3001\u8010\u529b\u95ee\u9898\u3002", ["\u590f\u751f\u5148\u9632\u71e5\u70ed\u8fc7\u65fa\uff0c\u51ac\u751f\u5148\u9632\u5bd2\u6e7f\u51dd\u6ede\u3002", "\u8c03\u5019\u5230\u4f4d\uff0c\u5b66\u4e60\u5438\u6536\u548c\u6267\u884c\u7a33\u5b9a\u6027\u63d0\u9ad8\u3002", "\u8c03\u5019\u4e0d\u5f53\uff0c\u5e38\u5148\u8868\u73b0\u4e3a\u70e6\u8e81\u3001\u75b2\u5026\u3001\u62d6\u5ef6\u6216\u8003\u8bd5\u72b6\u6001\u6ce2\u52a8\u3002"], ["\u6210\u7ee9\u6ce2\u52a8\u662f\u5426\u5e38\u548c\u7761\u7720\u3001\u4f53\u529b\u3001\u60c5\u7eea\u70ed\u51b7\u6709\u5173\uff1f"]),
    _book("book_mingli_yueyan_agent", "jing_xuan_ming_li_yue_yan_nlc", "\u7cbe\u9009\u547d\u7406\u7ea6\u8a00\u5b50\u667a\u80fd\u4f53", "\u7cbe\u9009\u547d\u7406\u7ea6\u8a00", "\u7ea6\u8a00\u7ecf\u9a8c\u5ba1\u67e5\u6cd5", ["\u7ecf\u9a8c\u89c4\u5219", "\u53cd\u4f8b\u5ba1\u67e5", "\u8bed\u8a00\u538b\u7f29"], ["school_debate", "data_validation_analysis"], "\u7ecf\u9a8c\u65ad\u8bed\u5fc5\u987b\u77ed\u3001\u51c6\u3001\u53ef\u6821\u9a8c\uff1b\u4e0d\u80fd\u4e3a\u4e86\u7384\u5965\u800c\u5806\u53e0\u91cd\u590d\u8bdd\u672f\u3002", "\u82e5\u8f93\u51fa\u7f3a\u5c11\u6307\u5411\u6027\u3001\u6ca1\u6709\u5e74\u4efd\u5dee\u5f02\u3001\u8bed\u8a00\u91cd\u590d\uff0c\u5e94\u9000\u56de\u91cd\u7b97\u8bc1\u636e\u3002", ["\u6bcf\u6761\u65ad\u8bed\u8981\u80fd\u5bf9\u5e94\u660e\u786e\u8bc1\u636e\u5b57\u6bb5\u3002", "\u91cd\u590d\u53e5\u5f0f\u4e0d\u80fd\u66ff\u4ee3\u72ec\u7acb\u5e74\u5ea6\u3001\u6708\u5ea6\u63a8\u7406\u3002", "\u7ecf\u9a8c\u89c4\u5219\u5fc5\u987b\u63a5\u53d7\u4e8b\u5b9e\u53cd\u4f8b\u6821\u51c6\u3002"], ["\u7528\u6237\u53cd\u9988\u4e2d\u54ea\u4e9b\u65ad\u8bed\u51c6\u786e\uff0c\u54ea\u4e9b\u53ea\u662f\u6cdb\u6cdb\u800c\u8c08\uff1f"]),
    _book("book_weiqianli_agent", "wei_qian_li_ming_xue_jiang_yi_nlc", "\u97e6\u5343\u91cc\u547d\u5b66\u8bb2\u4e49\u5b50\u667a\u80fd\u4f53", "\u97e6\u5343\u91cc\u547d\u5b66\u8bb2\u4e49", "\u8fd1\u73b0\u4ee3\u8bb2\u4e49\u6cd5", ["\u6559\u5b66\u5206\u89e3", "\u73b0\u4ee3\u89e3\u91ca", "\u62a5\u544a\u53ef\u8bfb\u6027"], ["classical_layered_methodology", "method_matrix", "school_debate"], "\u590d\u6742\u547d\u7406\u5224\u65ad\u8981\u62c6\u6210\u8bfb\u8005\u80fd\u7406\u89e3\u7684\u6b65\u9aa4\uff0c\u5148\u8bb2\u4e3a\u4ec0\u4e48\uff0c\u518d\u8bb2\u7ed3\u8bba\u3002", "\u82e5\u62a5\u544a\u5806\u672f\u8bed\u3001\u5939\u82f1\u6587\u3001\u5939\u4ee3\u7801\u6216\u7f3a\u5c11\u73b0\u5b9e\u89e3\u91ca\uff0c\u5e94\u5224\u4e3a\u8868\u8fbe\u5931\u8d25\u3002", ["\u5148\u7ed9\u7ed3\u8bba\uff0c\u518d\u7ed9\u547d\u7406\u8bc1\u636e\uff0c\u518d\u7ed9\u73b0\u5b9e\u5efa\u8bae\u3002", "\u5b66\u4e60\u3001\u4e8b\u4e1a\u3001\u5173\u7cfb\u3001\u5065\u5eb7\u8981\u6309\u5e74\u9f84\u9636\u6bb5\u8f6c\u6362\u8bed\u8a00\u3002", "\u513f\u7ae5\u548c\u5b66\u751f\u9636\u6bb5\u4e0d\u80fd\u786c\u5957\u6210\u4eba\u8d22\u8fd0\u5b98\u8fd0\u8bdd\u672f\u3002"], ["\u62a5\u544a\u8bfb\u8005\u662f\u5426\u80fd\u770b\u61c2\u6bcf\u4e2a\u7ed3\u8bba\u4ece\u54ea\u91cc\u6765\uff1f"]),
)


def build_classical_book_agent_debate(deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Build one sub-agent vote for every downloaded classical source."""
    votes = [_book_vote(agent, deep, context) for agent in BOOK_AGENT_DEFINITIONS]
    layer_map = _layer_map(votes)
    conflicts = _book_conflicts(votes)
    consensus = _book_consensus(votes, conflicts)
    material = {
        "schema_version": "classical-book-agent-debate-v1",
        "source_policy": "Downloaded scans are method sources; exact quotation and page-level rule promotion require OCR/manual edition review.",
        "agent_count": len(votes),
        "sub_agent_count": len(_sub_agent_votes(votes)),
        "layer_sub_agent_count": sum(len(vote.get("layer_sub_agents", [])) for vote in votes),
        "votes": votes,
        "sub_agent_votes": _sub_agent_votes(votes),
        "layer_map": layer_map,
        "conflicts": conflicts,
        "consensus": consensus,
    }
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**material, "sha256": hashlib.sha256(encoded).hexdigest()}


def _book_vote(agent: dict[str, Any], deep: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    fields = [field for field in agent["fields"] if _field_present(field, deep, context)]
    missing = [field for field in agent["fields"] if field not in fields]
    confidence = _book_confidence(agent, fields, missing, deep, context)
    architecture = _analysis_architecture(agent, fields)
    return {
        "agent_id": agent["agent_id"],
        "source_id": agent["source_id"],
        "agent_name": agent["title"],
        "book": agent["book"],
        "school": agent["school"],
        "primary_layers": agent["primary_layers"],
        "analysis_architecture": architecture,
        "layer_sub_agents": _layer_sub_agents(agent, architecture),
        "stance": "support" if confidence >= 0.66 else "caution",
        "confidence": confidence,
        "claim": agent["stance"],
        "challenge": agent["challenge"],
        "evidence_fields": fields,
        "missing_fields": missing,
        "method_rules": agent["rules"],
        "sub_agents": _vote_sub_agents(agent),
        "calibration_questions": agent["calibration_questions"],
        "source_boundary": "method-card level; not page-quote level",
    }


def _analysis_architecture(agent: dict[str, Any], evidence_fields: list[str]) -> dict[str, Any]:
    """Return this book's independent layered analysis architecture."""
    primary_layers = [str(item) for item in agent.get("primary_layers", [])]
    rules = [str(item) for item in agent.get("rules", [])]
    layers = []
    for index, layer_name in enumerate(primary_layers, start=1):
        layers.append(
            {
                "layer_index": index,
                "layer_name": layer_name,
                "functional_module": _functional_module(layer_name),
                "evidence_fields": evidence_fields,
                "method_rule": rules[index - 1] if index - 1 < len(rules) else rules[-1] if rules else "",
                "output_contract": _output_contract(layer_name),
                "calibration_role": U("\u7528\u771f\u5b9e\u5e74\u4efd\u4e8b\u4ef6\u6821\u51c6\u672c\u5c42\u662f\u5426\u6709\u6548\uff0c\u4e0d\u80fd\u53ea\u51ed\u53e4\u7c4d\u6765\u6e90\u63d0\u9ad8\u7f6e\u4fe1\u5ea6\u3002"),
            }
        )
    return {
        "schema_version": "book-layered-analysis-architecture-v1",
        "book": agent["book"],
        "source_id": agent["source_id"],
        "layer_count": len(layers),
        "layers": layers,
        "integration_rule": U("\u672c\u4e66\u5148\u5728\u81ea\u5df1\u7684\u5c42\u6b21\u67b6\u6784\u5185\u5b8c\u6210\u5224\u65ad\uff0c\u518d\u8fdb\u5165\u4e66\u672c\u7fa4\u4f53\u8fa9\u8bba\u548c\u516b\u5b57\u6d41\u6d3e\u8fa9\u8bba\u3002"),
    }


def _layer_sub_agents(agent: dict[str, Any], architecture: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for layer in architecture.get("layers", []):
        index = int(layer.get("layer_index", 0))
        rows.append(
            {
                "agent_id": f"{agent['agent_id']}_layer_{index}",
                "parent_agent_id": agent["agent_id"],
                "source_id": agent["source_id"],
                "book": agent["book"],
                "layer_index": index,
                "layer_name": layer.get("layer_name"),
                "functional_module": layer.get("functional_module"),
                "evidence_fields": layer.get("evidence_fields", []),
                "output_contract": layer.get("output_contract"),
                "current_status": "active_method_layer_sub_agent",
            }
        )
    return rows


def _functional_module(layer_name: str) -> str:
    if any(token in layer_name for token in (U("\u8c03\u5019"), U("\u6c14\u5019"), U("\u5bd2\u6696"), U("\u5b66\u4e60\u72b6\u6001"))):
        return "state_and_climate_module"
    if any(token in layer_name for token in (U("\u6c14\u52bf"), U("\u6d41\u901a"), U("\u75c5\u836f"), U("\u901a\u5173"), U("\u5236\u5316"))):
        return "circulation_disease_medicine_module"
    if any(token in layer_name for token in (U("\u8bed\u8a00"), U("\u62a5\u544a"), U("\u6559\u5b66"), U("\u73b0\u4ee3\u89e3\u91ca"), U("\u7ecf\u9a8c"), U("\u53cd\u4f8b"))):
        return "report_and_experience_audit_module"
    if any(token in layer_name for token in (U("\u6e90\u6d41"), U("\u5386\u53f2"), U("\u8fb9\u754c"), U("\u65c1\u8bc1"), U("\u661f\u547d"))):
        return "lineage_boundary_module"
    if any(token in layer_name for token in (U("\u5927\u8fd0"), U("\u5c81\u8fd0"), U("\u6d41\u5e74"), U("\u6d41\u6708"), U("\u5e94\u671f"))):
        return "timing_activation_module"
    if any(token in layer_name for token in (U("\u6574\u4f53"), U("\u56db\u67f1"), U("\u683c\u5c40"), U("\u547d\u5c40"), U("\u6708\u4ee4"), U("\u5341\u795e"))):
        return "natal_structure_module"
    return "book_specific_method_module"


def _output_contract(layer_name: str) -> str:
    module = _functional_module(layer_name)
    contracts = {
        "state_and_climate_module": U("\u8f93\u51fa\u72b6\u6001\u6761\u4ef6\u3001\u53d1\u6325\u7a33\u5b9a\u6027\u3001\u5b66\u4e60\u8010\u529b\u548c\u73af\u5883\u8c03\u8282\u5efa\u8bae\u3002"),
        "circulation_disease_medicine_module": U("\u8f93\u51fa\u4e94\u884c\u6d41\u901a\u3001\u963b\u65ad\u70b9\u3001\u75c5\u836f\u5173\u7cfb\u548c\u4fee\u590d\u8def\u5f84\u3002"),
        "report_and_experience_audit_module": U("\u8f93\u51fa\u901a\u4fd7\u8868\u8fbe\u3001\u53cd\u6a21\u677f\u5ba1\u67e5\u548c\u53ef\u6821\u51c6\u65ad\u8bed\u3002"),
        "lineage_boundary_module": U("\u8f93\u51fa\u6765\u6e90\u8fb9\u754c\u3001\u5386\u53f2\u65c1\u8bc1\u548c\u53ef\u7528\u4e0d\u53ef\u7528\u8303\u56f4\u3002"),
        "timing_activation_module": U("\u8f93\u51fa\u65f6\u95f4\u5c42\u7ea7\u3001\u89e6\u53d1\u5173\u7cfb\u3001\u5211\u51b2\u5408\u5bb3\u548c\u5e94\u671f\u8fb9\u754c\u3002"),
        "natal_structure_module": U("\u8f93\u51fa\u547d\u76d8\u4e3b\u7ebf\u3001\u683c\u5c40\u5165\u53e3\u3001\u7528\u795e\u4fdd\u62a4\u6216\u7ed3\u6784\u77db\u76fe\u3002"),
    }
    return contracts.get(module, U("\u8f93\u51fa\u672c\u4e66\u65b9\u6cd5\u5c42\u7684\u7ed3\u6784\u5316\u5224\u65ad\u548c\u6821\u51c6\u95ee\u9898\u3002"))


def _vote_sub_agents(agent: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for sub_agent in agent.get("sub_agents", []):
        rows.append(
            {
                "agent_id": sub_agent["agent_id"],
                "source_id": sub_agent["source_id"],
                "volume": sub_agent["volume"],
                "book": sub_agent["book"],
                "role": sub_agent["role"],
                "current_status": sub_agent["current_status"],
                "promotion_rule": sub_agent["promotion_rule"],
            }
        )
    return rows


def _sub_agent_votes(votes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for vote in votes:
        for sub_agent in vote.get("sub_agents", []):
            key = str(sub_agent["agent_id"])
            row = dict(by_id.get(key, sub_agent))
            row.setdefault("parent_agent_ids", [])
            parent_ids = set(row["parent_agent_ids"])
            parent_ids.add(str(vote["agent_id"]))
            row["parent_agent_ids"] = sorted(parent_ids)
            by_id[key] = row
    return [by_id[key] for key in sorted(by_id)]


def _field_present(field: str, deep: dict[str, Any], context: dict[str, Any]) -> bool:
    if field == "element_counts":
        return bool(context.get("element_counts"))
    value = deep.get(field)
    return bool(value)


def _book_confidence(
    agent: dict[str, Any],
    fields: list[str],
    missing: list[str],
    deep: dict[str, Any],
    context: dict[str, Any],
) -> float:
    base = 0.56 + 0.06 * len(fields) - 0.04 * len(missing)
    if deep.get("classical_layered_methodology"):
        base += 0.04
    if context.get("provider") and context.get("provider") != "approximate":
        base += 0.03
    source_id = str(agent.get("source_id", ""))
    if source_id in {"tian_bu_zhen_yuan_ren_ming_bu_ia", "jing_xuan_ming_li_yue_yan_nlc"}:
        base -= 0.02
    return max(0.1, min(0.9, round(base, 2)))


def _layer_map(votes: list[dict[str, Any]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for vote in votes:
        for layer in vote.get("primary_layers", []):
            mapping.setdefault(str(layer), []).append(str(vote["agent_id"]))
    return mapping


def _book_conflicts(votes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": "pattern_vs_strength",
            "topic": U("\u683c\u5c40\u4e0e\u5f3a\u5f31"),
            "positions": [U("\u5b50\u5e73\u771f\u8be0\u5b50\u667a\u80fd\u4f53\u91cd\u6708\u4ee4\u683c\u5c40"), U("\u795e\u5cf0\u901a\u8003\u5b50\u667a\u80fd\u4f53\u91cd\u75c5\u836f"), U("\u6ef4\u5929\u9ad3\u8f91\u8981\u5b50\u667a\u80fd\u4f53\u91cd\u6c14\u52bf\u6d41\u901a")],
            "resolution_rule": U("\u5148\u5b9a\u6708\u4ee4\u683c\u5c40\uff0c\u518d\u7528\u75c5\u836f\u548c\u6c14\u52bf\u68c0\u67e5\u683c\u5c40\u80fd\u5426\u8fd0\u8f6c\uff0c\u4e0d\u7528\u5355\u4e00\u5f3a\u5f31\u8986\u76d6\u6240\u6709\u5224\u65ad\u3002"),
        },
        {
            "id": "climate_vs_event",
            "topic": U("\u8c03\u5019\u4e0e\u5e94\u4e8b"),
            "positions": [U("\u7a77\u901a\u5b9d\u9274\u5b50\u667a\u80fd\u4f53\u91cd\u72b6\u6001\u73af\u5883"), U("\u4e09\u547d\u901a\u4f1a\u5e94\u671f\u5b50\u667a\u80fd\u4f53\u91cd\u5c81\u8fd0\u5e94\u671f")],
            "resolution_rule": U("\u8c03\u5019\u89e3\u91ca\u72b6\u6001\u548c\u53d1\u6325\u6761\u4ef6\uff0c\u5c81\u8fd0\u89e3\u91ca\u4e8b\u4ef6\u89e6\u53d1\uff1b\u4e24\u8005\u540c\u5411\u65f6\u63d0\u9ad8\u7f6e\u4fe1\u5ea6\u3002"),
        },
        {
            "id": "classical_quote_boundary",
            "topic": U("\u53e4\u7c4d\u5f15\u7528\u8fb9\u754c"),
            "positions": [vote["book"] for vote in votes],
            "resolution_rule": U("\u5f53\u524d\u53ea\u4f7f\u7528\u65b9\u6cd5\u5361\uff0c\u4e0d\u4f7f\u7528\u672a\u7ecf\u6821\u52d8\u7684\u9010\u5b57\u5f15\u7528\uff1b\u540e\u7eedOCR\u6821\u52d8\u540e\u518d\u5347\u683c\u4e3a\u6761\u6587\u89c4\u5219\u3002"),
        },
    ]


def _book_consensus(votes: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [vote["agent_id"] for vote in votes if vote["confidence"] >= 0.7]
    auxiliary = [vote["agent_id"] for vote in votes if vote["confidence"] < 0.7]
    return {
        "decision": "usable_as_layered_method_debate",
        "primary_agent_ids": primary,
        "auxiliary_agent_ids": auxiliary,
        "conflict_count": len(conflicts),
        "synthesis_rule": U("\u603b\u65ad\u5148\u7528\u4e09\u547d\u7efc\u5408\u6cd5\u7acb\u5c42\u7ea7\uff0c\u518d\u7528\u5b50\u5e73\u683c\u5c40\u5b9a\u4e3b\u7ebf\uff0c\u7528\u795e\u5cf0\u75c5\u836f\u548c\u6ef4\u5929\u9ad3\u6c14\u52bf\u67e5\u6d41\u901a\uff0c\u7528\u7a77\u901a\u5b9d\u9274\u770b\u72b6\u6001\u73af\u5883\uff0c\u6700\u540e\u7528\u7ea6\u8a00\u548c\u97e6\u5343\u91cc\u8bb2\u4e49\u538b\u7f29\u6210\u901a\u4fd7\u62a5\u544a\u3002"),
    }
