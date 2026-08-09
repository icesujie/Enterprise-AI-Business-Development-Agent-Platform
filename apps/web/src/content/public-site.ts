export const capabilities = [
  {
    number: "01",
    title: "Kitchen design and engineering",
    shortTitle: "Design",
    description:
      "Translate menu, meal volume, staffing, hygiene flow, utilities, and space constraints into a coordinated commercial kitchen plan.",
    deliverables: [
      "Operational workflow and zone planning",
      "Capacity-led equipment requirements",
      "Utility and site coordination inputs",
    ],
  },
  {
    number: "02",
    title: "Equipment and manufacturing coordination",
    shortTitle: "Manufacturing",
    description:
      "Connect the approved equipment scope with China-based manufacturing capability, technical review, and defined quality checkpoints.",
    deliverables: [
      "Equipment scope coordination",
      "Technical specification review",
      "Pre-shipment quality checkpoints",
    ],
  },
  {
    number: "03",
    title: "Logistics and site readiness",
    shortTitle: "Logistics",
    description:
      "Align manufacturing release, shipping information, access planning, utilities, and installation readiness before equipment reaches the site.",
    deliverables: [
      "Delivery sequence planning",
      "Site-readiness coordination",
      "Project interface tracking",
    ],
  },
  {
    number: "04",
    title: "Local installation and commissioning",
    shortTitle: "Installation",
    description:
      "Coordinate Indonesia-based placement, connection checks, testing, handover, and operator familiarisation around the approved project scope.",
    deliverables: [
      "Installation coordination",
      "Testing and commissioning records",
      "Operational handover support",
    ],
  },
  {
    number: "05",
    title: "After-sales support coordination",
    shortTitle: "After-sales",
    description:
      "Keep equipment records, operating guidance, and service coordination connected after project handover.",
    deliverables: [
      "Handover information",
      "Maintenance planning inputs",
      "Service issue coordination",
    ],
  },
] as const;

export const industries = [
  {
    slug: "schools",
    number: "01",
    title: "School kitchens",
    description:
      "Plan safe, maintainable production and serving flow around concentrated meal periods, student movement, and repeatable daily routines.",
    priorities: [
      "Meal volume and service-window planning",
      "Clear receiving-to-washing workflow",
      "Safe operation and maintainability",
    ],
  },
  {
    slug: "hospitals",
    number: "02",
    title: "Hospital kitchen solutions",
    description:
      "Structure production, separation, distribution, washing, and cleaning workflows for reliable institutional food service.",
    priorities: [
      "Production and hygiene-zone separation",
      "Diet and meal-distribution workflow",
      "Reliability, cleaning, and service access",
    ],
  },
  {
    slug: "factories",
    number: "03",
    title: "Factory and corporate cafeterias",
    description:
      "Engineer bulk preparation and fast service around shift peaks, staff circulation, durability, and future operating changes.",
    priorities: [
      "Peak-shift throughput",
      "Bulk preparation and serving flow",
      "Durability and maintenance access",
    ],
  },
  {
    slug: "central-kitchens",
    number: "04",
    title: "Central kitchens",
    description:
      "Coordinate high-volume production from receiving and storage through cooking, holding, packing, and dispatch.",
    priorities: [
      "High-volume production flow",
      "Repeatability and dispatch coordination",
      "Utilities, logistics, and expansion planning",
    ],
  },
] as const;

export const sampleProjects = [
  {
    sector: "Education",
    location: "Greater Jakarta, Indonesia",
    title: "1,200-meal school kitchen planning scenario",
    challenge:
      "Serve concentrated lunch periods while keeping receiving, preparation, cooking, service, and washing movement clear.",
    scope:
      "Illustrative workflow study, equipment zoning, manufacturing coordination, and local installation sequence.",
  },
  {
    sector: "Healthcare",
    location: "Java, Indonesia",
    title: "Hospital nutrition kitchen upgrade scenario",
    challenge:
      "Plan a phased upgrade around production separation, meal distribution, cleaning flow, and continued operations.",
    scope:
      "Illustrative engineering review, phasing inputs, equipment coordination, installation, and commissioning plan.",
  },
  {
    sector: "Industrial dining",
    location: "West Java, Indonesia",
    title: "Two-shift factory cafeteria scenario",
    challenge:
      "Prepare and serve high meal volumes within short shift-change windows while supporting practical cleaning and maintenance.",
    scope:
      "Illustrative capacity plan, bulk-production zones, service-line coordination, logistics, and local site delivery.",
  },
] as const;

export const deliveryStages = [
  {
    number: "01",
    title: "Discover",
    description:
      "Clarify facility type, menu, meal volume, service windows, site constraints, timeline, and decision stakeholders.",
  },
  {
    number: "02",
    title: "Engineer",
    description:
      "Develop workflow zones, capacity requirements, equipment scope, and coordination inputs for the wider project team.",
  },
  {
    number: "03",
    title: "Coordinate manufacturing",
    description:
      "Align the approved design with equipment sourcing, technical review, manufacturing information, and quality gates.",
  },
  {
    number: "04",
    title: "Prepare delivery",
    description:
      "Coordinate shipping information, access, utilities, site readiness, sequencing, and installation responsibilities.",
  },
  {
    number: "05",
    title: "Install and commission",
    description:
      "Place, check, test, hand over, and support operator familiarisation for the approved scope in Indonesia.",
  },
] as const;
