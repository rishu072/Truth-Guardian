import { NextResponse } from "next/server";

/**
 * POST /api/verify_social_news
 *
 * Proxies social media verification requests to the Django backend.
 */

const DJANGO_API_BASE = process.env.DJANGO_API_BASE || "http://localhost:8000";

const ALLOWED_ORIGINS = [
  process.env.EXTENSION!,
  process.env.BROWSER!,
].filter(Boolean);

export async function POST(request: Request) {
  try {
    const origin = request.headers.get("origin");

    if (ALLOWED_ORIGINS.length > 0 && origin && !ALLOWED_ORIGINS.includes(origin)) {
      return NextResponse.json({ error: "Unauthorized access" }, { status: 403 });
    }

    const { url, claim = "Verify the claim and check if it is true.", type = "text" } =
      await request.json();

    if (!url) {
      return NextResponse.json({ error: "URL is required" }, { status: 400 });
    }

    const djangoResponse = await fetch(`${DJANGO_API_BASE}/api/detect/social/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, claim }),
    });

    const result = await djangoResponse.json();

    if (!djangoResponse.ok) {
      return NextResponse.json(result, { status: djangoResponse.status });
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error proxying social verification:", error);
    return NextResponse.json(
      { error: "Failed to process social media verification request" },
      { status: 500 }
    );
  }
}