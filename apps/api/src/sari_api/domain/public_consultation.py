# ruff: noqa: E501, RUF001 -- multilingual customer copy is intentionally kept intact.

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PublicConsultationLanguage = Literal["en", "zh-CN"]
PublicConsultationField = Literal[
    "facility_type",
    "project_type",
    "location",
    "capacity",
    "timeline",
    "budget_range",
    "contact_name",
    "company",
    "email",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PublicConsultationAgentReply(StrictModel):
    language: PublicConsultationLanguage
    assistant_message: str = Field(min_length=1, max_length=600)


class InvalidPublicConsultationInputError(Exception):
    pass


PROMPTS: dict[PublicConsultationLanguage, dict[PublicConsultationField, str]] = {
    "en": {
        "facility_type": "What type of facility is this for, such as a school, hospital, factory, or central kitchen?",
        "project_type": "Is this a new kitchen, renovation, expansion, or equipment replacement project?",
        "location": "Where will the project be located? Please provide the country and city.",
        "capacity": "What operating capacity do you expect, for example meals per day or kitchen area?",
        "timeline": "What is your expected design, installation, or opening timeline?",
        "budget_range": "Do you have an indicative budget range? You may type Skip.",
        "contact_name": "Who should our project team contact?",
        "company": "What is your organization or company name?",
        "email": "What business email address may our team use to follow up?",
    },
    "zh-CN": {
        "facility_type": "这个项目属于哪类设施，例如学校、医院、工厂食堂或中央厨房？",
        "project_type": "这是新建厨房、改造、扩建，还是设备更换项目？",
        "location": "项目位于哪里？请提供国家和城市。",
        "capacity": "预计运营规模是多少？例如每日供餐量或厨房面积。",
        "timeline": "预计设计、安装或开业时间是什么时候？",
        "budget_range": "是否有初步预算范围？如暂时没有，可以输入“跳过”。",
        "contact_name": "我们的项目团队应该联系谁？",
        "company": "您的机构或公司名称是什么？",
        "email": "销售团队可以使用哪个商务邮箱与您联系？",
    },
}

FIELD_ORDER: tuple[PublicConsultationField, ...] = tuple(PROMPTS["en"])

PUBLIC_KNOWLEDGE_SUMMARY = {
    "en": (
        "Sari Arta is presented as an Indonesia commercial-kitchen engineering partner. "
        "Public services cover project discovery, kitchen workflow and layout planning, "
        "manufacturing coordination, logistics planning, local installation coordination, "
        "commissioning support, and after-sales planning. Public product categories include "
        "preparation, storage, cooking, refrigeration, washing, serving, and ventilation equipment. "
        "No price, delivery, compliance, warranty, capacity, or technical commitment is approved "
        "through this assistant."
    ),
    "zh-CN": (
        "Sari Arta 的公开定位是印度尼西亚商用厨房工程合作伙伴。公开服务包括项目需求梳理、"
        "厨房流程和平面规划、制造协调、物流规划、印尼本地安装协调、调试支持和售后规划。"
        "公开产品类别包括备餐、储存、烹饪、制冷、洗涤、配餐和通风设备。"
        "本助手不会确认价格、交期、合规、质保、产能或技术承诺。"
    ),
}


def validate_public_answer(field: PublicConsultationField, value: str) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) > 500:
        raise InvalidPublicConsultationInputError("The answer is too long.")
    if field == "budget_range" and cleaned.casefold() in {"skip", "跳过", "暂不确定"}:
        return ""
    if len(cleaned) < 2:
        raise InvalidPublicConsultationInputError("Please provide a little more detail.")
    if field == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned):
        raise InvalidPublicConsultationInputError("Please provide a valid business email.")
    if contains_abuse_pattern(cleaned):
        raise InvalidPublicConsultationInputError("This input cannot be processed.")
    return cleaned


def next_field(current: PublicConsultationField) -> PublicConsultationField | None:
    index = FIELD_ORDER.index(current)
    return FIELD_ORDER[index + 1] if index + 1 < len(FIELD_ORDER) else None


def contains_abuse_pattern(value: str) -> bool:
    normalized = value.casefold()
    blocked = (
        "<script",
        "javascript:",
        "ignore previous instructions",
        "reveal system prompt",
        "show internal documents",
        "dump crm",
        "select * from",
    )
    if any(item in normalized for item in blocked):
        return True
    return bool(re.search(r"(.)\1{39,}", normalized))


def deterministic_acknowledgement(
    language: PublicConsultationLanguage,
    current: PublicConsultationField,
    following: PublicConsultationField | None,
) -> str:
    if following is None:
        return (
            "Thank you. Please review the summary and confirm consent before creating an inquiry."
            if language == "en"
            else "谢谢。请检查项目摘要，并在创建询盘前确认联系授权。"
        )
    prefix = "Thank you. " if language == "en" else "谢谢。"
    return prefix + PROMPTS[language][following]
