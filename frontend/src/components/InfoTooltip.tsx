import React, { useState, useRef } from "react";
import { createPortal } from "react-dom";
import styles from "./InfoTooltip.module.css";

interface Props {
  /** The text or element that the user will see and hover over */
  displayText?: string | React.ReactNode;
  /** The detailed information that appears inside the tooltip bubble */
  infoText: string | React.ReactNode;
  /** The component to wrap the tooltip around */
  children?: React.ReactNode;
}

const InfoTooltip: React.FC<Props> = ({ displayText, infoText, children }) => {
  const [isHovered, setIsHovered] = useState(false);
  // We now track the width and height as well to create an exact clone of the bounding box
  const [coords, setCoords] = useState({ top: 0, left: 0, width: 0, height: 0 });
  const wrapperRef = useRef<HTMLSpanElement>(null);

  const handleMouseEnter = () => {
    if (wrapperRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect();
      setCoords({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height,
      });
    }
    setIsHovered(true);
  };

  return (
    <span
      ref={wrapperRef}
      className={[styles.wrapper, children ? styles.childWrapper : styles.inlineWrapper].join(" ")}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setIsHovered(false)}
    >
      {children || displayText}

      {isHovered &&
        createPortal(
          /* The Ghost Wrapper: 
            This sits invisibly on top of your button, immune to overflow restrictions,
            providing the exact parent-context your CSS file expects.
          */
          <div
            className={styles.portalFrame}
            style={{
              top: `${coords.top}px`,
              left: `${coords.left}px`,
              width: `${coords.width}px`,
              height: `${coords.height}px`,
            }}
          >
            {/* The Bubble: Unmodified so your App.css takes complete control */}
            <div className={styles.bubble}>
              {infoText}
              <div className={styles.arrow} />
            </div>
          </div>,
          document.body
        )}
    </span>
  );
};

export default InfoTooltip;
