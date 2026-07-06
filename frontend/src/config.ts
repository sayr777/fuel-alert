/** true по умолчанию — данные из моков дизайна «Топливный Дозор» */
export const USE_MOCKS =
  import.meta.env.VITE_USE_MOCKS !== "false" && import.meta.env.VITE_USE_MOCKS !== "0";

export const TELEGRAM_BOT_URL = import.meta.env.VITE_TELEGRAM_BOT_URL ?? "https://t.me/fuelwatch_bot";