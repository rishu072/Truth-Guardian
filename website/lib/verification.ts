/**
 * Client-side verification helpers.
 *
 * In production the Next.js API routes proxy to the Django backend so the
 * browser never talks to Django directly (avoids CORS / credential issues).
 *
 * The API routes defined under /app/api/* forward requests to the Django
 * backend and relay the response back to the client.
 */

interface VerificationResult {
  title: string;
  truth_score: number;
  verdict: string;
  reason: string;
  evidence_links: string[];
}

export async function verifyTextNews(content: string): Promise<VerificationResult> {
  try {
    const response = await fetch("/api/verify_text_news", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Text verification failed:", error);
    throw new Error(
      error instanceof Error ? error.message : "Failed to verify text content"
    );
  }
}

export async function verifyImageNews(
  file: File,
  claim: string
): Promise<VerificationResult> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("query", claim);

    const response = await fetch("/api/verify_image_news", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Image verification failed:", error);
    throw new Error(
      error instanceof Error ? error.message : "Failed to verify image content"
    );
  }
}

export async function verifySocialNews(
  url: string,
  claim: string,
  type: "text" | "image"
): Promise<VerificationResult> {
  try {
    const response = await fetch("/api/verify_social_news", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url, claim, type }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Social media verification failed:", error);
    throw new Error(
      error instanceof Error
        ? error.message
        : "Failed to verify social media content"
    );
  }
}