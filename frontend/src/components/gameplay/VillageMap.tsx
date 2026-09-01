import React, { useEffect, useRef, useState } from "react";
import {
  MapDataDTO,
  MapTileDTO,
  DevelopmentCostsDict,
  Phase,
  PublicPlayerDTO,
  DevelopmentDTO,
  Resource,
} from "../../dtos/index";
import { usePlayerName } from "../hooks/usePlayerName";
import PlayerInfo from "./playerInfo/PlayerInfo";
import { usePlayerColors } from "../hooks/usePlayerColor";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faWheatAwn,
  faTree,
  faMountain,
} from "@fortawesome/free-solid-svg-icons";
import styles from "./VillageMap.module.css";
import {
  axialToIsometric,
  getHexSlotForOccupantIndex,
  getNightFireSeatPosition,
  getPlayerMapPosition,
  getTradeGroupOffset,
} from "./mapGeometry";
import MapPlayerActor from "./player/MapPlayerActor";
import { getPhaseScene } from "./phaseScene";

interface Props {
  mapData: MapDataDTO;
  onBuild: (tileId: string) => void;
  playerId: string;
  development_costs: DevelopmentCostsDict;
  players: PublicPlayerDTO[];
  phase: Phase;
  onReact?: (emoji: "👍" | "❤️" | "😂" | "😠") => void;
  maxFireSeats?: number;
  onMaintain?: (devId: string) => void;
  onUpgrade?: (devId: string) => void;
  onContest?: (devId: string, side: "INITIATOR" | "CONTESTER" | "OWNER") => void;
  onApplyForJob?: (targetId: string, devId: string, wage: number, wageType: Resource) => void;
  onDraftTrade?: (targetId: string, offer: Record<string, number>, request: Record<string, number>) => void;
  onRequestSeat?: (targetId: string) => void;
  onOfferSeat?: (targetId: string) => void;
  myActions?: any[]; // using any[] to avoid importing ActionDTO here if not necessary, or we can use the proper type
  onAcceptApplicant?: (actionId: string) => void;
  onDenyApplicant?: (actionId: string) => void;
}

