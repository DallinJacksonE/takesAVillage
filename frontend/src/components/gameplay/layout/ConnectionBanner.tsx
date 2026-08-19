import type { ConnectionState } from "../../../service/GameplayService";
import styles from "./GameplayNotifications.module.css";

interface Props {
  state: ConnectionState;
}

const ConnectionBanner = ({ state }: Props) => {
  if (state === "CONNECTED") return null;

  return (
    <div
      className={`${styles.connectionBanner} ${state === "CONNECTING" ? styles.connecting : styles.disconnected}`}
      role="status"
    >
      {state === "CONNECTING"
        ? "Negotiating connection..."
        : "Connection lost. Watchdog is reconnecting..."}
    </div>
  );
};

export default ConnectionBanner;
