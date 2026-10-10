import type { ActionDTO, GameStateDTO, MapDataDTO, ResourceBundle } from "../../../dtos";

export interface PanelAttentionState {
  readonly seenKey: string | null;
  readonly hasAttention: boolean;
}

export interface PanelAttentionUpdate {
  readonly contentKey: string;
  readonly isOpen: boolean;
}

export const updatePanelAttention = (
  previous: PanelAttentionState | undefined,
  update: PanelAttentionUpdate,
): PanelAttentionState => {
  if (!previous || update.isOpen) {
    return {
      seenKey: update.contentKey,
      hasAttention: false,
    };
  }

  if (previous.seenKey !== update.contentKey) {
    return {
      seenKey: previous.seenKey,
      hasAttention: true,
    };
  }

  return previous;
};

const summarizeResources = (resources: ResourceBundle) => ({
  food: resources.food,
  iron: resources.iron,
  wood: resources.wood,
});

const summarizeAction = (action: ActionDTO) => ({
  id: action.id,
  initiator_id: action.initiator_id,
  status: action.status,
  target_id: action.target_id ?? null,
  type: action.type,
});

const summarizeCommittedAction = (action: GameStateDTO["me"]["committed_action"]) => {
  if (!action) {
    return null;
  }

  if ("action_id" in action) {
    return {
      action_id: action.action_id,
      development_id: action.development.id,
      employer_id: action.employer_id,
      type: "WORK",
    };
  }

  return summarizeAction(action);
};

const mapTiles = (mapData: MapDataDTO) => (
  Array.isArray(mapData) ? mapData : Object.values(mapData)
);

export const buildPhaseAttentionKey = (state: GameStateDTO): string => {
  const actionIds = state.me.actions
    .map(summarizeAction)
    .sort((left, right) => left.id.localeCompare(right.id));
  const availableWorkIds = state.me.available_work
    .map((job) => ({
      action_id: job.action_id,
      development_id: job.development.id,
      employer_id: job.employer_id,
      wage: job.wage,
      wage_type: job.wage_type,
    }))
    .sort((left, right) => (left.action_id || "").localeCompare(right.action_id || ""));
  const mapDevelopments = mapTiles(state.map)
    .map((tile) => ({
      development_id: tile.development?.id ?? null,
      is_contested: tile.development?.is_contested ?? false,
      owner_id: tile.development?.owner_id ?? null,
      pending_contest: tile.development?.pending_contest ?? false,
      q: tile.q,
      r: tile.r,
      tile_id: tile.id,
      type: tile.type,
    }))
    .sort((left, right) => left.tile_id.localeCompare(right.tile_id));

  return JSON.stringify({
    actions: actionIds,
    available_work: availableWorkIds,
    committed_action: summarizeCommittedAction(state.me.committed_action),
    developments: [...state.me.developments].sort(),
    finished_phase: state.me.finished_phase,
    fire_status: state.me.fire_status,
    map: mapDevelopments,
    phase: state.phase,
    phase_state: state.me.phase_state,
    resources: summarizeResources(state.me.resources),
  });
};
