import { NextResponse } from "next/server";

/**
 * POST /api/verify_text_news
 *
 * Proxies text verification requests to the Django backend.
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

    const { content } = await request.json();

    if (!content) {
      return NextResponse.json({ error: "Content is required" }, { status: 400 });
    }

    const djangoResponse = await fetch(`${DJANGO_API_BASE}/api/detect/text/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });

    const result = await djangoResponse.json();

    if (!djangoResponse.ok) {
      return NextResponse.json(
        result,
        { status: djangoResponse.status }
      );
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error proxying text verification:", error);
    return NextResponse.json(
      { error: "Failed to process text verification request" },
      { status: 500 }
    );
  }
}