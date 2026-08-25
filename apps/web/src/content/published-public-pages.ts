import {
  getPublishedCaseStudy,
  type CaseStudyPageContent,
} from "@/content/case-studies";
import { getPublishedGuide, type GuidePageContent } from "@/content/guides";
import {
  schoolsIndustry,
  type IndustryPageContent,
} from "@/content/industry-pages";
import {
  schoolCanteenSolution,
  type SolutionPageContent,
} from "@/content/solution-pages";
import type { Locale } from "@/i18n/config";
import {
  getPublishedCmsPage,
  isGovernedUnavailable,
  type PublishedCmsPage,
  type PublishedMediaReference,
  type PublicPageType,
} from "@/lib/public-content";

type Section = { title: string; description: string };
type Related = { label: string; path: string };
type Cta = { label: string; description: string; destination: string };

type CmsSolution = {
  overview: string[];
  customer_needs: string[];
  service_scope: Section[];
  workflow_areas: Section[];
  related_industries: Related[];
  related_projects: Related[];
  cta: Cta;
};

type CmsIndustry = {
  overview: string[];
  business_needs: string[];
  relevant_solutions: Related[];
  project_considerations: Section[];
  related_projects: Related[];
  cta: Cta;
};

type CmsCaseStudy = {
  project_overview: string[];
  location: string;
  industry: string;
  project_type: string;
  project_requirements: string[];
  scope_of_work: Section[];
  functional_areas: Section[];
  delivery_approach: Section[];
  approved_project_facts: Array<{ label: string; value: string }>;
  gallery_references: PublishedMediaReference[];
  related_solution: Related | null;
  related_industry: Related | null;
  cta: Cta;
};

type CmsGuide = {
  introduction: string[];
  sections: Section[];
  faq_items: Array<{ question: string; answer: string }>;
  related_solutions: Related[];
  related_industries: Related[];
  related_projects: Related[];
  cta: Cta;
};

export type ResolvedPublicPage =
  | {
      source: "cms" | "legacy";
      pageType: "solution";
      path: string;
      content: SolutionPageContent;
    }
  | {
      source: "cms" | "legacy";
      pageType: "industry";
      path: string;
      content: IndustryPageContent;
    }
  | {
      source: "cms" | "legacy";
      pageType: "case_study";
      path: string;
      content: CaseStudyPageContent;
      publishedAt?: string;
      updatedAt?: string;
    }
  | {
      source: "cms" | "legacy";
      pageType: "guide";
      path: string;
      content: GuidePageContent;
      publishedAt?: string;
      updatedAt?: string;
    };

export type GovernedTemplatePageType = Exclude<PublicPageType, "product">;

export async function resolvePublishedPublicPage(
  pageType: GovernedTemplatePageType,
  slug: string,
  locale: Locale,
): Promise<ResolvedPublicPage | null> {
  const fallback = legacyFallback(pageType, slug, locale);
  try {
    const cms = await getPublishedCmsPage(pageType, slug, locale);
    if (isGovernedUnavailable(cms)) return null;
    return cms ? adaptCmsPage(cms, locale) : fallback;
  } catch (error) {
    if (fallback) return fallback;
    throw error;
  }
}

