# ruff: noqa: E501, RUF001 -- multilingual technical copy is intentionally kept intact.

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


LABORATORY_ANIMAL_FACILITY_PACKAGE = DomainAgentManifest(
    domain_key="laboratory_animal_facility",
    domain_name=text(
        "Laboratory Animal Facility",
        "实验动物设施",
        "Fasilitas Hewan Laboratorium",
    ),
    package_key="laboratory_animal_facility",
    package_version="1.0.0",
    agent_key="laboratory_animal_facility.ivc_business_development",
    agent_name=text(
        "IVC Facility Business Development Agent",
        "IVC 设施商务拓展智能体",
        "Agen Pengembangan Bisnis Fasilitas IVC",
    ),
    agent_type="business_development",
    implementation_key="ivc_business_development_v1",
    business_objectives=(
        text(
            "Identify qualified IVC and laboratory-animal-facility opportunities for specialist review.",
            "识别值得交由专家跟进的 IVC 和实验动物设施商机。",
            "Mengidentifikasi peluang IVC dan fasilitas hewan laboratorium yang layak untuk ditinjau spesialis.",
        ),
        text(
            "Collect facility scope, species, capacity, environmental, biosafety, stakeholder, budget, and timeline evidence.",
            "收集设施范围、动物种类、容量、环境、生物安全、决策人、预算和时间信息。",
            "Mengumpulkan data ruang lingkup fasilitas, spesies, kapasitas, lingkungan, biosafety, pemangku kepentingan, anggaran, dan jadwal.",
        ),
        text(
            "Separate commercial discovery from scientific, veterinary, regulatory, and engineering validation.",
            "明确区分商务需求发现与科研、兽医、法规和工程验证。",
            "Memisahkan penemuan kebutuhan komersial dari validasi ilmiah, veteriner, regulasi, dan teknik.",
        ),
        text(
            "Recommend a safe next action without making unsupported compliance or performance claims.",
            "在不作无依据合规或性能承诺的前提下，建议安全的下一步行动。",
            "Merekomendasikan langkah berikutnya secara aman tanpa klaim kepatuhan atau kinerja yang tidak didukung.",
        ),
    ),
    qualification_fields=(
        QualificationField(
            key="facility_project_type",
            label=text("Facility project type", "设施项目类型", "Jenis proyek fasilitas"),
            description=text(
                "New facility, expansion, retrofit, equipment replacement, or feasibility study.",
                "新建设施、扩建、改造、设备替换或可行性研究。",
                "Fasilitas baru, perluasan, renovasi, penggantian peralatan, atau studi kelayakan.",
            ),
            field_type="choice",
            required=True,
            choices=("new_facility", "expansion", "retrofit", "replacement", "feasibility"),
        ),
        QualificationField(
            key="facility_location",
            label=text("Facility location", "设施地点", "Lokasi fasilitas"),
            description=text(
                "Country, city, and site or campus context.",
                "国家、城市以及园区或场地背景。",
                "Negara, kota, dan konteks lokasi atau kampus.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="research_program_and_species",
            label=text(
                "Research program and species", "研究方向和动物种类", "Program riset dan spesies"
            ),
            description=text(
                "Intended research use and animal species; scientific suitability requires expert validation.",
                "计划研究用途和动物种类；科研适用性必须由专家验证。",
                "Penggunaan riset dan spesies hewan; kesesuaian ilmiah memerlukan validasi ahli.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="planned_capacity",
            label=text("Planned capacity", "计划容量", "Kapasitas yang direncanakan"),
            description=text(
                "Expected cages, racks, rooms, or phased capacity.",
                "预计笼位、笼架、房间或分期容量。",
                "Perkiraan jumlah kandang, rak, ruangan, atau kapasitas bertahap.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="containment_and_biosafety_context",
            label=text(
                "Containment and biosafety context",
                "隔离与生物安全背景",
                "Konteks containment dan biosafety",
            ),
            description=text(
                "Known containment, biosecurity, quarantine, or institutional biosafety requirements.",
                "已知的隔离、生物安保、检疫或机构生物安全要求。",
                "Persyaratan containment, biosecurity, karantina, atau biosafety institusi yang diketahui.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="environmental_and_hvac_requirements",
            label=text(
                "Environmental and HVAC requirements",
                "环境与 HVAC 要求",
                "Persyaratan lingkungan dan HVAC",
            ),
            description=text(
                "Known temperature, humidity, pressure, ventilation, exhaust, redundancy, and monitoring needs.",
                "已知温度、湿度、压差、通风、排风、冗余和监控需求。",
                "Kebutuhan suhu, kelembapan, tekanan, ventilasi, exhaust, redundansi, dan pemantauan yang diketahui.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="room_and_workflow_scope",
            label=text("Room and workflow scope", "房间与流程范围", "Ruang dan alur kerja"),
            description=text(
                "Housing, procedure, quarantine, washing, sterilization, storage, and support-room scope.",
                "饲养、实验、检疫、清洗、灭菌、储存及辅助房间范围。",
                "Ruang pemeliharaan, prosedur, karantina, pencucian, sterilisasi, penyimpanan, dan pendukung.",
            ),
            field_type="multi_choice",
            required=True,
            choices=(
                "housing",
                "procedure",
                "quarantine",
                "washing",
                "sterilization",
                "storage",
                "support",
            ),
        ),
        QualificationField(
            key="existing_design_information",
            label=text(
                "Existing design information", "现有设计资料", "Informasi desain yang tersedia"
            ),
            description=text(
                "Availability of room data, layouts, user requirement specifications, utilities, and design stage.",
                "是否已有房间数据、布局、用户需求文件、机电条件及当前设计阶段。",
                "Ketersediaan data ruang, layout, spesifikasi kebutuhan pengguna, utilitas, dan tahap desain.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="validation_and_compliance_expectations",
            label=text(
                "Validation and compliance expectations",
                "验证与合规预期",
                "Harapan validasi dan kepatuhan",
            ),
            description=text(
                "Applicable institutional, national, accreditation, commissioning, or documentation expectations.",
                "适用的机构、国家、认证、调试或文件要求。",
                "Harapan institusi, nasional, akreditasi, commissioning, atau dokumentasi yang berlaku.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="procurement_and_decision_authority",
            label=text(
                "Procurement and decision authority",
                "采购与决策权限",
                "Pengadaan dan otoritas keputusan",
            ),
            description=text(
                "Project owner, principal investigator, veterinarian, facility manager, consultant, procurement, and approval path.",
                "业主、PI、兽医、设施经理、顾问、采购和审批流程。",
                "Pemilik proyek, peneliti utama, dokter hewan, manajer fasilitas, konsultan, pengadaan, dan jalur persetujuan.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="budget",
            label=text("Indicative budget", "预估预算", "Anggaran indikatif"),
            description=text(
                "Available budget range, currency, funding source, and approval status.",
                "预算范围、币种、资金来源和审批状态。",
                "Rentang anggaran, mata uang, sumber pendanaan, dan status persetujuan.",
            ),
            field_type="text",
            required=False,
        ),
        QualificationField(
            key="target_timeline",
            label=text("Target timeline", "目标时间", "Target jadwal"),
            description=text(
                "Target design freeze, procurement, installation, commissioning, or facility operation date.",
                "目标设计冻结、采购、安装、调试或设施投运日期。",
                "Target desain final, pengadaan, instalasi, commissioning, atau tanggal operasional fasilitas.",
            ),
            field_type="text",
            required=True,
        ),
        QualificationField(
            key="service_and_lifecycle_scope",
            label=text(
                "Service and lifecycle scope",
                "服务与生命周期范围",
                "Ruang lingkup layanan dan siklus hidup",
            ),
            description=text(
                "Installation, commissioning support, training, preventive service, spare parts, and consumables expectations.",
                "安装、调试支持、培训、预防性维护、备件和耗材需求。",
                "Harapan instalasi, dukungan commissioning, pelatihan, servis preventif, suku cadang, dan bahan habis pakai.",
            ),
            field_type="multi_choice",
            required=False,
            choices=(
                "installation",
                "commissioning_support",
                "training",
                "preventive_service",
                "spare_parts",
                "consumables",
            ),
        ),
    ),
    knowledge_categories=(
        KnowledgeCategory(
            key="ivc_systems_and_components",
            label=text("IVC systems and components", "IVC 系统与部件", "Sistem dan komponen IVC"),
            description=text(
                "Approved product families, configurations, compatible components, and technical literature.",
                "经批准的产品系列、配置、兼容部件和技术资料。",
                "Keluarga produk, konfigurasi, komponen kompatibel, dan literatur teknis yang disetujui.",
            ),
            expert_review_required=True,
        ),
        KnowledgeCategory(
            key="facility_planning_and_workflow",
            label=text(
                "Facility planning and workflow",
                "设施规划与流程",
                "Perencanaan fasilitas dan alur kerja",
            ),
            description=text(
                "Approved planning principles for rooms, personnel, animals, materials, washing, and waste flows.",
                "经批准的房间、人员、动物、物料、清洗和废弃物流规划原则。",
                "Prinsip perencanaan ruang, personel, hewan, material, pencucian, dan limbah yang disetujui.",
            ),
            expert_review_required=True,
        ),
        KnowledgeCategory(
            key="environmental_control_and_hvac",
            label=text(
                "Environmental control and HVAC", "环境控制与 HVAC", "Kontrol lingkungan dan HVAC"
            ),
            description=text(
                "Approved environmental, ventilation, pressure, exhaust, monitoring, and utility guidance.",
                "经批准的环境、通风、压差、排风、监控和机电指导。",
                "Panduan lingkungan, ventilasi, tekanan, exhaust, pemantauan, dan utilitas yang disetujui.",
            ),
            expert_review_required=True,
        ),
        KnowledgeCategory(
            key="biosafety_biosecurity_and_animal_welfare",
            label=text(
                "Biosafety, biosecurity, and animal welfare",
                "生物安全、生物安保与动物福利",
                "Biosafety, biosecurity, dan kesejahteraan hewan",
            ),
            description=text(
                "Approved references that always require qualified local and institutional interpretation.",
                "必须由当地和机构专业人员解释的经批准参考资料。",
                "Referensi yang disetujui dan selalu memerlukan interpretasi profesional lokal dan institusional.",
            ),
            expert_review_required=True,
        ),
        KnowledgeCategory(
            key="installation_commissioning_and_validation",
            label=text(
                "Installation, commissioning, and validation",
                "安装、调试与验证",
                "Instalasi, commissioning, dan validasi",
            ),
            description=text(
                "Approved scope, prerequisites, records, tests, training, and handover information.",
                "经批准的范围、前提、记录、测试、培训和移交信息。",
                "Informasi ruang lingkup, prasyarat, catatan, pengujian, pelatihan, dan serah terima yang disetujui.",
            ),
            expert_review_required=True,
        ),
        KnowledgeCategory(
            key="service_parts_and_consumables",
            label=text(
                "Service, parts, and consumables",
                "服务、备件与耗材",
                "Layanan, suku cadang, dan bahan habis pakai",
            ),
            description=text(
                "Approved lifecycle support, preventive service, parts, and consumables information.",
                "经批准的生命周期支持、预防性维护、备件和耗材信息。",
                "Informasi dukungan siklus hidup, servis preventif, suku cadang, dan bahan habis pakai yang disetujui.",
            ),
        ),
        KnowledgeCategory(
            key="approved_cases_and_capabilities",
            label=text(
                "Approved cases and capabilities",
                "批准案例与能力",
                "Kasus dan kemampuan yang disetujui",
            ),
            description=text(
                "Verified organizational capabilities and approved case references without invented claims.",
                "经过验证的企业能力和批准案例，不允许虚构项目声明。",
                "Kemampuan organisasi terverifikasi dan referensi kasus yang disetujui tanpa klaim rekaan.",
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
                "Structured project qualification and missing-information identification.",
                "结构化项目资格判断和缺失信息识别。",
                "Kualifikasi proyek terstruktur dan identifikasi informasi yang belum tersedia.",
            ),
        ),
        CapabilityRequirement(
            key="structured_output",
            required=True,
            status="available",
            description=text(
                "Schema-validated business summary, factors, risks, and next action.",
                "经过 Schema 校验的业务摘要、因素、风险和下一步行动。",
                "Ringkasan bisnis, faktor, risiko, dan langkah berikutnya yang tervalidasi skema.",
            ),
        ),
        CapabilityRequirement(
            key="localized_response",
            required=True,
            status="available",
            description=text(
                "Localized responses in English, Chinese, and Indonesian.",
                "支持英文、中文和印尼语本地化输出。",
                "Respons terlokalisasi dalam bahasa Inggris, Mandarin, dan Indonesia.",
            ),
        ),
        CapabilityRequirement(
            key="human_review",
            required=True,
            status="available",
            description=text(
                "Mandatory human review for scientific, veterinary, regulatory, engineering, and commercial conclusions.",
                "科研、兽医、法规、工程和商业结论必须人工审核。",
                "Tinjauan manusia wajib untuk kesimpulan ilmiah, veteriner, regulasi, teknik, dan komersial.",
            ),
        ),
        CapabilityRequirement(
            key="approved_knowledge_retrieval",
            required=True,
            status="planned",
            description=text(
                "Future cited retrieval from approved IVC and facility knowledge; not implemented in this package release.",
                "未来从批准的 IVC 和设施知识中进行带引用检索；本版本尚未实现。",
                "Pengambilan bersitasi dari pengetahuan IVC dan fasilitas yang disetujui; belum diterapkan pada rilis paket ini.",
            ),
        ),
    ),
)
