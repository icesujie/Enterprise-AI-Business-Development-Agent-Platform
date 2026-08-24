import type { Locale } from "@/i18n/config";

export type SolutionPageContent = {
  path: string;
  metadataTitle: string;
  metadataDescription: string;
  breadcrumbLabel: string;
  eyebrow: string;
  title: string;
  description: string;
  overviewEyebrow: string;
  overviewTitle: string;
  overviewDescription: string;
  priorities: ReadonlyArray<{ title: string; description?: string }>;
  scopeEyebrow: string;
  scopeTitle: string;
  scopeDescription: string;
  scopeItems: ReadonlyArray<{
    number: string;
    title: string;
    description: string;
  }>;
  inputsEyebrow: string;
  inputsTitle: string;
  inputsDescription: string;
  inputs: readonly string[];
  deliveryEyebrow: string;
  deliveryTitle: string;
  deliveryDescription: string;
  consultationEyebrow: string;
  consultationTitle: string;
  consultationDescription: string;
  consultationAgentLabel: string;
  consultationFormLabel: string;
  relatedLinks?: ReadonlyArray<{ label: string; href: string }>;
};

export const schoolCanteenSolution: Record<Locale, SolutionPageContent> = {
  en: {
    path: "/solutions/school-canteen-kitchen",
    metadataTitle: "School Canteen Kitchen Solutions Indonesia",
    metadataDescription:
      "Plan a school canteen commercial kitchen in Indonesia around meal volume, service windows, workflow, equipment coordination, site readiness, and local installation.",
    breadcrumbLabel: "School canteen kitchens",
    eyebrow: "School canteen kitchen solutions · Indonesia",
    title: "School canteen kitchens planned around the daily meal service.",
    description:
      "Sari Arta coordinates commercial kitchen design, equipment and manufacturing information, logistics, Indonesia-based installation, commissioning, and handover around the approved school project scope.",
    overviewEyebrow: "Operational planning",
    overviewTitle: "Start with the way the canteen needs to operate.",
    overviewDescription:
      "A useful school kitchen brief connects the number of meals, menu, service windows, student movement, staffing, cleaning routines, available space, and project interfaces before equipment decisions are fixed.",
    priorities: [
      {
        title: "Meal service rhythm",
        description:
          "Clarify expected meal volume, concentrated service periods, menu pattern, and how food reaches students.",
      },
      {
        title: "Working flow",
        description:
          "Review movement from receiving and storage through preparation, cooking, service, washing, and cleaning.",
      },
      {
        title: "Facility interfaces",
        description:
          "Coordinate the available area, access, utilities, floor-plan inputs, timeline, and responsibilities with the wider project team.",
      },
    ],
    scopeEyebrow: "Coordinated project scope",
    scopeTitle: "One delivery framework from early planning to handover.",
    scopeDescription:
      "The exact responsibility matrix is agreed for each project. These are the main coordination areas available to a school canteen project.",
    scopeItems: [
      {
        number: "01",
        title: "Workflow and capacity planning",
        description:
          "Translate meal volume, service windows, menu, staffing, hygiene flow, and space constraints into coordinated zones and equipment requirements.",
      },
      {
        number: "02",
        title: "Equipment and manufacturing coordination",
        description:
          "Connect the approved equipment scope with China-based manufacturing capability, technical review, and defined quality checkpoints.",
      },
      {
        number: "03",
        title: "Logistics and site readiness",
        description:
          "Align shipping information, delivery access, utilities, site readiness, sequencing, and installation responsibilities before equipment reaches the school.",
      },
      {
        number: "04",
        title: "Local installation and handover",
        description:
          "Coordinate Indonesia-based placement, connection checks, testing, commissioning records, handover information, and operator familiarisation for the approved scope.",
      },
    ],
    inputsEyebrow: "Prepare for consultation",
    inputsTitle: "Early estimates are enough to begin the project discussion.",
    inputsDescription:
      "Missing information can be identified during discovery. Share what is known and clearly mark what is still being decided.",
    inputs: [
      "School location and current project stage",
      "Expected meals per service period and service times",
      "Menu or food-service model",
      "Available kitchen and serving area",
      "Floor plans, access, and known utility information",
      "Target opening period and known procurement requirements",
    ],
    deliveryEyebrow: "China–Indonesia delivery model",
    deliveryTitle:
      "Manufacturing coordination connected to local project execution.",
    deliveryDescription:
      "Sari Arta connects the approved design and equipment scope with manufacturing information, delivery preparation, Indonesia-based installation, commissioning, and after-sales coordination.",
    consultationEyebrow: "Public project consultation",
    consultationTitle:
      "Organize your school canteen kitchen brief for human review.",
    consultationDescription:
      "Use the consultation agent to record the facility, location, capacity, timeline, and contact details. It does not provide pricing, delivery, or technical commitments.",
    consultationAgentLabel: "Start project consultation",
    consultationFormLabel: "Use consultation form",
  },
  "zh-CN": {
    path: "/solutions/school-canteen-kitchen",
    metadataTitle: "印度尼西亚学校食堂厨房解决方案",
    metadataDescription:
      "围绕供餐量、供餐时段、工作流程、设备协调、场地准备和本地安装，规划印度尼西亚学校食堂商用厨房。",
    breadcrumbLabel: "学校食堂厨房",
    eyebrow: "学校食堂厨房解决方案 · 印度尼西亚",
    title: "围绕每日供餐运营规划学校食堂厨房。",
    description:
      "Sari Arta 围绕已批准的学校项目范围，协调商用厨房设计、设备与制造信息、物流、印度尼西亚本地安装、调试和交接。",
    overviewEyebrow: "运营规划",
    overviewTitle: "从食堂实际运营方式开始。",
    overviewDescription:
      "一份有效的学校厨房需求应在确定设备前，连接餐数、菜单、供餐时段、学生动线、人员配置、清洁流程、可用空间和项目接口。",
    priorities: [
      {
        title: "供餐节奏",
        description:
          "明确预计餐数、集中供餐时段、菜单模式，以及餐食如何送达学生。",
      },
      {
        title: "工作流程",
        description: "审视从收货、储存到准备、烹饪、供餐、洗涤和清洁的动线。",
      },
      {
        title: "场地接口",
        description:
          "与项目团队协调可用面积、通道、公用设施、平面图资料、时间和责任分工。",
      },
    ],
    scopeEyebrow: "协调项目范围",
    scopeTitle: "从早期规划到交接的一体化交付框架。",
    scopeDescription:
      "每个项目都会单独确认准确的责任分工。以下是学校食堂项目可采用的主要协调范围。",
    scopeItems: [
      {
        number: "01",
        title: "流程与产能规划",
        description:
          "把餐数、供餐时段、菜单、人员、卫生动线和空间限制转化为协调分区与设备需求。",
      },
      {
        number: "02",
        title: "设备与制造协调",
        description:
          "把已批准设备范围与中国制造能力、技术审核和明确的质量检查节点连接起来。",
      },
      {
        number: "03",
        title: "物流与场地准备",
        description:
          "在设备到达学校前，协调运输信息、进场条件、公用设施、场地准备、顺序和安装责任。",
      },
      {
        number: "04",
        title: "本地安装与交接",
        description:
          "围绕已批准范围协调印度尼西亚本地就位、连接检查、测试、调试记录、交接资料和操作熟悉支持。",
      },
    ],
    inputsEyebrow: "咨询准备",
    inputsTitle: "早期估算信息已经足够开始项目讨论。",
    inputsDescription:
      "可在需求了解阶段识别缺失信息。请提供已知内容，并明确哪些事项仍待决定。",
    inputs: [
      "学校地点和当前项目阶段",
      "每个供餐时段的预计餐数和供餐时间",
      "菜单或餐饮服务模式",
      "可用厨房和供餐面积",
      "平面图、进场条件和已知公用设施信息",
      "目标启用时间和已知采购要求",
    ],
    deliveryEyebrow: "中国—印度尼西亚交付模式",
    deliveryTitle: "把制造协调与本地项目执行连接起来。",
    deliveryDescription:
      "Sari Arta 将已批准设计和设备范围与制造信息、交付准备、印度尼西亚本地安装、调试和售后协调连接起来。",
    consultationEyebrow: "公开项目咨询",
    consultationTitle: "整理学校食堂厨房需求，交由人工审核。",
    consultationDescription:
      "使用咨询智能体记录设施、地点、产能、时间和联系方式。它不会提供价格、交付或技术承诺。",
    consultationAgentLabel: "开始项目咨询",
    consultationFormLabel: "使用咨询表单",
  },
};
