export type TimerSeverity = "normal" | "warning" | "critical";

export const getTimerSeverity = (seconds: number): TimerSeverity => {
  if (seconds < 15) return "critical";
  if (seconds <= 30) return "warning";
  return "normal";
};
