import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ModerationPanel from "../../components/ModerationPanel";

vi.mock("react-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-dom")>();
  return {
    ...actual,
    createPortal: (children: React.ReactNode) => children,
  };
});

const EVENT_TYPE_MAP = {
  NO_FUEL: {
    code: "NO_FUEL",
    label_ru: "Топливо отсутствует",
    color: "#FF4B3E",
    requires_moderation: false,
    ttl_hours: 24,
    attributes: ["fuel_grades"],
  },
};

beforeEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe("ModerationPanel — login screen", () => {
  it("shows login form when no token in sessionStorage", () => {
    render(<ModerationPanel eventTypeMap={EVENT_TYPE_MAP} onClose={vi.fn()} />);
    expect(screen.getByPlaceholderText("Токен")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Войти/i })).toBeInTheDocument();
  });

  it("login button is disabled when token is empty", () => {
    render(<ModerationPanel eventTypeMap={EVENT_TYPE_MAP} onClose={vi.fn()} />);
    expect(screen.getByRole("button", { name: /Войти/i })).toBeDisabled();
  });

  it("login button enables when token is typed", async () => {
    const user = userEvent.setup();
    render(<ModerationPanel eventTypeMap={EVENT_TYPE_MAP} onClose={vi.fn()} />);
    await user.type(screen.getByPlaceholderText("Токен"), "abc123");
    expect(screen.getByRole("button", { name: /Войти/i })).toBeEnabled();
  });
});

describe("ModerationPanel — authenticated (mocks)", () => {
  async function renderAuthenticated(onClose = vi.fn()) {
    sessionStorage.setItem("fuelwatch-mod-token", "test-token");
    render(<ModerationPanel eventTypeMap={EVENT_TYPE_MAP} onClose={onClose} />);
    // Wait for an element that only exists in authenticated state (tabs sidebar)
    await waitFor(() => screen.getByRole("button", { name: /Очередь/ }), { timeout: 3000 });
  }

  it("shows sidebar tabs after auth", async () => {
    await renderAuthenticated();
    expect(screen.getByRole("button", { name: /Очередь/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Опубликованные/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Удалённые/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Мониторинг/ })).toBeInTheDocument();
  });

  it("shows back to map button", async () => {
    await renderAuthenticated();
    expect(screen.getByText(/← Карта/)).toBeInTheDocument();
  });

  it("calls onClose when back button clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    await renderAuthenticated(onClose);
    await user.click(screen.getByText(/← Карта/));
    expect(onClose).toHaveBeenCalled();
  });

  it("switches to Monitoring tab and shows service cards", async () => {
    const user = userEvent.setup();
    await renderAuthenticated();
    await user.click(screen.getByRole("button", { name: /Мониторинг/ }));
    // "Статус сервисов" header is always visible; wait for cards which appear only after health data loads
    await waitFor(() => {
      screen.getByText(/База данных/);
      screen.getByText(/Redis/);
      screen.getByText(/Telegram/);
    }, { timeout: 3000 });
  });

  it("switches to Published tab and shows date filter inputs", async () => {
    const user = userEvent.setup();
    await renderAuthenticated();
    await user.click(screen.getByRole("button", { name: /Опубликованные/ }));
    // Tab switch is a synchronous state update — date inputs appear immediately after click
    const dateInputs = document.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBeGreaterThan(0);
  });

  it("monitoring tab shows log viewer with container tabs", async () => {
    const user = userEvent.setup();
    await renderAuthenticated();
    await user.click(screen.getByRole("button", { name: /Мониторинг/ }));
    await waitFor(() => {
      screen.getByText(/База данных/);
    }, { timeout: 3000 });
    // Log viewer appears once containers are loaded from mock health data
    await waitFor(() => {
      expect(document.querySelector(".log-viewer")).toBeTruthy();
    }, { timeout: 3000 });
    // Each container becomes a tab in the log viewer
    const logTabs = document.querySelectorAll(".log-tab");
    expect(logTabs.length).toBeGreaterThan(0);
  });
});