function adaptCmsPage(
  page: PublishedCmsPage,
  locale: Locale,
): ResolvedPublicPage {
  const copy = interfaceCopy[locale];
  if (page.page_type === "solution") {
    const content = page.structured_content as CmsSolution;
    return {
      source: "cms",
      pageType: "solution",
      path: page.canonical_path,
      content: {
        path: page.canonical_path,
        metadataTitle: page.seo_title,
        metadataDescription: page.seo_description,
        breadcrumbLabel: page.title,
        eyebrow: copy.solution,
        title: page.title,
        description: page.summary,
        overviewEyebrow: copy.overview,
        overviewTitle: copy.solutionOverview,
        overviewDescription: content.overview.join(" "),
        priorities: content.workflow_areas,
        scopeEyebrow: copy.scope,
        scopeTitle: copy.serviceScope,
        scopeDescription: page.summary,
        scopeItems: content.service_scope.map((item, index) => ({
          number: String(index + 1).padStart(2, "0"),
          ...item,
        })),
        inputsEyebrow: copy.customerNeeds,
        inputsTitle: copy.customerNeeds,
        inputsDescription: content.overview[0] ?? page.summary,
        inputs: content.customer_needs,
        deliveryEyebrow: copy.workflow,
        deliveryTitle: copy.workflowAreas,
        deliveryDescription:
          content.overview.slice(1).join(" ") || page.summary,
        consultationEyebrow: copy.consultation,
        consultationTitle: content.cta.label,
        consultationDescription: content.cta.description,
        consultationAgentLabel: content.cta.label,
        consultationFormLabel: copy.contactForm,
        relatedLinks: [
          ...content.related_industries,
          ...content.related_projects,
        ].map(link),
      },
    };
  }
  if (page.page_type === "industry") {
    const content = page.structured_content as CmsIndustry;
    const primarySolution = content.relevant_solutions[0];
    return {
      source: "cms",
      pageType: "industry",
      path: page.canonical_path,
      content: {
        path: page.canonical_path,
        metadataTitle: page.seo_title,
        metadataDescription: page.seo_description,
        breadcrumbLabel: page.title,
        eyebrow: copy.industry,
        title: page.title,
        description: page.summary,
        needsEyebrow: copy.businessNeeds,
        needsTitle: copy.businessNeeds,
        needsDescription: content.overview.join(" "),
        needs: content.business_needs.map((title) => ({ title })),
        projectEyebrow: copy.considerations,
        projectTitle: copy.projectConsiderations,
        projectDescription: content.overview[0] ?? page.summary,
        projectTypes: content.project_considerations,
        workflowEyebrow: copy.workflow,
        workflowTitle: copy.workflowAreas,
        workflowDescription: page.summary,
        workflowAreas: [],
        solutionEyebrow: copy.relatedSolution,
        solutionTitle: primarySolution?.label ?? "",
        solutionDescription: content.overview.at(-1) ?? page.summary,
        solutionLinkLabel: primarySolution?.label ?? "",
        solutionLinkHref: primarySolution?.path,
        consultationEyebrow: copy.consultation,
        consultationTitle: content.cta.label,
        consultationDescription: content.cta.description,
        consultationAgentLabel: content.cta.label,
        consultationFormLabel: copy.contactForm,
        consultationFormHref: `/contact?industry=${page.slug}`,
        relatedLinks: [
          ...content.relevant_solutions.slice(1),
          ...content.related_projects,
        ].map(link),
      },
    };
  }
  if (page.page_type === "case_study") {
    const content = page.structured_content as CmsCaseStudy;
    return {
      source: "cms",
      pageType: "case_study",
      path: page.canonical_path,
      content: {
        metadataTitle: page.seo_title,
        metadataDescription: page.seo_description,
        breadcrumbLabel: page.title,
        eyebrow: copy.caseStudy,
        title: page.title,
        summary: page.summary,
        projectType: content.project_type,
        location: content.location,
        industry: content.industry,
        projectRequirements: content.project_requirements,
        scopeOfWork: content.scope_of_work,
        kitchenAreas: content.functional_areas,
        deliveryApproach: content.delivery_approach,
        approvedProjectFacts: content.approved_project_facts,
        images: [...page.media_references, ...content.gallery_references]
          .filter((reference) =>
            ["hero", "project_gallery", "supporting"].includes(reference.role),
          )
          .filter(
            (reference, index, all) =>
              all.findIndex(
                (candidate) =>
                  candidate.media_asset_id === reference.media_asset_id,
              ) === index,
          )
          .map(publicImage),
        relatedSolution: content.related_solution
          ? caseRelated(content.related_solution)
          : undefined,
        relatedIndustry: content.related_industry
          ? caseRelated(content.related_industry)
          : undefined,
        consultationLabel: content.cta.label,
        consultationDescription: content.cta.description,
      },
      publishedAt: page.published_at,
      updatedAt: page.version_created_at,
    };
  }
  const content = page.structured_content as CmsGuide;
  return {
    source: "cms",
    pageType: "guide",
    path: page.canonical_path,
    content: {
      metadataTitle: page.seo_title,
      metadataDescription: page.seo_description,
      breadcrumbLabel: page.title,
      eyebrow: copy.guide,
      title: page.title,
      summary: page.summary,
      introduction: content.introduction,
      sections: content.sections.map((section) => ({
        heading: section.title,
        paragraphs: [section.description],
      })),
      faqItems: content.faq_items,
      relatedSolutions: content.related_solutions.map(guideLink),
      relatedIndustries: content.related_industries.map(guideLink),
      relatedProjects: content.related_projects.map(guideLink),
      consultationLabel: content.cta.label,
      consultationDescription: content.cta.description,
    },
    publishedAt: page.published_at,
    updatedAt: page.version_created_at,
  };
}

