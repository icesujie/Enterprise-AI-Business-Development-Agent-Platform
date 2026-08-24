import type { Locale } from "./config";

export type Messages = {
  language: { english: string; chinese: string; label: string };
  public: {
    navigation: string;
    solutions: string;
    industries: string;
    projects: string;
    about: string;
    contact: string;
    consultation: string;
    menu: string;
    openNavigation: string;
    skip: string;
    kitchenEngineering: string;
    explore: string;
    company: string;
    projectInquiry: string;
    staffAccess: string;
    footerDescription: string;
    copyright: string;
    hero: {
      eyebrow: string;
      title: string;
      description: string;
      delivery: string;
      engineering: string;
      manufacturing: string;
      installation: string;
      visualLabel: string;
      workflow: string;
      qualityGate: string;
    };
    consultationBand: {
      eyebrow: string;
      title: string;
      description: string;
    };
  };
  workspace: {
    workspace: string;
    internal: string;
    dashboard: string;
    leads: string;
    opportunities: string;
    followUp: string;
    agentPlayground: string;
    knowledge: string;
    marketingContent: string;
    publicContent: string;
    records: string;
    companies: string;
    contacts: string;
    publicWebsite: string;
    navigation: string;
    mobileNavigation: string;
    signedInUser: string;
    signOut: string;
    skip: string;
  };
  login: {
    title: string;
    description: string;
    demoAccount: string;
    email: string;
    password: string;
    signIn: string;
    unavailable: string;
    failed: string;
  };
};

const en: Messages = {
  language: { english: "English", chinese: "中文", label: "Language" },
  public: {
    navigation: "Public navigation",
    solutions: "Solutions",
    industries: "Industries",
    projects: "Projects",
    about: "About Us",
    contact: "Contact",
    consultation: "Request kitchen consultation",
    menu: "Menu",
    openNavigation: "Open navigation",
    skip: "Skip to content",
    kitchenEngineering: "Kitchen Engineering",
    explore: "Explore",
    company: "Company",
    projectInquiry: "Project inquiry",
    staffAccess: "Staff access",
    footerDescription:
      "Commercial kitchen design, manufacturing coordination, and local project delivery for institutional and industrial operations in Indonesia.",
    copyright: "© 2026 Sari Arta. All project scopes remain subject to review.",
    hero: {
      eyebrow: "Indonesia Commercial Kitchen Engineering Partner",
      title: "Commercial kitchens engineered for real operating demands.",
      description:
        "Sari Arta brings together commercial kitchen design, China-based manufacturing capability, and local Indonesia installation to help institutional and industrial projects move from requirement to operation.",
      delivery: "See how we deliver",
      engineering: "Kitchen engineering",
      manufacturing: "China manufacturing",
      installation: "Indonesia installation",
      visualLabel: "Abstract commercial kitchen workflow plan",
      workflow: "Workflow planning",
      qualityGate: "Quality gate 03",
    },
    consultationBand: {
      eyebrow: "Start with what you know",
      title: "Planning a commercial kitchen project in Indonesia?",
      description:
        "Share your facility type, location, approximate size or meal volume, target date, and known requirements. Early-stage briefs are welcome and every inquiry is reviewed by a person.",
    },
  },
  workspace: {
    workspace: "Workspace",
    internal: "Internal workspace",
    dashboard: "Dashboard",
    leads: "Leads",
    opportunities: "Opportunities",
    followUp: "Follow-up",
    agentPlayground: "Agent Playground",
    knowledge: "Knowledge",
    marketingContent: "Marketing Content",
    publicContent: "Public Content",
    records: "Records",
    companies: "Companies",
    contacts: "Contacts",
    publicWebsite: "Public website",
    navigation: "Workspace navigation",
    mobileNavigation: "Mobile workspace navigation",
    signedInUser: "Signed in user",
    signOut: "Sign out",
    skip: "Skip to workspace content",
  },
  login: {
    title: "Sales workspace",
    description: "Sign in with your authorized business account.",
    demoAccount: "Local demo account",
    email: "Email",
    password: "Password",
    signIn: "Sign in",
    unavailable: "Authentication is not configured for this environment.",
    failed: "Sign-in failed. Check the email and password and try again.",
  },
};

const zh: Messages = {
  language: { english: "English", chinese: "中文", label: "语言" },
  public: {
    navigation: "网站导航",
    solutions: "解决方案",
    industries: "行业应用",
    projects: "项目案例",
    about: "关于我们",
    contact: "联系我们",
    consultation: "申请厨房项目咨询",
    menu: "菜单",
    openNavigation: "打开导航",
    skip: "跳到主要内容",
    kitchenEngineering: "商用厨房工程",
    explore: "浏览",
    company: "公司",
    projectInquiry: "项目咨询",
    staffAccess: "员工入口",
    footerDescription:
      "面向印度尼西亚学校、医院、工厂和企业餐厅，提供商用厨房设计、制造协调、本地安装与项目交付服务。",
    copyright: "© 2026 Sari Arta。所有项目范围均需经过正式确认。",
    hero: {
      eyebrow: "印度尼西亚商用厨房工程合作伙伴",
      title: "为真实运营需求打造商用厨房。",
      description:
        "Sari Arta 将商用厨房设计、中国制造能力与印度尼西亚本地安装结合起来，帮助学校、医院、工厂及中央厨房项目从需求规划走向正式运营。",
      delivery: "了解我们的交付方式",
      engineering: "厨房工程设计",
      manufacturing: "中国制造协调",
      installation: "印尼本地安装",
      visualLabel: "商用厨房工作流程示意图",
      workflow: "流程规划",
      qualityGate: "质量检查点 03",
    },
    consultationBand: {
      eyebrow: "从已有信息开始",
      title: "正在印度尼西亚规划商用厨房项目？",
      description:
        "请告诉我们项目类型、地点、厨房面积或供餐量、目标日期及已知需求。早期项目同样欢迎咨询，每一条询盘都会由业务人员审核。",
    },
  },
  workspace: {
    workspace: "工作台",
    internal: "内部业务系统",
    dashboard: "仪表盘",
    leads: "销售线索",
    opportunities: "项目商机",
    followUp: "跟进管理",
    agentPlayground: "智能体演示",
    knowledge: "知识管理",
    marketingContent: "营销内容",
    publicContent: "公开内容",
    records: "基础资料",
    companies: "客户公司",
    contacts: "联系人",
    publicWebsite: "公开网站",
    navigation: "工作台导航",
    mobileNavigation: "移动端工作台导航",
    signedInUser: "当前登录用户",
    signOut: "退出登录",
    skip: "跳到工作台内容",
  },
  login: {
    title: "销售工作台",
    description: "请使用已授权的业务账号登录。",
    demoAccount: "本地演示账号",
    email: "邮箱",
    password: "密码",
    signIn: "登录",
    unavailable: "当前环境尚未配置身份认证。",
    failed: "登录失败，请检查邮箱和密码后重试。",
  },
};

export function messagesFor(locale: Locale): Messages {
  return locale === "zh-CN" ? zh : en;
}
