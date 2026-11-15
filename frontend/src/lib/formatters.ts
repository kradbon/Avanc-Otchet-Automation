export const formatDate = (value: string) =>
  new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric"
  }).format(new Date(value));

export const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));

export const formatNumber = (value: number) =>
  new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1
  }).format(value);

const SUPPORTED_MONEY = new Set(["RUB", "TJS", "USD", "CNY"]);

const localeForCurrency: Record<string, string> = {
  RUB: "ru-RU",
  TJS: "ru-RU",
  USD: "en-US",
  CNY: "zh-CN"
};

export const formatMoneyAmount = (value: number, currency: string) => {
  const code = SUPPORTED_MONEY.has(currency) ? currency : "RUB";
  const locale = localeForCurrency[code] ?? "ru-RU";
  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: code,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    }).format(value);
  } catch {
    return `${formatNumber(value)} ${code}`;
  }
};

export const formatCurrency = (value: number) => formatMoneyAmount(value, "RUB");
