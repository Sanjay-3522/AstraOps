const BASE = "";

async function handle(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function getHealth() {
  return handle(await fetch(`${BASE}/api/health`));
}

export async function getIncidents(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return handle(await fetch(`${BASE}/api/incidents${qs ? `?${qs}` : ""}`));
}

export async function getHotspots() {
  return handle(await fetch(`${BASE}/api/hotspots`));
}

export async function predictEvent(payload) {
  return handle(
    await fetch(`${BASE}/predict/event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function simulateEvent(payload) {
  return handle(
    await fetch(`${BASE}/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function getSimilarEvents(params) {
  const qs = new URLSearchParams(params).toString();
  return handle(await fetch(`${BASE}/similar-events?${qs}`));
}

export async function postFeedback(payload) {
  return handle(
    await fetch(`${BASE}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function getLearningLog() {
  return handle(await fetch(`${BASE}/api/learning-log`));
}
