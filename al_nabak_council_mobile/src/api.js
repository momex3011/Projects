const DEFAULT_API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://127.0.0.1:5000";

export function cleanBaseUrl(value) {
  return (value || DEFAULT_API_BASE_URL).trim().replace(/\/+$/, "");
}

async function requestJson(baseUrl, path, options = {}) {
  const url = `${cleanBaseUrl(baseUrl)}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.message || `Request failed (${response.status})`);
  }
  return payload;
}

export function getBootstrap(baseUrl, locale) {
  return requestJson(baseUrl, `/${locale}/api/mobile/bootstrap`);
}

export function getProjects(baseUrl, locale) {
  return requestJson(baseUrl, `/${locale}/api/mobile/projects`);
}

export function getProposals(baseUrl, locale) {
  return requestJson(baseUrl, `/${locale}/api/mobile/proposals`);
}

export function getDonationCampaigns(baseUrl, locale) {
  return requestJson(baseUrl, `/${locale}/api/mobile/donations`);
}

export function submitSuggestion(baseUrl, locale, body) {
  return requestJson(baseUrl, `/${locale}/api/mobile/suggestions`, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function submitVolunteer(baseUrl, locale, projectId, body) {
  return requestJson(baseUrl, `/${locale}/api/mobile/projects/${projectId}/volunteer`, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function submitDonationPledge(baseUrl, locale, campaignId, body) {
  return requestJson(baseUrl, `/${locale}/api/mobile/donations/${campaignId}/pledge`, {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export { DEFAULT_API_BASE_URL };