function legacyFallback(
  pageType: GovernedTemplatePageType,
  slug: string,
  locale: Locale,
): ResolvedPublicPage | null {
  if (pageType === "solution" && slug === "school-canteen-kitchen") {
    return {
      source: "legacy",
      pageType,
      path: `/solutions/${slug}`,
      content: schoolCanteenSolution[locale],
    };
  }
  if (pageType === "industry" && slug === "schools") {
    return {
      source: "legacy",
      pageType,
      path: `/industries/${slug}`,
      content: schoolsIndustry[locale],
    };
  }
  if (pageType === "case_study") {
    const page = getPublishedCaseStudy(slug, locale);
    return page
      ? {
          source: "legacy",
          pageType,
          path: `/projects/${slug}`,
          content: page.content,
          publishedAt: page.record.publishedAt,
          updatedAt: page.record.updatedAt,
        }
      : null;
  }
  if (pageType === "guide") {
    const page = getPublishedGuide(slug, locale);
    return page
      ? {
          source: "legacy",
          pageType,
          path: `/guides/${slug}`,
          content: page.content,
          publishedAt: page.record.publishedAt,
          updatedAt: page.record.updatedAt,
        }
      : null;
  }
  return null;
}

function link(value: Related) {
  return { label: value.label, href: value.path };
}

function guideLink(value: Related) {
  return {
    label: value.label,
    href: value.path as
      `/solutions/${string}` | `/industries/${string}` | `/projects/${string}`,
  };
}

function caseRelated(value: Related) {
  return {
    label: value.label,
    href: value.path as `/solutions/${string}` | `/industries/${string}`,
  };
}

function publicImage(reference: PublishedMediaReference) {
  return {
    src: `/public-media/${reference.media_asset_id}`,
    alt: reference.alt_text,
    width: reference.width,
    height: reference.height,
    caption: reference.caption ?? undefined,
  };
}

const interfaceCopy = {
  en: {
    solution: "Commercial kitchen solution",
    industry: "Industry solution",
    caseStudy: "Approved project case study",
    guide: "Commercial kitchen planning guide",
    overview: "Overview",
    solutionOverview: "Solution overview",
    scope: "Scope",
    serviceScope: "Service scope",
    customerNeeds: "Customer needs",
    businessNeeds: "Business needs",
    considerations: "Planning",
    projectConsiderations: "Project considerations",
    workflow: "Workflow",
    workflowAreas: "Workflow and functional areas",
    relatedSolution: "Related solution",
    consultation: "Project consultation",
    contactForm: "Use consultation form",
  },
  "zh-CN": {
    solution: "商用厨房解决方案",
    industry: "行业解决方案",
    caseStudy: "已批准项目案例",
    guide: "商用厨房规划指南",
    overview: "概览",
    solutionOverview: "解决方案概览",
    scope: "服务范围",
    serviceScope: "服务范围",
    customerNeeds: "客户需求",
    businessNeeds: "业务需求",
    considerations: "项目规划",
    projectConsiderations: "项目注意事项",
    workflow: "工作流程",
    workflowAreas: "工作流程与功能区域",
    relatedSolution: "相关解决方案",
    consultation: "项目咨询",
    contactForm: "使用咨询表单",
  },
} satisfies Record<Locale, Record<string, string>>;
