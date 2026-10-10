import type { GameNotification } from "../../../service/GameplayService";
import styles from "./GameplayNotifications.module.css";

export type ToastItem = GameNotification & { id: number };

interface Props {
  toasts: ToastItem[];
}

const ToastStack = ({ toasts }: Props) => (
  <div className={styles.toastStack}>
    {toasts.map((toast) => (
      <div
        className={`${styles.toast} ${styles[toast.level ?? "info"]}`}
        key={toast.id}
        role="status"
      >
        {toast.message}
      </div>
    ))}
  </div>
);

export default ToastStack;
