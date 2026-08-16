import type { Metadata } from "next";

import type { Locale } from "@/i18n/config";
import {
  absolutePublicUrl,
  getSiteUrl,
  siteIdentity,
} from "@/lib/search-foundation";

export type PublicPageKey =
  | "home"
  | "solutions"
  | "industries"
  | "projects"
  | "about"
  | "contact";

const publicMetadata: Record<
  PublicPageKey,
  Record<Locale, { title: string; description: string; path: string }>
> = {
  home: {
    en: {
      title: "Commercial Kitchen Engineering Indonesia",
      description:
        "Sari Arta coordinates commercial kitchen design, China-based manufacturing capability, logistics, local installation, and commissioning for projects in Indonesia.",
      path: "/",
    },
    "zh-CN": {
      title: "印度尼西亚商用厨房工程",
      description:
        "Sari Arta 为印度尼西亚项目协调商用厨房设计、中国制造能力、物流、本地安装和调试交付。",
      path: "/",
    },
  },
  solutions: {
    en: {
      title: "Commercial Kitchen Design & Project Delivery",
      description:
        "Explore Sari Arta commercial kitchen design, manufacturing coordination, logistics, installation, commissioning, and after-sales support in Indonesia.",
      path: "/solutions",
    },
    "zh-CN": {
      title: "商用厨房设计与项目交付",
      description:
        "了解 Sari Arta 在印度尼西亚提供的商用厨房设计、制造协调、物流、安装、调试和售后支持。",
      path: "/solutions",
    },
  },
  industries: {
    en: {
      title: "School, Hospital & Central Kitchen Solutions",
      description:
        "Commercial kitchen engineering for schools, hospitals, factories, corporate cafeterias, and central kitchens in Indonesia.",
      path: "/industries",
    },
    "zh-CN": {
      title: "学校、医院与中央厨房解决方案",
      description:
        "面向印度尼西亚学校、医院、工厂、企业食堂和中央厨房的商用厨房工程服务。",
      path: "/industries",
    },
  },
  projects: {
    en: {
      title: "Commercial Kitchen Project Scenarios",
      description:
        "Explore clearly labelled sample scenarios showing Sari Arta's approach to school, hospital, factory cafeteria, and central kitchen engineering projects.",
      path: "/projects",
    },
    "zh-CN": {
      title: "商用厨房项目示例",
      description:
        "查看明确标记为演示内容的学校、医院、工厂食堂和中央厨房工程项目场景。",
      path: "/projects",
    },
  },
  about: {
    en: {
      title: "About Sari Arta",
      description:
        "Learn how Sari Arta coordinates commercial kitchen engineering, China-based manufacturing capability, and local installation in Indonesia.",
      path: "/about",
    },
    "zh-CN": {
      title: "关于 Sari Arta",
      description:
        "了解 Sari Arta 如何协调商用厨房工程、中国制造能力和印度尼西亚本地安装。",
      path: "/about",
    },
  },
  contact: {
    en: {
      title: "Request a Commercial Kitchen Consultation",
      description:
        "Share your commercial kitchen project location, facility type, estimated size, timeline, and requirements with Sari Arta.",
      path: "/contact",
    },
    "zh-CN": {
      title: "申请商用厨房项目咨询",
      description:
        "向 Sari Arta 提供商用厨房项目地点、设施类型、预计规模、时间计划和需求。",
      path: "/contact",
    },
  },
};

export function buildRootMetadata(locale: Locale): Metadata {
  const description = publicMetadata.home[locale].description;
  return {
    metadataBase: new URL(getSiteUrl()),
    applicationName: siteIdentity.name,
    title: {
      default: siteIdentity.defaultTitle,
      template: "%s | Sari Arta",
    },
    description,
    category: "Commercial kitchen engineering",
    openGraph: {
      type: "website",
      siteName: siteIdentity.name,
      title: siteIdentity.defaultTitle,
      description,
      locale: locale === "zh-CN" ? "zh_CN" : "en_US",
      images: [socialImage()],
    },
    twitter: {
      card: "summary_large_image",
      title: siteIdentity.defaultTitle,
      description,
      images: ["/sari-arta-social-card.png"],
    },
    verification: buildVerificationMetadata(),
  };
}

export function buildPublicPageMetadata(
  page: PublicPageKey,
  locale: Locale,
): Metadata {
  const content = publicMetadata[page][locale];
  const canonical = absolutePublicUrl(content.path);
  return {
    title: content.title,
    description: content.description,
    alternates: { canonical },
    robots: {
      index: true,
      follow: true,
      googleBot: { index: true, follow: true },
    },
    openGraph: {
      type: "website",
      siteName: siteIdentity.name,
      title: `${content.title} | Sari Arta`,
      description: content.description,
      url: canonical,
      locale: locale === "zh-CN" ? "zh_CN" : "en_US",
      images: [socialImage()],
    },
    twitter: {
      card: "summary_large_image",
      title: `${content.title} | Sari Arta`,
      description: content.description,
      images: ["/sari-arta-social-card.png"],
    },
    other: { "content-language": locale },
  };
}

export const privateMetadata: Metadata = {
  robots: {
    index: false,
    follow: false,
    noarchive: true,
    nosnippet: true,
    googleBot: {
      index: false,
      follow: false,
      noarchive: true,
      nosnippet: true,
      noimageindex: true,
    },
  },
};

function socialImage() {
  return {
    url: "/sari-arta-social-card.png",
    width: 1730,
    height: 909,
    alt: "Sari Arta commercial kitchen engineering and delivery model",
  };
}

function buildVerificationMetadata(): Metadata["verification"] {
  const google = process.env.GOOGLE_SITE_VERIFICATION?.trim();
  const bing = process.env.BING_SITE_VERIFICATION?.trim();
  if (!google && !bing) return undefined;
  return {
    google: google || undefined,
    other: bing ? { "msvalidate.01": bing } : undefined,
  };
}
