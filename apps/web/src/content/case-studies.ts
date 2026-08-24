import type { Locale } from "@/i18n/config";
import type { PublishedPublicRoute } from "@/lib/search-foundation";

export type CaseStudyImage = {
  src: string;
  alt: string;
  width: number;
  height: number;
  caption?: string;
};

export type CaseStudyFact = {
  label: string;
  value: string;
};

export type CaseStudySectionItem = {
  title: string;
  description: string;
};

export type CaseStudyRelatedLink = {
  label: string;
  href: `/solutions/${string}` | `/industries/${string}`;
};

export type CaseStudyPageContent = {
  metadataTitle: string;
  metadataDescription: string;
  breadcrumbLabel: string;
  eyebrow: string;
  title: string;
  summary: string;
  projectType: string;
  location: string;
  industry: string;
  projectRequirements: readonly string[];
  scopeOfWork: readonly CaseStudySectionItem[];
  kitchenAreas: readonly CaseStudySectionItem[];
  deliveryApproach: readonly CaseStudySectionItem[];
  approvedProjectFacts: readonly CaseStudyFact[];
  images: readonly CaseStudyImage[];
  relatedSolution?: CaseStudyRelatedLink;
  relatedIndustry?: CaseStudyRelatedLink;
  consultationLabel?: string;
  consultationDescription?: string;
};

export type CaseStudyRecord = {
  slug: string;
  status: "draft" | "review" | "approved" | "published" | "archived";
  isPublic: boolean;
  publishedAt?: string;
  updatedAt?: string;
  publicationApproval?: {
    versionId: string;
    approvedAt: string;
    contentChecksum: string;
    factsApproved: boolean;
    imagesApproved: boolean;
    publicUseApproved: boolean;
  };
  content: Partial<Record<Locale, CaseStudyPageContent>>;
};

/**
 * Public case studies belong here only after their facts, images, permissions,
 * English content, and Chinese content have all been approved for publication.
 * The empty registry is intentional: demo scenarios on /projects are not cases.
 */
export const publicCaseStudies: readonly CaseStudyRecord[] = [];

export function isPublishedPublicCaseStudy(record: CaseStudyRecord): boolean {
  return Boolean(
    record.isPublic &&
    record.status === "published" &&
    record.publishedAt &&
    record.publicationApproval?.versionId &&
    record.publicationApproval.approvedAt &&
    record.publicationApproval.contentChecksum &&
    record.publicationApproval?.factsApproved &&
    record.publicationApproval.imagesApproved &&
    record.publicationApproval.publicUseApproved &&
    record.content.en &&
    record.content["zh-CN"],
  );
}

export function getPublishedCaseStudy(
  slug: string,
  locale: Locale,
): { record: CaseStudyRecord; content: CaseStudyPageContent } | undefined {
  const record = publicCaseStudies.find(
    (candidate) =>
      candidate.slug === slug && isPublishedPublicCaseStudy(candidate),
  );
  const content = record?.content[locale];
  return record && content ? { record, content } : undefined;
}

export function getPublishedCaseStudySlugs(): string[] {
  return publicCaseStudies
    .filter(isPublishedPublicCaseStudy)
    .map((record) => record.slug);
}

export function buildCaseStudySitemapRoutes(
  records: readonly CaseStudyRecord[] = publicCaseStudies,
): PublishedPublicRoute[] {
  return records.filter(isPublishedPublicCaseStudy).map((record) => ({
    path: `/projects/${record.slug}`,
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

export const caseStudyInterfaceCopy: Record<
  Locale,
  {
    overview: string;
    requirements: string;
    scope: string;
    kitchenAreas: string;
    deliveryApproach: string;
    approvedFacts: string;
    gallery: string;
    related: string;
    relatedDescription: string;
    consultationEyebrow: string;
    consultationTitle: string;
    consultationDescription: string;
    consultationLabel: string;
  }
> = {
  en: {
    overview: "Project overview",
    requirements: "Project requirements",
    scope: "Scope of work",
    kitchenAreas: "Kitchen areas",
    deliveryApproach: "Solution and delivery approach",
    approvedFacts: "Approved project facts",
    gallery: "Project gallery",
    related: "Related planning resources",
    relatedDescription:
      "Continue with the relevant solution framework or industry context.",
    consultationEyebrow: "Project consultation",
    consultationTitle: "Discuss a commercial kitchen project with Sari Arta.",
    consultationDescription:
      "Share your facility, location, capacity, timeline, and project requirements for human review. No pricing, delivery, or technical commitment is made in the public assistant.",
    consultationLabel: "Start project consultation",
  },
  "zh-CN": {
    overview: "项目概况",
    requirements: "项目需求",
    scope: "工作范围",
    kitchenAreas: "厨房区域",
    deliveryApproach: "方案与交付方式",
    approvedFacts: "已批准的项目事实",
    gallery: "项目图片",
    related: "相关规划资料",
    relatedDescription: "继续查看相关解决方案框架或行业应用信息。",
    consultationEyebrow: "项目咨询",
    consultationTitle: "与 Sari Arta 讨论商用厨房项目。",
    consultationDescription:
      "提交设施、地点、产能、时间和项目需求供人工审核。公开咨询智能体不会作出价格、交付或技术承诺。",
    consultationLabel: "开始项目咨询",
  },
};
