const API_BASE_URL = window.API_BASE_URL || "/api/v1";

export async function generateRecipe(payload) {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await safeErrorMessage(response);
    throw new Error(message);
  }

  return response.json();
}

async function safeErrorMessage(response) {
  try {
    const data = await response.json();
    if (Array.isArray(data.detail)) {
      return "Request validation failed";
    }
    return data.detail || "Request failed";
  } catch {
    return "Request failed";
  }
}
