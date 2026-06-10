import React, { useState, useRef } from "react";
import { createPortal } from "react-dom";

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
      className="player-tooltip-wrapper"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        display: children ? "inline-flex" : "inline",
        flex: children ? 1 : "none",
      }}
    >
      {children || displayText}

      {isHovered &&
        createPortal(
          /* The Ghost Wrapper: 
            This sits invisibly on top of your button, immune to overflow restrictions,
            providing the exact parent-context your CSS file expects.
          */
          <div
            className="player-tooltip-wrapper"
            style={{
              position: "fixed",
              top: `${coords.top}px`,
              left: `${coords.left}px`,
              width: `${coords.width}px`,
              height: `${coords.height}px`,
              zIndex: 99999,
              pointerEvents: "none", // Ensures the ghost doesn't block you from actually clicking the button underneath
            }}
          >
            {/* The Bubble: Unmodified so your App.css takes complete control */}
            <div className="player-tooltip-bubble" style={{ visibility: "visible", opacity: 1 }}>
              {infoText}
              <div className="player-tooltip-arrow" />
            </div>
          </div>,
          document.body
        )}
    </span>
  );
};

export default InfoTooltip;
