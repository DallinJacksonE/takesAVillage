import type { TrainingService } from "./service.js";

export interface WatchdogScheduler {
  setInterval(callback: () => void | Promise<void>, milliseconds: number): unknown;
  clearInterval(handle: unknown): void;
}

const systemScheduler: WatchdogScheduler = {
  setInterval: (callback, milliseconds) => setInterval(() => { void callback(); }, milliseconds),
  clearInterval: (handle) => clearInterval(handle as NodeJS.Timeout),
};

export function startTrainingWatchdog(
  service: TrainingService,
  intervalMilliseconds = 30_000,
  staleAfterMilliseconds = 600_000,
  scheduler: WatchdogScheduler = systemScheduler,
  onError: (error: unknown) => void = () => undefined,
): () => void {
  const handle = scheduler.setInterval(
    () => service.reconcileStalled(staleAfterMilliseconds).catch(onError),
    intervalMilliseconds,
  );
  return () => scheduler.clearInterval(handle);
}
