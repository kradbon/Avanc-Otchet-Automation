const API_BASE = import.meta.env.VITE_API_URL ?? "/api";

type RequestOptions = {
  method?: "GET" | "POST";
  token?: string | null;
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? "GET",
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {})
      },
      body: options.body ? JSON.stringify(options.body) : undefined
    });
  } catch {
    throw new Error(
      "API недоступно. Проверьте, что backend запущен на 127.0.0.1:8000."
    );
  }

  if (!response.ok) {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const error = (await response.json()) as { detail?: string };
      throw new Error(error.detail ?? "Ошибка запроса.");
    }
    throw new Error(await response.text());
  }

  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, token?: string | null) => request<T>(path, { token }),
  post: <T>(path: string, body: unknown, token?: string | null) =>
    request<T>(path, { method: "POST", body, token }),
  pdf: async (path: string, token?: string | null) => {
    let response: Response;

    try {
      response = await fetch(`${API_BASE}${path}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined
      });
    } catch {
      throw new Error(
        "PDF недоступен. Проверьте, что backend запущен на 127.0.0.1:8000."
      );
    }

    if (!response.ok) {
      throw new Error("Не удалось загрузить PDF.");
    }

    return response.blob();
  }
};
