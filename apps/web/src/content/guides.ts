import {
  isPublishedPublicCaseStudy,
  publicCaseStudies,
} from "@/content/case-studies";
import type { Locale } from "@/i18n/config";
import {
  publishedPublicRoutes,
  type PublishedPublicRoute,
} from "@/lib/search-foundation";

export type GuideSection = {
  heading: string;
  paragraphs: readonly string[];
  points?: readonly string[];
};

export type GuideFaqItem = {
  question: string;
  answer: string;
};

export type GuideRelatedLink = {
  label: string;
  href:
    `/solutions/${string}` | `/industries/${string}` | `/projects/${string}`;
};

export type GuidePageContent = {
  metadataTitle: string;
  metadataDescription: string;
  breadcrumbLabel: string;
  eyebrow: string;
  title: string;
  summary: string;
  introduction: readonly string[];
  sections: readonly GuideSection[];
  faqItems: readonly GuideFaqItem[];
  relatedSolutions: readonly GuideRelatedLink[];
  relatedIndustries: readonly GuideRelatedLink[];
  relatedProjects: readonly GuideRelatedLink[];
  consultationLabel?: string;
  consultationDescription?: string;
};

export type GuideRecord = {
  slug: string;
  status: "draft" | "review" | "approved" | "published" | "archived";
  isPublic: boolean;
  publishedAt?: string;
  updatedAt?: string;
  publicationApproval?: {
    versionId: string;
    approvedAt: string;
    contentChecksum: string;
    factualContentApproved: boolean;
    publicUseApproved: boolean;
  };
  content: Partial<Record<Locale, GuidePageContent>>;
};

/**
 * Add a guide only after its exact bilingual version has been fact-checked and
 * approved for public use. The empty registry intentionally publishes nothing.
 */
export const publicGuides: readonly GuideRecord[] = [];

export function isPublishedPublicGuide(record: GuideRecord): boolean {
  const english = record.content.en;
  const chinese = record.content["zh-CN"];
  return Boolean(
    /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(record.slug) &&
    record.isPublic &&
    record.status === "published" &&
    record.publishedAt &&
    record.publicationApproval?.versionId &&
    record.publicationApproval.approvedAt &&
    record.publicationApproval.contentChecksum &&
    record.publicationApproval.factualContentApproved &&
    record.publicationApproval.publicUseApproved &&
    english &&
    chinese &&
    hasCompleteGuideContent(english) &&
    hasCompleteGuideContent(chinese) &&
    hasPublishedRelatedLinks(english) &&
    hasPublishedRelatedLinks(chinese),
  );
}

export function getPublishedGuide(
  slug: string,
  locale: Locale,
): { record: GuideRecord; content: GuidePageContent } | undefined {
  const record = publicGuides.find(
    (candidate) => candidate.slug === slug && isPublishedPublicGuide(candidate),
  );
  const content = record?.content[locale];
  return record && content ? { record, content } : undefined;
}

export function getPublishedGuideSlugs(): string[] {
  return publicGuides
    .filter(isPublishedPublicGuide)
    .map((record) => record.slug);
}

export function buildGuideSitemapRoutes(
  records: readonly GuideRecord[] = publicGuides,
): PublishedPublicRoute[] {
  return records.filter(isPublishedPublicGuide).map((record) => ({
    path: `/guides/${record.slug}`,
    status: "published",
    isPublic: true,
    lastModified: record.updatedAt
      ? new Date(record.updatedAt)
      : record.publishedAt
        ? new Date(record.publishedAt)
        : undefined,
    changeFrequency: "monthly",
    priority: 0.7,
  }));
}

function hasCompleteGuideContent(content: GuidePageContent): boolean {
  return Boolean(
    content.metadataTitle.trim() &&
    content.metadataDescription.trim() &&
    content.breadcrumbLabel.trim() &&
    content.title.trim() &&
    content.summary.trim() &&
    content.introduction.length > 0 &&
    content.introduction.every((paragraph) => paragraph.trim()) &&
    content.sections.length > 0 &&
    content.sections.every(
      (section) =>
        section.heading.trim() &&
        section.paragraphs.length > 0 &&
        section.paragraphs.every((paragraph) => paragraph.trim()) &&
        (section.points?.every((point) => point.trim()) ?? true),
    ) &&
    content.faqItems.every(
      (item) => item.question.trim() && item.answer.trim(),
    ) &&
    content.relatedSolutions.length > 0 &&
    content.relatedIndustries.length > 0,
  );
}

function hasPublishedRelatedLinks(content: GuidePageContent): boolean {
  return [
    ...content.relatedSolutions,
    ...content.relatedIndustries,
    ...content.relatedProjects,
  ].every((link) => isPublishedPublicLink(link.href));
}

function isPublishedPublicLink(href: GuideRelatedLink["href"]): boolean {
  if (href.startsWith("/projects/")) {
    const slug = href.slice("/projects/".length);
    return publicCaseStudies.some(
      (record) => record.slug === slug && isPublishedPublicCaseStudy(record),
    );
  }
  return publishedPublicRoutes.some((route) => route.path === href);
}

export const guideInterfaceCopy: Record<
  Locale,
  {
    introduction: string;
    faq: string;
    related: string;
    relatedSolutions: string;
    relatedIndustries: string;
    relatedProjects: string;
    consultationEyebrow: string;
    consultationTitle: string;
    consultationDescription: string;
    consultationLabel: string;
  }
> = {
  en: {
    introduction: "Introduction",
    faq: "Frequently asked questions",
    related: "Related planning resources",
    relatedSolutions: "Solutions",
    relatedIndustries: "Industries",
    relatedProjects: "Project cases",
    consultationEyebrow: "Project consultation",
    consultationTitle: "Turn planning questions into a project brief.",
    consultationDescription:
      "The Public Consultation Agent can organize your facility, location, capacity, timeline, and requirements for human review. It does not provide pricing, delivery, or technical commitments.",
    consultationLabel: "Start project consultation",
  },
  "zh-CN": {
    introduction: "引言",
    faq: "常见问题",
    related: "相关规划资料",
    relatedSolutions: "解决方案",
    relatedIndustries: "行业应用",
    relatedProjects: "项目案例",
    consultationEyebrow: "项目咨询",
    consultationTitle: "把规划问题整理为项目需求。",
    consultationDescription:
      "公开咨询智能体可以整理设施、地点、产能、时间和需求供人工审核，不会作出价格、交付或技术承诺。",
    consultationLabel: "开始项目咨询",
  },
};
