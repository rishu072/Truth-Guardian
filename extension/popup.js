/**
 * Truth Guardian — Extension Popup Logic
 *
 * Connects to the Django REST API at API_BASE (defined in config.js).
 */

// ── Tab switching ───────────────────────────────────────────────────────────────

document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const selectedTab = btn.dataset.tab;
    document.querySelectorAll(".tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.tab === selectedTab);
    });
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    // Hide previous result when switching tabs
    document.getElementById("result").classList.add("hidden");
  });
});

// ── File name display ───────────────────────────────────────────────────────────

document.getElementById("imageFile").addEventListener("change", (e) => {
  const name = e.target.files.length > 0 ? e.target.files[0].name : "No file chosen";
  document.getElementById("fileName").textContent = name;
});

// ── Helpers ─────────────────────────────────────────────────────────────────────

function showResult(html) {
  const resultDiv = document.getElementById("result");
  resultDiv.classList.remove("hidden");
  resultDiv.innerHTML = html;
}

function showLoading() {
  showResult('<span class="loading-spinner"></span> Analysing with AI…');
}

function buildResultHTML(data) {
  if (data.error && !data.verdict) {
    return `<span style="color:#ef4444;">❌ ${data.error}</span>`;
  }

  const score = Math.round(data.truth_score || 0);
  let badgeClass, barClass, icon;

  if (score >= 70) {
    badgeClass = "badge-green";
    barClass = "bar-green";
    icon = "✅";
  } else if (score >= 40) {
    badgeClass = "badge-yellow";
    barClass = "bar-yellow";
    icon = "⚠️";
  } else {
    badgeClass = "badge-red";
    barClass = "bar-red";
    icon = "🚨";
  }

  let html = `
    <div class="verdict-badge ${badgeClass}">${icon} ${data.verdict || "Unknown"}</div>
    <p><strong>Truth Score:</strong></p>
    <div class="truth-score-bar-container">
      <div class="truth-score-bar ${barClass}" style="width: ${score}%;">
        ${score}%
      </div>
    </div>
    <p><strong>Reason:</strong> ${data.reason || "No explanation provided."}</p>
  `;

  const links = data.evidence_links || [];
  if (links.length > 0) {
    html += `<p style="margin-top:8px;"><strong>Evidence:</strong></p><ul class="evidence-list">`;
    links.forEach((link) => {
      html += `<li><a href="${link}" target="_blank" rel="noopener noreferrer">🔗 ${link}</a></li>`;
    });
    html += `</ul>`;
  }

  return html;
}

// ── Grab selected text from the active tab ──────────────────────────────────────

document.getElementById("grabSelectedBtn").addEventListener("click", async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.id) return;

    chrome.tabs.sendMessage(tab.id, { action: "getSelectedText" }, (response) => {
      if (chrome.runtime.lastError) {
        // Content script not injected — try scripting API
        chrome.scripting.executeScript(
          {
            target: { tabId: tab.id },
            func: () => window.getSelection().toString().trim(),
          },
          (results) => {
            const text = results?.[0]?.result || "";
            if (text) {
              document.getElementById("textInput").value = text;
            } else {
              showResult('<span style="color:#eab308;">⚠️ No text selected on the page.</span>');
            }
          }
        );
        return;
      }
      if (response && response.text) {
        document.getElementById("textInput").value = response.text;
      } else {
        showResult('<span style="color:#eab308;">⚠️ No text selected on the page.</span>');
      }
    });
  } catch (err) {
    console.error(err);
  }
});

// ── Text verification ───────────────────────────────────────────────────────────

document.getElementById("textForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = document.getElementById("textInput").value.trim();
  if (!text) return showResult('<span style="color:#eab308;">⚠️ Please enter some text.</span>');

  showLoading();

  try {
    const res = await fetch(`${API_BASE}/api/detect/text/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: text }),
    });
    const data = await res.json();
    showResult(buildResultHTML(data));
  } catch (err) {
    console.error(err);
    showResult('<span style="color:#ef4444;">❌ Could not connect to the backend.</span>');
  }
});

// ── Social verification ─────────────────────────────────────────────────────────

document.getElementById("socialForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const link = document.getElementById("socialLink").value.trim();
  const claim = document.getElementById("socialClaim").value.trim();

  if (!link) return showResult('<span style="color:#eab308;">⚠️ Please enter a URL.</span>');

  showLoading();

  try {
    const res = await fetch(`${API_BASE}/api/detect/social/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: link,
        claim: claim || "Verify this social media post.",
      }),
    });
    const data = await res.json();
    showResult(buildResultHTML(data));
  } catch (err) {
    console.error(err);
    showResult('<span style="color:#ef4444;">❌ Could not connect to the backend.</span>');
  }
});

// ── Image verification ──────────────────────────────────────────────────────────

document.getElementById("imageForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("imageFile");
  const claim = document.getElementById("imageClaim").value.trim();

  if (!fileInput.files || fileInput.files.length === 0) {
    return showResult('<span style="color:#eab308;">⚠️ Please select an image.</span>');
  }

  showLoading();

  try {
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    if (claim) formData.append("query", claim);

    const res = await fetch(`${API_BASE}/api/detect/image/`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    showResult(buildResultHTML(data));
  } catch (err) {
    console.error(err);
    showResult('<span style="color:#ef4444;">❌ Could not connect to the backend.</span>');
  }
});
