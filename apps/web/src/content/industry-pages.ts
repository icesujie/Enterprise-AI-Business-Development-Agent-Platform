import type { Locale } from "@/i18n/config";

export type IndustryPageContent = {
  path: string;
  metadataTitle: string;
  metadataDescription: string;
  breadcrumbLabel: string;
  eyebrow: string;
  title: string;
  description: string;
  needsEyebrow: string;
  needsTitle: string;
  needsDescription: string;
  needs: ReadonlyArray<{ title: string; description: string }>;
  projectEyebrow: string;
  projectTitle: string;
  projectDescription: string;
  projectTypes: ReadonlyArray<{ title: string; description: string }>;
  workflowEyebrow: string;
  workflowTitle: string;
  workflowDescription: string;
  workflowAreas: ReadonlyArray<{ title: string; description: string }>;
  solutionEyebrow: string;
  solutionTitle: string;
  solutionDescription: string;
  solutionLinkLabel: string;
  consultationEyebrow: string;
  consultationTitle: string;
  consultationDescription: string;
  consultationAgentLabel: string;
  consultationFormLabel: string;
};

export const schoolsIndustry: Record<Locale, IndustryPageContent> = {
  en: {
    path: "/industries/schools",
    metadataTitle: "Commercial Kitchen Solutions for Schools Indonesia",
    metadataDescription:
      "Plan new school canteen kitchens and renovation projects in Indonesia around institutional meal preparation, workflow, storage, cooking, service, and washing.",
    breadcrumbLabel: "Schools",
    eyebrow: "Commercial kitchen solutions for schools · Indonesia",
    title: "School kitchens shaped around meals, movement, and daily routines.",
    description:
      "Sari Arta helps school project teams organize commercial kitchen requirements around concentrated meal periods, institutional food preparation, student movement, practical cleaning, and the available facility.",
    needsEyebrow: "School food-service needs",
    needsTitle: "The operating brief comes before the equipment list.",
    needsDescription:
      "School canteen planning begins with who the kitchen serves, when meals move, how the team works, and how each area supports a repeatable daily routine.",
    needs: [
      {
        title: "Institutional meal preparation",
        description:
          "Clarify expected meals, menu pattern, preparation approach, staffing, and the service windows that shape daily demand.",
      },
      {
        title: "Student and staff movement",
        description:
          "Consider how kitchen work, meal service, student circulation, returns, and cleaning interact within the available facility.",
      },
      {
        title: "Maintainable daily operation",
        description:
          "Include cleaning routines, service access, operating guidance, equipment records, and handover needs in the project discussion.",
      },
    ],
    projectEyebrow: "Project starting points",
    projectTitle: "Support for new school kitchens and canteen renovation.",
    projectDescription:
      "The engineering discussion changes with the project condition. Existing information and constraints are reviewed before a detailed scope is agreed.",
    projectTypes: [
      {
        title: "New kitchen projects",
        description:
          "Coordinate meal requirements, workflow zones, equipment scope, utility inputs, access, manufacturing information, site readiness, installation, and handover with the wider project team.",
      },
      {
        title: "Canteen renovation",
        description:
          "Review the existing layout, retained equipment, current operations, known constraints, available utilities, access, and intended changes before defining the renovation sequence.",
      },
    ],
    workflowEyebrow: "Kitchen workflow",
    workflowTitle: "Connect the main working areas into one coordinated flow.",
    workflowDescription:
      "The final arrangement depends on the menu, meal volume, service model, available space, and responsible project professionals. These areas provide a practical starting point for discussion.",
    workflowAreas: [
      {
        title: "Receiving and storage",
        description:
          "Review incoming goods, storage needs, access, and movement into preparation areas.",
      },
      {
        title: "Preparation",
        description:
          "Organize preparation activities around the menu, staffing, hygiene flow, and connection to cooking.",
      },
      {
        title: "Cooking and service",
        description:
          "Coordinate cooking requirements and the movement of prepared meals into the school service period.",
      },
      {
        title: "Return, washing, and cleaning",
        description:
          "Consider returns, washing flow, cleaning routines, drainage inputs, and service access around the approved plan.",
      },
    ],
    solutionEyebrow: "Relevant solution",
    solutionTitle: "Review the school canteen kitchen planning framework.",
    solutionDescription:
      "See the project inputs and coordinated delivery areas for a school canteen kitchen, from early operational planning through manufacturing coordination and local installation.",
    solutionLinkLabel: "Explore school canteen kitchen solutions",
    consultationEyebrow: "Engineering consultation",
    consultationTitle:
      "Discuss what your school kitchen needs to prepare, serve, and support.",
    consultationDescription:
      "The Public Consultation Agent can organize the facility, location, capacity, timeline, and contact details for human review. It does not provide pricing, delivery, or technical commitments.",
    consultationAgentLabel: "Start project consultation",
    consultationFormLabel: "Use consultation form",
  },
  "zh-CN": {
    path: "/industries/schools",
    metadataTitle: "印度尼西亚学校商用厨房解决方案",
    metadataDescription:
      "围绕机构餐食准备、工作流程、储存、烹饪、供餐和洗涤，规划印度尼西亚学校新建食堂厨房和改造项目。",
    breadcrumbLabel: "学校",
    eyebrow: "学校商用厨房解决方案 · 印度尼西亚",
    title: "围绕餐食、动线和每日运营规划学校厨房。",
    description:
      "Sari Arta 协助学校项目团队围绕集中供餐时段、机构餐食准备、学生动线、实际清洁需求和可用场地整理商用厨房需求。",
    needsEyebrow: "学校餐饮需求",
    needsTitle: "先明确运营需求，再确定设备清单。",
    needsDescription:
      "学校食堂规划从厨房服务对象、供餐时段、团队工作方式，以及各区域如何支持可重复的日常运营开始。",
    needs: [
      {
        title: "机构餐食准备",
        description:
          "明确预计餐数、菜单模式、准备方式、人员配置和决定日常需求的供餐时段。",
      },
      {
        title: "学生与员工动线",
        description:
          "考虑厨房工作、供餐、学生通行、餐具回收和清洁如何在现有场地内相互衔接。",
      },
      {
        title: "可维护的日常运营",
        description:
          "在项目讨论中纳入清洁流程、维护通道、操作指导、设备记录和交接需求。",
      },
    ],
    projectEyebrow: "项目起点",
    projectTitle: "支持学校新建厨房和食堂改造。",
    projectDescription:
      "工程讨论会根据项目现状调整。在确认详细范围前，应审核现有资料和限制条件。",
    projectTypes: [
      {
        title: "新建厨房项目",
        description:
          "与项目团队协调餐食需求、流程分区、设备范围、公用设施资料、进场条件、制造信息、场地准备、安装和交接。",
      },
      {
        title: "食堂改造",
        description:
          "在确定改造顺序前，审核现有布局、保留设备、当前运营、已知限制、公用设施、进场条件和预期变化。",
      },
    ],
    workflowEyebrow: "厨房工作流程",
    workflowTitle: "把主要工作区域连接成协调一致的流程。",
    workflowDescription:
      "最终布局取决于菜单、餐数、服务模式、可用空间和负责项目的专业人员。以下区域可作为讨论起点。",
    workflowAreas: [
      {
        title: "收货与储存",
        description: "审核货物进入、储存需求、通道和进入准备区域的动线。",
      },
      {
        title: "准备区域",
        description: "围绕菜单、人员、卫生动线和与烹饪区域的连接组织准备工作。",
      },
      {
        title: "烹饪与供餐",
        description: "协调烹饪需求以及餐食进入学校供餐时段的动线。",
      },
      {
        title: "回收、洗涤与清洁",
        description:
          "围绕已批准方案考虑餐具回收、洗涤流程、清洁、排水资料和维护通道。",
      },
    ],
    solutionEyebrow: "相关解决方案",
    solutionTitle: "查看学校食堂厨房规划框架。",
    solutionDescription:
      "了解学校食堂厨房的项目资料和协调交付范围，包括早期运营规划、制造协调和本地安装。",
    solutionLinkLabel: "查看学校食堂厨房解决方案",
    consultationEyebrow: "工程咨询",
    consultationTitle: "讨论学校厨房需要准备、供应和支持的内容。",
    consultationDescription:
      "公开咨询智能体可以整理设施、地点、产能、时间和联系方式供人工审核。它不会提供价格、交付或技术承诺。",
    consultationAgentLabel: "开始项目咨询",
    consultationFormLabel: "使用咨询表单",
  },
};
