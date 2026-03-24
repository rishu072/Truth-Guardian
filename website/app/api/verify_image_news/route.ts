import { NextResponse } from "next/server";

/**
 * POST /api/verify_image_news
 *
 * Proxies image verification requests to the Django backend.
 * Forwards the multipart form data (file + query) as-is.
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

    const formData = await request.formData();
    const file = formData.get("file") as File;
    const query = formData.get("query") as string || formData.get("claim") as string;

    if (!file) {
      return NextResponse.json({ error: "Image file is required" }, { status: 400 });
    }

    // Build new FormData for Django
    const djangoFormData = new FormData();
    djangoFormData.append("file", file, file.name);
    if (query) {
      djangoFormData.append("query", query);
    }

    const djangoResponse = await fetch(`${DJANGO_API_BASE}/api/detect/image/`, {
      method: "POST",
      body: djangoFormData,
    });

    const result = await djangoResponse.json();

    if (!djangoResponse.ok) {
      return NextResponse.json(result, { status: djangoResponse.status });
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error proxying image verification:", error);
    return NextResponse.json(
      { error: "Failed to process image verification request" },
      { status: 500 }
    );
  }
}