const VillageMap: React.FC<Props> = ({
  mapData,
  onBuild,
  playerId,
  development_costs,
  players,
  phase,
  onReact,
  maxFireSeats = 3,
  onMaintain,
  onUpgrade,
  onContest,
  onApplyForJob,
  onDraftTrade,
  onRequestSeat,
  onOfferSeat,
  myActions = [],
  onAcceptApplicant,
  onDenyApplicant,
}) => {
  const [selectedTile, setSelectedTile] = useState<MapTileDTO | null>(null);
  const [selectedPlayer, setSelectedPlayer] = useState<PublicPlayerDTO | null>(null);
  const mapCardRef = useRef<HTMLDivElement>(null);

  // Draft Job Application State for Map Popup
  const [appWage, setAppWage] = useState<number>(1);
  const [appWageType, setAppWageType] = useState<"food" | "wood" | "iron">("food");

  // Draft Trade State for Map Popup
  const [tradeOffer, setTradeOffer] = useState({ food: 0, wood: 0, iron: 0 });
  const [tradeRequest, setTradeRequest] = useState({ food: 0, wood: 0, iron: 0 });

  const [fireFit, setFireFit] = useState({
    scale: 1,
    x: 0,
    y: 0,
  });

  const getPlayerNameFromHook = usePlayerName();
  const { getPlayerColor } = usePlayerColors();
  const myPlayer = players.find(p => p.id === playerId);
  const scene = getPhaseScene(phase);

  /*
   * maxFireSeats is the number of player seats in addition to
   * the host.
   *
   * Slot 0 = host
   * Slot 1..maxFireSeats = additional seats
   *
   * Therefore there are maxFireSeats + 1 total vertices/pips.
   */
  const totalFireSeats = Math.max(1, Math.floor(maxFireSeats) + 1);

  const tradeIds = players.flatMap((player) =>
    player.visual_state.location.kind === "TRADE"
      ? [player.visual_state.location.id]
      : []
  );

  const fireHosts = players.filter(
    (player) =>
      player.visual_state.location.kind === "FIRE" &&
      player.visual_state.location.slot === 0
  );

  const fireIds = fireHosts.flatMap((host) =>
    host.visual_state.location.kind === "FIRE"
      ? [host.visual_state.location.id]
      : []
  );

  useEffect(() => {
    if (phase !== "NIGHT") {
      setFireFit({
        scale: 1,
        x: 0,
        y: 0,
      });
      return;
    }

    const card = mapCardRef.current;

    if (!card || fireIds.length === 0) {
      return;
    }

    const fitFireLayout = () => {
      const width = card.clientWidth;
      const height = card.clientHeight;

      if (width <= 0 || height <= 0) {
        return;
      }

      const points: { x: number; y: number }[] = [];

      fireIds.forEach((fireId) => {
        /*
         * Render maxFireSeats + 1 total positions,
         * but pass maxFireSeats to the geometry function because
         * the geometry function itself adds the host vertex.
         */
        for (
          let seatIndex = 0;
          seatIndex < totalFireSeats;
          seatIndex++
        ) {
          const seat = getNightFireSeatPosition(
            fireId,
            seatIndex,
            maxFireSeats,
            fireIds
          );

          points.push({
            x: seat.x,
            y: seat.y,
          });
        }

        const fire = getNightFireSeatPosition(
          fireId,
          0,
          maxFireSeats,
          fireIds
        );

        points.push({
          x: fire.x,
          y: fire.y,
        });
      });

      if (points.length === 0) {
        setFireFit({
          scale: 1,
          x: 0,
          y: 0,
        });
        return;
      }

      let minX = Infinity;
      let maxX = -Infinity;
      let minY = Infinity;
      let maxY = -Infinity;

      for (const point of points) {
        minX = Math.min(minX, point.x);
        maxX = Math.max(maxX, point.x);
        minY = Math.min(minY, point.y);
        maxY = Math.max(maxY, point.y);
      }

      const FIT_PADDING = 55;

      const layoutWidth =
        maxX - minX + FIT_PADDING * 2;
      const layoutHeight =
        maxY - minY + FIT_PADDING * 2;

      const scale = Math.min(
        1,
        (width - FIT_PADDING * 2) / layoutWidth,
        (height - FIT_PADDING * 2) / layoutHeight
      );

      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;

      setFireFit({
        scale,
        x: -centerX * scale,
        y: -centerY * scale,
      });
    };

    fitFireLayout();

    const resizeObserver = new ResizeObserver(fitFireLayout);
    resizeObserver.observe(card);

    window.addEventListener("resize", fitFireLayout);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", fitFireLayout);
    };
  }, [phase, fireIds.join(","), maxFireSeats, totalFireSeats]);

  const HEX_SIZE = window.innerWidth * 0.045;
  const hexWidth = HEX_SIZE * Math.sqrt(3);
  const hexHeight = HEX_SIZE * 2;
  const DEVELOPMENT_SPRITE_SIZE = HEX_SIZE * 1;

  const pointyClipPath =
    "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)";

  const hexToPixel = (q: number, r: number) => {
    return axialToIsometric(q, r, HEX_SIZE);
  };

  const woodsBackground = "#267447";
  const farmBackground = "#D9AA3F";
  const mineBackground = "#687783";
  const openBorder = "#F5E6B8";
  const myBorder = "#5BE58A";

  const getTypeColor = (type: string) => {
    switch (type) {
      case "Farm":
        return farmBackground;
      case "Woods":
        return woodsBackground;
      case "Mine":
        return mineBackground;
      default:
        return "#e0e0e0";
    }
  };

  const getOwnerColor = (ownerId?: string) => {
    if (!ownerId) return openBorder;
    if (ownerId === playerId) return myBorder;
    return getPlayerColor(ownerId);
  };

  const getDevelopmentSprite = (
    development: DevelopmentDTO
  ): string | undefined => {
    const base = ({
      Farm: "farm",
      Woods: "lumber_mill",
      Mine: "mine",
    } as const)[development.type as "Farm" | "Woods" | "Mine"];

    if (!base) return undefined;

    const level = Math.max(1, Math.min(3, development.level || 1));
    return `/images/sprites/developments/${base}/level-${level}.png`;
  };

  return (
    <div
      ref={mapCardRef}
      className={`card ${styles.mapCard} ${styles.card}`}
      aria-label={scene.label}
      data-phase={scene.theme}
      onClick={() => {
        setSelectedTile(null);
        setSelectedPlayer(null);
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          transformOrigin: "center center",
        }}
      >
        {scene.showAxialMap &&
          Object.values(mapData).map((tile) => {
            const { x, y } = hexToPixel(tile.q, tile.r);
            const isSelected =
              selectedTile?.id === tile.id;

            return (
              <div
                className={styles.hexTile}
                key={tile.id}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedTile(tile);
                }}
                style={{
                  position: "absolute",
                  left: x,
                  top: y,
                  width: hexWidth,
                  height: hexHeight,
                  background: tile.development
                    ? getOwnerColor(
                      tile.development.owner_id
                    )
                    : openBorder,
                  clipPath: pointyClipPath,
                  cursor: "pointer",
                  transform: `translate(-50%, -50%) ${isSelected
                    ? "scale(1.15)"
                    : "scale(1)"
                    }`,
                  transition:
                    "transform 0.15s ease-in-out",
                  zIndex: isSelected ? 10 : 1,
                }}
              >
                <div
                  className={styles.hexCore}
                  style={{
                    position: "absolute",
                    top: "4px",
                    left: "4px",
                    right: "4px",
                    bottom: "4px",
                    background: getTypeColor(tile.type),
                    clipPath: pointyClipPath,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexDirection: "column",
                    color: "#333",
                  }}
                >
                  {tile.development ? (
                    <img
                      src={getDevelopmentSprite(tile.development)}
                      alt=""
                      aria-hidden="true"
                      className={styles.developmentSprite}
                      draggable={false}
                      style={{
                        width: `${DEVELOPMENT_SPRITE_SIZE}px`,
                        height: `${DEVELOPMENT_SPRITE_SIZE}px`,
                      }}
                    />
                  ) : (
                    <span className={styles.field}>
                      {tile.type === "Farm" && (
                        <FontAwesomeIcon
                          icon={faWheatAwn}
                        />
                      )}
                      {tile.type === "Woods" && (
                        <FontAwesomeIcon
                          icon={faTree}
                        />
                      )}
                      {tile.type === "Mine" && (
                        <FontAwesomeIcon
                          icon={faMountain}
                        />
                      )}
                    </span>
                  )}
                </div>
              </div>
            );
          })}

        {!scene.showAxialMap && (
          <div className={styles.sceneTitle}>
            {scene.label}
          </div>
        )}

        {phase === "NIGHT" && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              pointerEvents: "none",
              transform: `translate(${fireFit.x}px, ${fireFit.y}px) scale(${fireFit.scale})`,
              transformOrigin: "center center",
            }}
          >
            {fireHosts.map((host) => {
              const fireId =
                host.visual_state.location.kind ===
                  "FIRE"
                  ? host.visual_state.location.id
                  : host.id;

              /*
               * Slot 0 is the host.
               * There are maxFireSeats + 1 total positions.
               *
               * IMPORTANT:
               * getNightFireSeatPosition receives maxFireSeats,
               * NOT totalFireSeats, because the geometry function
               * uses maxFireSeats to determine the polygon size.
               */
              const center =
                getNightFireSeatPosition(
                  fireId,
                  0,
                  maxFireSeats,
                  fireIds
                );

              return (
                <React.Fragment
                  key={`fire-group-${host.id}`}
                >
                  {Array.from(
                    { length: totalFireSeats },
                    (_, seatIndex) => {
                      const occupied =
                        players.some(
                          (player) =>
                            player.visual_state.location.kind ===
                            "FIRE" &&
                            player.visual_state.location.id ===
                            fireId &&
                            player.visual_state.location.slot ===
                            seatIndex
                        );

                      if (occupied) {
                        return null;
                      }

                      const seat =
                        getNightFireSeatPosition(
                          fireId,
                          seatIndex,
                          maxFireSeats,
                          fireIds
                        );

                      const isHostSeat =
                        seatIndex === 0;

                      return (
                        <div
                          aria-label={
                            isHostSeat
                              ? `Available host seat at ${getPlayerNameFromHook(
                                host.id
                              )}'s fire`
                              : `Available fire seat ${seatIndex} at ${getPlayerNameFromHook(
                                host.id
                              )}'s fire`
                          }
                          className={
                            styles.fireSeatDot
                          }
                          key={`fire-seat-${host.id}-${seatIndex}`}
                          style={{
                            left: seat.x,
                            top: seat.y,
                          }}
                        />
                      );
                    }
                  )}

                  <div
                    aria-label={`Campfire hosted by ${getPlayerNameFromHook(
                      host.id
                    )}`}
                    className={styles.campfire}
                    key={`fire-${host.id}`}
                    role="img"
                    style={{
                      left: center.x,
                      top: center.y + 35,
                    }}
                  />
                </React.Fragment>
              );
            })}
          </div>
        )}

        {players.map((player, index) => {
          const getPlayerTileId = (
            loc: typeof player.visual_state.location
          ): string | null => {
            if (loc.kind === "TILE") {
              return loc.id;
            }
            if (loc.kind === "DEVELOPMENT") {
              const tiles = Array.isArray(mapData)
                ? mapData
                : Object.values(mapData);
              const tile = tiles.find(
                (candidate) =>
                  candidate.development?.id === loc.id
              );
              return tile ? tile.id : null;
            }
            return null;
          };

          const tileId = getPlayerTileId(
            player.visual_state.location
          );
          const isHexLocation = tileId !== null;

          let hexSlot: number | undefined;
          if (isHexLocation) {
            if (
              player.visual_state.location.kind ===
              "TILE" ||
              player.visual_state.location.kind ===
              "DEVELOPMENT"
            ) {
              if (
                player.visual_state.location.slot !==
                undefined
              ) {
                hexSlot =
                  player.visual_state.location.slot;
              } else {
                const precedingPeers = players
                  .slice(0, index)
                  .filter(
                    (peer) =>
                      getPlayerTileId(
                        peer.visual_state.location
                      ) === tileId
                  ).length;
                hexSlot =
                  getHexSlotForOccupantIndex(
                    precedingPeers
                  );
              }
            }
          }

          const position = getPlayerMapPosition(
            player.visual_state.location,
            mapData,
            index,
            HEX_SIZE,
            fireIds,
            maxFireSeats,
            hexSlot
          );

          const tradeOffset =
            player.visual_state.location.kind ===
              "TRADE"
              ? getTradeGroupOffset(
                player.visual_state.location.id,
                tradeIds
              )
              : { x: 0, y: 0 };

          const locationKey = JSON.stringify(
            player.visual_state.location
          );

          const locationPeers = players
            .slice(0, index)
            .filter(
              (candidate) =>
                JSON.stringify(
                  candidate.visual_state.location
                ) === locationKey
            ).length;

          const isFireLocation =
            player.visual_state.location.kind ===
            "FIRE";

          const peerOffset = isFireLocation || isHexLocation
            ? { x: 0, y: 0 }
            : {
              x: locationPeers * 24,
              y: locationPeers * 8,
            };

          const finalX = isFireLocation
            ? (position.x + tradeOffset.x + peerOffset.x) * fireFit.scale + fireFit.x
            : isHexLocation
              ? position.x
              : position.x + tradeOffset.x + peerOffset.x;

          const finalY = isFireLocation
            ? (position.y + tradeOffset.y + peerOffset.y) * fireFit.scale + fireFit.y
            : isHexLocation
              ? position.y
              : position.y + tradeOffset.y + peerOffset.y;

          const isSelectedPlayer = selectedPlayer?.id === player.id;
          const isMe = player.id === playerId;

          return (
            <React.Fragment key={player.id}>
              <MapPlayerActor
                color={getPlayerColor(player.id)}
                isLocal={isMe}
                isSelected={isSelectedPlayer}
                onClick={phase !== "WORK" && player.visual_state.animation !== "DEAD" ? () => {
                  setSelectedPlayer(player);
                  setSelectedTile(null);
                  setTradeOffer({ food: 0, wood: 0, iron: 0 });
                  setTradeRequest({ food: 0, wood: 0, iron: 0 });
                } : undefined}
                onReact={isMe && phase !== "WORK" && player.visual_state.animation !== "DEAD" ? onReact : undefined}
                player={player}
                x={finalX}
                y={finalY}
              />

            </React.Fragment>
          );
        })}


      </div>
      {selectedPlayer && selectedPlayer.id !== playerId && (
        <div
          className="card"
          style={{
            position: "absolute",
            zIndex: 9999,
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
            background: "white",
            padding: "10px",
            borderRadius: "8px",
            boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            cursor: "default",
            minWidth: "220px"
          }}
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <h4 style={{ margin: 0 }}>{selectedPlayer.name}</h4>

          {phase === "TRADE" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", borderTop: "1px solid #eee", paddingTop: "8px" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: "bold" }}>Draft Trade</label>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "0.85rem" }}>
                <strong>Offer:</strong>
                <div style={{ display: "flex", gap: "4px" }}>
                  <label>Food: <input type="number" min={0} value={tradeOffer.food} onChange={e => setTradeOffer(o => ({ ...o, food: Number(e.target.value) }))} style={{ width: "50px" }} /></label>
                  <label>Wood: <input type="number" min={0} value={tradeOffer.wood} onChange={e => setTradeOffer(o => ({ ...o, wood: Number(e.target.value) }))} style={{ width: "50px" }} /></label>
                  <label>Iron: <input type="number" min={0} value={tradeOffer.iron} onChange={e => setTradeOffer(o => ({ ...o, iron: Number(e.target.value) }))} style={{ width: "50px" }} /></label>
                </div>
                <strong>Request:</strong>
                <div style={{ display: "flex", gap: "4px" }}>
                  <label>Food: <input type="number" min={0} value={tradeRequest.food} onChange={e => setTradeRequest(r => ({ ...r, food: Number(e.target.value) }))} style={{ width: "50px" }} /></label>
                  <label>Wood: <input type="number" min={0} value={tradeRequest.wood} onChange={e => setTradeRequest(r => ({ ...r, wood: Number(e.target.value) }))} style={{ width: "50px" }} /></label>
                  <label>Iron: <input type="number" min={0} value={tradeRequest.iron} onChange={e => setTradeRequest(r => ({ ...r, iron: Number(e.target.value) }))} style={{ width: "50px" }} /></label>
                </div>
              </div>
              <button className="btn success" onClick={() => {
                onDraftTrade?.(selectedPlayer.id, tradeOffer, tradeRequest);
                setSelectedPlayer(null);
              }}>
                Send Trade
              </button>
            </div>
          )}

          {phase === "NIGHT" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", borderTop: "1px solid #eee", paddingTop: "8px" }}>
              <label style={{ fontSize: "0.8rem", fontWeight: "bold" }}>Campfire Action</label>
              
              {myPlayer?.fire_status === "HOST" && (
                <button className="btn success" onClick={() => {
                  onOfferSeat?.(selectedPlayer.id);
                  setSelectedPlayer(null);
                }}>
                  Invite to Fire
                </button>
              )}

              {selectedPlayer.fire_status === "HOST" && (myPlayer?.fire_status === "COLD" || myPlayer?.fire_status === "GUEST") && (
                <button className="btn" onClick={() => {
                  onRequestSeat?.(selectedPlayer.id);
                  setSelectedPlayer(null);
                }}>
                  Request Seat
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {selectedTile && (
        <div
          className="card"
          style={{
            fontSize: 15,
            position: "absolute",
            zIndex: 9999,
            height: "auto",
            minWidth: "150px",
            width: "max-content",
            padding: "8px",
            boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
            transform: "translate(-50%, -50%)",
            left: "50%",
            top: "50%",
            background: "white",
            cursor: "default",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <h4 className={styles.field2}>
            {selectedTile.type}
          </h4>

          {selectedTile.development ? (
            <div className={styles.field3} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div>
                <strong className={styles.field4}>
                  OWNER:
                </strong>
                <br />
                <PlayerInfo
                  playerId={
                    selectedTile.development
                      .owner_id
                  }
                />
              </div>
              <div>Level: {selectedTile.development.level}</div>

              {selectedTile.development.owner_id ===
                playerId ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  <button className="btn" onClick={() => onMaintain?.(selectedTile.development!.id)}>
                    Maintain
                  </button>
                  <button className="btn" onClick={() => onUpgrade?.(selectedTile.development!.id)}>
                    Upgrade
                  </button>

                  {(myActions || []).filter(a => a.type === "EMPLOYMENT" && a.dev_id === selectedTile.development!.id && a.is_application && a.status === "PENDING").length > 0 && (
                    <div style={{ borderTop: "1px solid #eee", marginTop: "4px", paddingTop: "4px" }}>
                      <label style={{ fontSize: "0.8rem", fontWeight: "bold" }}>Job Applicants:</label>
                      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                        {(myActions || []).filter(a => a.type === "EMPLOYMENT" && a.dev_id === selectedTile.development!.id && a.is_application && a.status === "PENDING").map(app => (
                          <div key={app.id} style={{ display: "flex", flexDirection: "column", gap: "2px", background: "#f5f5f5", padding: "4px", borderRadius: "4px" }}>
                            <span style={{ fontSize: "0.8rem" }}>{getPlayerNameFromHook(app.initiator_id)} asks {app.wage} {app.wage_type}</span>
                            <div style={{ display: "flex", gap: "4px" }}>
                              <button className="btn success" style={{ flex: 1, padding: "2px" }} onClick={() => onAcceptApplicant?.(app.id)}>Hire</button>
                              <button className="btn danger" style={{ flex: 1, padding: "2px" }} onClick={() => onDenyApplicant?.(app.id)}>Reject</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : phase === "WORK" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", borderTop: "1px solid #eee", paddingTop: "8px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "0.8rem", fontWeight: "bold" }}>Apply for Job</label>
                    <div style={{ display: "flex", gap: "4px" }}>
                      <input type="number" value={appWage} onChange={e => setAppWage(Number(e.target.value))} style={{ width: "50px" }} />
                      <select value={appWageType} onChange={e => setAppWageType(e.target.value as Resource)}>
                        <option value="food">Food</option>
                        <option value="wood">Wood</option>
                        <option value="iron">Iron</option>
                      </select>
                    </div>
                    <button className="btn success" onClick={() => {
                      onApplyForJob?.(selectedTile.development!.owner_id, selectedTile.development!.id, appWage, appWageType);
                      setSelectedTile(null);
                    }}>
                      Apply
                    </button>
                  </div>
                  <button className="btn danger" onClick={() => {
                    onContest?.(selectedTile.development!.id, "OWNER");
                    setSelectedTile(null);
                  }}>
                    Contest Property
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <div className={styles.field6}>
              <div className={styles.field7}>
                Available for Development
              </div>

              <button
                className={`btn-tooltip success ${styles.field8}`}
                onClick={() => {
                  onBuild(selectedTile.id);
                  setSelectedTile(null);
                }}
              >
                Build:{" "}
                {development_costs[
                  selectedTile.type
                ]?.build
                  ? Object.entries(
                    development_costs[
                      selectedTile.type
                    ].build
                  )
                    .map(
                      ([resource, amount]) =>
                        `${amount} ${resource}`
                    )
                    .join(", ")
                  : "Unknown Cost"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VillageMap;