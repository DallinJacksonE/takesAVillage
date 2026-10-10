import type { ReactNode } from "react";
import type { Phase } from "../../../dtos";
import styles from "./PlayerStatusBar.module.css";
import { getTimerSeverity } from "./timerPresentation";

interface Props {
  day: number;
  phase: Phase;
  playerName: string;
  sprite: ReactNode;
  timeLeft: number;
}

const PlayerStatusBar = ({ day, phase, playerName, sprite, timeLeft }: Props) => {
  const severity = getTimerSeverity(timeLeft);

  return (
    <header className={styles.bar}>
      <div className={styles.identity}>
        <div className={styles.sprite}>{sprite}</div>
        <strong>{playerName}</strong>
      </div>
      <div className={styles.timerWrap}>
        <span className={styles.context}>Day {day} · {phase}</span>
        <span
          className={`${styles.timer} ${styles[severity]}`}
          data-severity={severity}
          role="timer"
        >
          {timeLeft}
        </span>
      </div>
      <div aria-hidden="true" className={styles.balance} />
    </header>
  );
};

export default PlayerStatusBar;
