import { NextResponse } from "next/server";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      id,
    )
  )
    return new NextResponse(null, { status: 404 });
  const upstream = await fetch(`${apiBaseUrl}/api/v1/media/public/${id}`, {
    next: { revalidate: 30, tags: [`public-media:${id}`] },
  });
  if (!upstream.ok)
    return new NextResponse(null, {
      status: upstream.status === 422 ? 404 : upstream.status,
    });
  return new NextResponse(upstream.body, {
    headers: {
      "Cache-Control":
        upstream.headers.get("cache-control") ??
        "public, max-age=30, must-revalidate",
      "Content-Type":
        upstream.headers.get("content-type") ?? "application/octet-stream",
      ETag: upstream.headers.get("etag") ?? "",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
