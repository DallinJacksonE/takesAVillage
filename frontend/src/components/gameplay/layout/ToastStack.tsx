import type { GameNotification } from "../../../service/GameplayService";
import styles from "./GameplayNotifications.module.css";

export type ToastItem = GameNotification & { id: number };

export interface ToastStackProps {
  toasts: ToastItem[];
}

const ToastStack = ({ toasts }: ToastStackProps) => (
  <div className={styles.toastStack}>
    {toasts.map((toast) => {
      const notificationLevel = toast.level ?? "info";
      const levelClassName = styles[notificationLevel];

      return (
        <div
          className={`${styles.toast} ${levelClassName}`}
          key={toast.id}
          role="status"
        >
          {toast.message}
        </div>
      );
    })}
  </div>
);

export default ToastStack;
