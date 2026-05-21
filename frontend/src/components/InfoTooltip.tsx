import React, { useState } from "react";

interface Props {
  /** The text or element that the user will see and hover over */
  displayText: string | React.ReactNode;
  /** The detailed information that appears inside the tooltip bubble */
  infoText: string | React.ReactNode;
}

const InfoTooltip: React.FC<Props> = ({ displayText, infoText }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <span
      className="player-tooltip-wrapper"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {displayText}

      {isHovered && (
        <div className="player-tooltip-bubble">
          {infoText}
          <div className="player-tooltip-arrow" />
        </div>
      )}
    </span>
  );
};

export default InfoTooltip;
