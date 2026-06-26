import React, { useState } from "react";
import { ResearchVisualizationDTO } from "../../../../dtos";

interface VisualizationGalleryProps {
  visualizations?: ResearchVisualizationDTO[];
}

export const VisualizationGallery: React.FC<VisualizationGalleryProps> = ({ visualizations = [] }) => {
  const [selectedVisualization, setSelectedVisualization] = useState<ResearchVisualizationDTO | null>(null);

  if (visualizations.length === 0) {
    return <p style={{ color: "#888", fontStyle: "italic" }}>No visualizations are available yet.</p>;
  }

  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
        {visualizations.map((visualization) => (
          <button
            key={visualization.id}
            type="button"
            aria-label={`Open ${visualization.title}`}
            onClick={() => setSelectedVisualization(visualization)}
            style={{
              margin: 0,
              border: "1px solid #ddd",
              borderRadius: "6px",
              padding: "10px",
              background: "#fff",
              color: "inherit",
              textAlign: "left",
              cursor: "zoom-in",
            }}
          >
            <figure style={{ margin: 0 }}>
              <img
                src={visualization.url}
                alt={visualization.title}
                style={{ width: "100%", display: "block", borderRadius: "4px" }}
              />
              <figcaption style={{ marginTop: "8px", fontWeight: 600 }}>{visualization.title}</figcaption>
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
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1100,
        background: "rgba(0, 0, 0, 0.72)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "28px",
      }}
    >
      <div
        style={{
          width: "min(1200px, 96vw)",
          maxHeight: "92vh",
          overflow: "auto",
          background: "#fff",
          borderRadius: "10px",
          padding: "18px",
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.35)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", marginBottom: "14px" }}>
          <h2 style={{ margin: 0 }}>{visualization.title}</h2>
          <div style={{ display: "flex", gap: "10px" }}>
            <a
              className="btn"
              href={visualization.url}
              download={downloadFileName(visualization)}
              style={{ textDecoration: "none", backgroundColor: "#2c3e50" }}
            >
              Download Image
            </a>
            <button className="btn btn-secondary" style={{ color: "black" }} type="button" onClick={onClose}>Close</button>
          </div>
        </div>
        <img
          src={visualization.url}
          alt={visualization.title}
          style={{ width: "100%", maxHeight: "78vh", objectFit: "contain", display: "block", background: "#f7f7f7", borderRadius: "6px" }}
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
