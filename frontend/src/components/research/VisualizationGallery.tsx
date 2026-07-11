import React, { useState } from "react";
import { ResearchVisualizationDTO } from "../../dtos";

import styles from "./VisualizationGallery.module.css";
interface VisualizationGalleryProps {
  visualizations?: ResearchVisualizationDTO[];
}

export const VisualizationGallery: React.FC<VisualizationGalleryProps> = ({ visualizations = [] }) => {
  const [selectedVisualization, setSelectedVisualization] = useState<ResearchVisualizationDTO | null>(null);

  if (visualizations.length === 0) {
    return <p className={styles.copy}>No visualizations are available yet.</p>;
  }

  return (
    <>
      <div className={styles.panel2}>
        {visualizations.map((visualization) => (
          <button
            key={visualization.id}
            type="button"
            aria-label={`Open ${visualization.title}`}
            onClick={() => setSelectedVisualization(visualization)}
            className={styles.thumbnailButton}
          >
            <figure className={styles.figure}>
              <img
                src={visualization.url}
                alt={visualization.title}
                className={styles.image2}
              />
              <figcaption className={styles.figcaption}>{visualization.title}</figcaption>
            </figure>
          </button>
        ))}
      </div>
      {selectedVisualization && (
        <VisualizationModal
          visualization={selectedVisualization}
          onClose={() => setSelectedVisualization(null)}
        />
      )}
    </>
  );
};

interface VisualizationModalProps {
  visualization: ResearchVisualizationDTO;
  onClose(): void;
}

const VisualizationModal: React.FC<VisualizationModalProps> = ({ visualization, onClose }) => {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={visualization.title}
      className={styles.modal}
    >
      <div
        className={styles.panel}
      >
        <div className={styles.row2}>
          <h2 className={styles.header}>{visualization.title}</h2>
          <div className={styles.row}>
            <a
              className={`btn ${styles.a}`}
              href={visualization.url}
              download={downloadFileName(visualization)}
              
            >
              Download Image
            </a>
            <button className={`btn btn-secondary ${styles.button}`}  type="button" onClick={onClose}>Close</button>
          </div>
        </div>
        <img
          src={visualization.url}
          alt={visualization.title}
          className={styles.image}
        />
      </div>
    </div>
  );
};

function downloadFileName(visualization: ResearchVisualizationDTO): string {
  const baseName = visualization.name || visualization.title;
  const safeName = baseName.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return `${safeName || "visualization"}.png`;
}
