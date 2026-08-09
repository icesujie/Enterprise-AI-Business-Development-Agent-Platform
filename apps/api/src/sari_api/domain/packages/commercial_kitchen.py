# ruff: noqa: E501, RUF001 -- multilingual business copy is intentionally kept intact.

from __future__ import annotations

from sari_api.domain.packages.models import (
    CapabilityRequirement,
    DomainAgentManifest,
    KnowledgeCategory,
    LocalizedText,
    QualificationField,
)


def text(en: str, zh_cn: str, id_text: str) -> LocalizedText:
    return LocalizedText(en=en, zh_cn=zh_cn, id=id_text)


COMMERCIAL_KITCHEN_PACKAGE = DomainAgentManifest(
    domain_key="commercial_kitchen",
    domain_name=text("Commercial Kitchen", "商用厨房", "Dapur Komersial"),
    package_key="commercial_kitchen",
    package_version="1.0.0",
    agent_key="commercial_kitchen.lead_qualification",
    agent_name=text(
        "Sari Arta Commercial Kitchen Agent",
        "Sari Arta 商用厨房智能体",
        "Agen Dapur Komersial Sari Arta",
    ),
    agent_type="business_development",
    implementation_key="lead_qualification_v1",
    business_objectives=(
        text(
            "Identify commercially viable institutional kitchen projects and their next sales action.",
            "识别具有商业价值的机构厨房项目，并给出下一步销售行动。",
            "Mengidentifikasi proyek dapur institusional yang layak secara komersial dan tindakan penjualan berikutnya.",
        ),
        text(
            "Collect enough project, capacity, stakeholder, budget, and timeline evidence for human qualification.",
            "收集足够的项目、产能、决策人、预算和时间证据，供人工资格判断。",
            "Mengumpulkan bukti proyek, kapasitas, pemangku kepentingan, anggaran, dan jadwal untuk kualifikasi manusia.",
        ),
        text(
            "Route incomplete or risky commitments to Sari Arta sales and engineering specialists.",
            "把信息不足或涉及承诺的事项交给 Sari Arta 销售和工程人员。",
            "Mengarahkan informasi yang belum lengkap atau komitmen berisiko kepada spesialis penjualan dan teknik Sari Arta.",
        ),
    ),
    qualification_fields=(
        QualificationField(
            key="facility_type",
            label=text("Facility type", "设施类型", "Jenis fasilitas"),
            description=text(
                "School, hospital, factory cafeteria, central kitchen, or another facility.",
                "学校、医院、工厂食堂、中央厨房或其他设施。",
                "Sekolah, rumah sakit, kantin pabrik, dapur pusat, atau fasilitas lain.",
            ),
            field_type="choice",
            required=True,
            choices=("school", "hospital", "factory_cafeteria", "central_kitchen", "other"),
        ),
        QualificationField(
            key="meal_capacity",
            label=text("Meal capacity", "供餐能力", "Kapasitas makanan"),
            description=text(
                "Expected meals per service or per day.",
                "预计每餐或每日供餐量。",
                "Perkiraan jumlah porsi per layanan atau per hari.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="project_location",
            label=text("Project location", "项目地点", "Lokasi proyek"),
            description=text(
                "Country and city where the kitchen will be delivered.",
                "厨房项目交付所在国家和城市。",
                "Negara dan kota lokasi pelaksanaan proyek dapur.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="service_scope",
            label=text("Required service scope", "所需服务范围", "Ruang lingkup layanan"),
            description=text(
                "Design, equipment, logistics, installation, training, or after-sales support.",
                "设计、设备、物流、安装、培训或售后支持。",
                "Desain, peralatan, logistik, instalasi, pelatihan, atau layanan purnajual.",
            ),
            field_type="multi_choice",
            required=True,
            choices=("design", "equipment", "logistics", "installation", "training", "after_sales"),
        ),
        QualificationField(
            key="floor_plan_and_utilities",
            label=text("Floor plan and utilities", "平面图和机电条件", "Denah dan utilitas"),
            description=text(
                "Availability of floor plans and known electrical, water, gas, drainage, and ventilation inputs.",
                "是否有平面图，以及已知电、水、燃气、排水和通风条件。",
                "Ketersediaan denah serta data listrik, air, gas, drainase, dan ventilasi.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="budget",
            label=text("Indicative budget", "预估预算", "Anggaran indikatif"),
            description=text(
                "Budget amount, currency, or current budget approval status.",
                "预算金额、币种或当前预算审批状态。",
                "Nilai anggaran, mata uang, atau status persetujuan anggaran.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="decision_authority",
            label=text("Decision authority", "决策权限", "Otoritas keputusan"),
            description=text(
                "Known decision maker, committee, consultant, owner, or procurement authority.",
                "已知决策人、委员会、顾问、业主或采购负责人。",
                "Pengambil keputusan, komite, konsultan, pemilik, atau otoritas pengadaan yang diketahui.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="target_timeline",
            label=text("Target timeline", "目标时间", "Target jadwal"),
            description=text(
                "Target design, procurement, installation, or opening date.",
                "目标设计、采购、安装或开业日期。",
                "Target tanggal desain, pengadaan, instalasi, atau pembukaan.",
            ),
            field_type="text",
            required=True,
        ),
    ),
    knowledge_categories=(
        KnowledgeCategory(
            key="engineering_capability",
            label=text("Engineering capability", "工程能力", "Kemampuan teknik"),
            description=text(
                "Approved design, workflow, installation, and delivery capability statements.",
                "经批准的设计、流程、安装和交付能力说明。",
                "Pernyataan kemampuan desain, alur kerja, instalasi, dan pelaksanaan yang disetujui.",
            ),
        ),
        KnowledgeCategory(
            key="equipment_catalogue",
            label=text("Equipment catalogue", "设备目录", "Katalog peralatan"),
            description=text(
                "Approved product families and technical literature.",
                "经批准的产品系列和技术资料。",
                "Keluarga produk dan literatur teknis yang disetujui.",
            ),
            expert_review_required=True,
        ),
        KnowledgeCategory(
            key="industry_solutions",
            label=text("Industry solutions", "行业解决方案", "Solusi industri"),
            description=text(
                "Approved school, hospital, factory, and central-kitchen solution patterns.",
                "经批准的学校、医院、工厂和中央厨房方案模式。",
                "Pola solusi sekolah, rumah sakit, pabrik, dan dapur pusat yang disetujui.",
            ),
        ),
        KnowledgeCategory(
            key="delivery_and_service",
            label=text("Delivery and service", "交付和服务", "Pelaksanaan dan layanan"),
            description=text(
                "Approved China–Indonesia delivery, installation, handover, and service scope.",
                "经批准的中国—印尼交付、安装、移交和服务范围。",
                "Ruang lingkup pengiriman Tiongkok–Indonesia, instalasi, serah terima, dan layanan yang disetujui.",
            ),
            expert_review_required=True,
        ),
    ),
    required_capabilities=(
        CapabilityRequirement(
            key="lead_qualification",
            required=True,
            status="available",
            description=text(
                "Structured A/B/C lead qualification with human review.",
                "带人工审核的 A/B/C 结构化线索资格评估。",
                "Kualifikasi prospek A/B/C terstruktur dengan tinjauan manusia.",
            ),
        ),
        CapabilityRequirement(
            key="structured_output",
            required=True,
            status="available",
            description=text(
                "Schema-validated business output without hidden reasoning.",
                "经过 Schema 校验且不暴露隐藏推理的业务输出。",
                "Keluaran bisnis tervalidasi skema tanpa penalaran tersembunyi.",
            ),
        ),
        CapabilityRequirement(
            key="localized_response",
            required=True,
            status="available",
            description=text(
                "Business-facing responses in English, Chinese, or Indonesian.",
                "提供英文、中文或印尼语业务输出。",
                "Respons bisnis dalam bahasa Inggris, Mandarin, atau Indonesia.",
            ),
        ),
        CapabilityRequirement(
            key="human_review",
            required=True,
            status="available",
            description=text(
                "Human review for commercial commitments, pricing, and low-confidence conclusions.",
                "商业承诺、价格以及低置信度结论需要人工审核。",
                "Tinjauan manusia untuk komitmen komersial, harga, dan kesimpulan dengan keyakinan rendah.",
            ),
        ),
        CapabilityRequirement(
            key="approved_knowledge_retrieval",
            required=False,
            status="planned",
            description=text(
                "Future retrieval from approved and cited Sari Arta knowledge.",
                "未来从经批准且可引用的 Sari Arta 知识中检索。",
                "Pengambilan informasi mendatang dari pengetahuan Sari Arta yang disetujui dan dapat dikutip.",
            ),
        ),
    ),
)
