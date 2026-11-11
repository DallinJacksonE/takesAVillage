export type TimerSeverity = "normal" | "warning" | "critical";

export const CRITICAL_TIMER_THRESHOLD_SECONDS = 15;
export const WARNING_TIMER_THRESHOLD_SECONDS = 30;

export const getTimerSeverity = (remainingSeconds: number): TimerSeverity => {
  if (remainingSeconds < CRITICAL_TIMER_THRESHOLD_SECONDS) {
    return "critical";
  }
  if (remainingSeconds <= WARNING_TIMER_THRESHOLD_SECONDS) {
    return "warning";
  }
  return "normal";
};
