import { API_BASE_URL } from "../../config.js";

export async function fazerLogout() {
  const response = await fetch(`${API_BASE_URL}/auth/sair`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  return await response.json();
}