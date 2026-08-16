# ruff: noqa: E501, RUF001 -- multilingual business copy is intentionally kept intact.

from __future__ import annotations

from sari_api.domain.packages.commercial_kitchen import text
from sari_api.domain.packages.models import (
    CapabilityRequirement,
    DomainAgentManifest,
    KnowledgeCategory,
    QualificationField,
)

MARKETING_CONTENT_AGENT_PACKAGE = DomainAgentManifest(
    domain_key="commercial_kitchen",
    domain_name=text("Commercial Kitchen", "商用厨房", "Dapur Komersial"),
    package_key="commercial_kitchen",
    package_version="1.0.0",
    agent_key="commercial_kitchen.marketing_content",
    agent_name=text(
        "Sari Arta Marketing Content Agent",
        "Sari Arta 营销内容智能体",
        "Agen Konten Pemasaran Sari Arta",
    ),
    agent_type="marketing_content",
    implementation_key="marketing_content_policy_v1",
    business_objectives=(
        text(
            "Prepare governed B2B marketing drafts only from explicitly eligible public knowledge.",
            "仅依据明确合格的公开知识准备受治理的 B2B 营销草稿。",
            "Menyiapkan draf pemasaran B2B yang terkelola hanya dari pengetahuan publik yang secara eksplisit memenuhi syarat.",
        ),
        text(
            "Preserve exact evidence references and require human review before approval.",
            "保留准确证据引用，并在批准前强制人工审核。",
            "Mempertahankan referensi bukti yang tepat dan mewajibkan tinjauan manusia sebelum persetujuan.",
        ),
        text(
            "Prevent private, commercial, customer, supplier, and internal operational knowledge from entering marketing generation.",
            "阻止私有、商业、客户、供应商和内部运营知识进入营销生成流程。",
            "Mencegah pengetahuan privat, komersial, pelanggan, pemasok, dan operasional internal masuk ke proses pembuatan pemasaran.",
        ),
    ),
    qualification_fields=(
        QualificationField(
            key="content_type",
            label=text("Content type", "内容类型", "Jenis konten"),
            description=text(
                "Website article, TikTok script, Instagram Reel script, Facebook post, or email draft.",
                "网站文章、TikTok 脚本、Instagram Reel 脚本、Facebook 帖子或邮件草稿。",
                "Artikel situs web, skrip TikTok, skrip Instagram Reel, posting Facebook, atau draf email.",
            ),
            field_type="choice",
            required=True,
            choices=(
                "website_article",
                "tiktok_script",
                "instagram_reel_script",
                "facebook_post",
                "email_draft",
            ),
        ),
        QualificationField(
            key="audience",
            label=text("Primary audience", "主要受众", "Audiens utama"),
            description=text(
                "The institutional or industrial audience for the draft.",
                "草稿面向的机构或工业受众。",
                "Audiens institusional atau industri untuk draf tersebut.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="business_objective",
            label=text("Business objective", "业务目标", "Tujuan bisnis"),
            description=text(
                "The controlled business purpose of the requested content.",
                "所请求内容的受控业务目的。",
                "Tujuan bisnis terkontrol dari konten yang diminta.",
            ),
            field_type="text",
            required=True,
        ),
    ),
    knowledge_categories=(
        KnowledgeCategory(
            key="public_company_profile",
            label=text("Public company profile", "公开公司介绍", "Profil perusahaan publik"),
            description=text(
                "Approved public company capability and service statements.",
                "经批准的公开公司能力与服务说明。",
                "Pernyataan kemampuan dan layanan perusahaan publik yang disetujui.",
            ),
        ),
        KnowledgeCategory(
            key="public_case_study",
            label=text("Public case study", "公开案例", "Studi kasus publik"),
            description=text(
                "Approved case evidence explicitly cleared for public marketing use.",
                "明确获准用于公开营销的经批准案例证据。",
                "Bukti kasus yang disetujui dan secara eksplisit diizinkan untuk pemasaran publik.",
            ),
        ),
        KnowledgeCategory(
            key="public_product_service",
            label=text("Public product and service information", "公开产品与服务信息", "Informasi produk dan layanan publik"),
            description=text(
                "Approved public product categories and service descriptions without private prices.",
                "不含私有价格的经批准公开产品类别和服务说明。",
                "Kategori produk dan deskripsi layanan publik yang disetujui tanpa harga privat.",
            ),
        ),
        KnowledgeCategory(
            key="public_brand_guideline",
            label=text("Public brand guideline", "公开品牌指南", "Pedoman merek publik"),
            description=text(
                "Approved brand voice, terminology, claims, and calls to action.",
                "经批准的品牌语调、术语、声明和行动号召。",
                "Nada merek, terminologi, klaim, dan ajakan bertindak yang disetujui.",
            ),
        ),
    ),
    required_capabilities=(
        CapabilityRequirement(
            key="public_marketing_content_generation",
            required=True,
            status="available",
            description=text(
                "Eligibility to create governed marketing drafts; it grants no approval, publishing, communication, or CRM write authority.",
                "创建受治理营销草稿的资格；不授予审批、发布、沟通或 CRM 写入权限。",
                "Kelayakan untuk membuat draf pemasaran terkelola; tidak memberikan kewenangan persetujuan, penerbitan, komunikasi, atau penulisan CRM.",
            ),
        ),
        CapabilityRequirement(
            key="approved_knowledge_retrieval",
            required=True,
            status="available",
            description=text(
                "Retrieve only approved, active, published, same-agent public-marketing evidence.",
                "仅检索已批准、已启用、已发布且绑定同一智能体的公开营销证据。",
                "Mengambil hanya bukti pemasaran publik yang disetujui, aktif, diterbitkan, dan terikat ke agen yang sama.",
            ),
        ),
        CapabilityRequirement(
            key="human_review",
            required=True,
            status="available",
            description=text(
                "Generated eligibility never replaces independent human review and approval.",
                "生成资格永远不能取代独立人工审核与批准。",
                "Kelayakan pembuatan tidak pernah menggantikan tinjauan dan persetujuan manusia yang independen.",
            ),
        ),
    ),
    supported_locales=("en", "zh-CN"),
    default_locale="en",
)
