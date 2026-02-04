import React, { useState } from 'react';

const VillageMap = ({ mapData, players }) => {
  const [selectedTile, setSelectedTile] = useState(null);

  // Constants for Hex Layout
  const HEX_SIZE = 50;
  const HEX_WIDTH = Math.sqrt(3) * HEX_SIZE;
  const HEX_HEIGHT = 2 * HEX_SIZE;

  // Convert Axial (q, r) to Pixel (x, y) for Iso layout
  const hexToPixel = (q, r) => {
    const x = HEX_SIZE * (Math.sqrt(3) * q + Math.sqrt(3) / 2 * r);
    const y = HEX_SIZE * (3. / 2 * r);
    return { x, y };
  };

  if (!mapData || mapData.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center', color: '#888' }}>Map generating...</div>;
  }

  return (
    <div className="card" style={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px' }}>Village Map</h3>

      <div style={{ flex: 1, position: 'relative', overflow: 'hidden', background: '#e0e5ec' }}>

        {/* Map Viewport - Centered */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)'
        }}>
          {mapData.map((tile) => {
            const { x, y } = hexToPixel(tile.q, tile.r);

            // Color based on type
            let bg = '#ccc';
            if (tile.type === 'Farm') bg = '#8bc34a'; // Green
            if (tile.type === 'Woods') bg = '#795548'; // Brown
            if (tile.type === 'Mine') bg = '#607d8b'; // Blue-Grey

            return (
              <div
                key={tile.id}
                onClick={() => setSelectedTile(tile)}
                style={{
                  position: 'absolute',
                  left: x,
                  top: y,
                  width: `${HEX_SIZE * 1.6}px`,
                  height: `${HEX_SIZE * 1.6}px`,
                  backgroundColor: bg,
                  clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  fontSize: '0.7rem',
                  color: 'white',
                  fontWeight: 'bold',
                  boxShadow: 'inset 0 0 10px rgba(0,0,0,0.2)',
                  border: selectedTile?.id === tile.id ? '3px solid white' : 'none',
                  zIndex: 10
                }}
              >
                {tile.type[0]}
              </div>
            );
          })}
        </div>

        {/* Floating Tooltip / Info Panel */}
        {selectedTile && (
          <div style={{
            position: 'absolute',
            bottom: '20px',
            right: '20px',
            width: '200px',
            background: 'white',
            padding: '15px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 100
          }}>
            <h4 style={{ margin: '0 0 5px 0' }}>{selectedTile.type} Plot</h4>
            <div style={{ fontSize: '0.85rem', color: '#666' }}>
              ID: {selectedTile.id}<br />
              Coords: {selectedTile.q}, {selectedTile.r}
            </div>
            <hr style={{ margin: '10px 0', border: '0', borderTop: '1px solid #eee' }} />
            {selectedTile.owner_id ? (
              <div>
                <strong>Owner:</strong><br />
                Player {selectedTile.owner_id.substring(0, 8)}...
              </div>
            ) : (
              <div style={{ color: '#2e7d32', fontStyle: 'italic' }}>
                Available for Development
              </div>
            )}
            <button
              className="btn btn-secondary"
              style={{ marginTop: '10px', width: '100%', padding: '5px' }}
              onClick={() => setSelectedTile(null)}
            >
              Close
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

export default VillageMap;
