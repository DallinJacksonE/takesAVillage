import type { ConnectionState } from "../../../service/GameplayService";
import styles from "./GameplayNotifications.module.css";

export interface ConnectionBannerProps {
  state: ConnectionState;
}

const ConnectionBanner = ({ state }: ConnectionBannerProps) => {
  if (state === "CONNECTED") {
    return null;
  }

  const isConnecting = state === "CONNECTING";
  const statusClassName = isConnecting ? styles.connecting : styles.disconnected;
  const bannerMessage = isConnecting
    ? "Negotiating connection..."
    : "Connection lost. Watchdog is reconnecting...";

  return (
    <div
      className={`${styles.connectionBanner} ${statusClassName}`}
      role="status"
    >
      {bannerMessage}
    </div>
  );
};

export default ConnectionBanner;
