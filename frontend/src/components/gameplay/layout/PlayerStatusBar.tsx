import type { ReactNode } from "react";
import type { Phase } from "../../../dtos";
import styles from "./PlayerStatusBar.module.css";
import { getTimerSeverity } from "./timerPresentation";

export interface PlayerStatusBarProps {
  day: number;
  phase: Phase;
  playerName: string;
  sprite: ReactNode;
  timeLeft: number;
}

const PlayerStatusBar = ({
  day,
  phase,
  playerName,
  sprite,
  timeLeft,
}: PlayerStatusBarProps) => {
  const timerSeverity = getTimerSeverity(timeLeft);
  const timerSeverityClass = styles[timerSeverity];

  return (
    <header className={styles.bar}>
      <div className={styles.identity}>
        <div className={styles.sprite}>{sprite}</div>
        <strong>{playerName}</strong>
      </div>
      <div className={styles.timerWrap}>
        <span className={styles.context}>
          Day {day} · {phase}
        </span>
        <span
          className={`${styles.timer} ${timerSeverityClass}`}
          data-severity={timerSeverity}
          role="timer"
        >
          {timeLeft}
        </span>
      </div>
      {/* Spacer element to keep the central timer centered in a 3-column grid */}
      <div aria-hidden="true" className={styles.balance} />
    </header>
  );
};

export default PlayerStatusBar;
