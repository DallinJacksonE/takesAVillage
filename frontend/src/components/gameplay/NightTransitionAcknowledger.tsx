import { useEffect, useRef } from "react";
import type { GameStateDTO } from "../../dtos";
import { getGoblinSpriteForAnimation } from "./player/playerSpriteCatalog";

interface Props {
  state: GameStateDTO;
  onComplete: (transitionId: string) => void;
}

const NightTransitionAcknowledger = ({ state, onComplete }: Props) => {
  const scheduled = useRef(new Set<string>());

  useEffect(() => {
    const transition = state.night_transition;
    if (
      !transition
      || !transition.affected_player_ids.includes(state.me.id)
      || scheduled.current.has(transition.id)
    ) {
      return;
    }

    const player = state.player_list.find((candidate) => candidate.id === state.me.id);
    if (!player || !["HURT", "DEAD"].includes(player.visual_state.animation)) {
      return;
    }

    scheduled.current.add(transition.id);
    const sprite = getGoblinSpriteForAnimation(player.visual_state.animation);
    const prefersReducedMotion = window.matchMedia?.(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const delay = prefersReducedMotion
      ? 0
      : Math.ceil((sprite.frameCount / sprite.fps) * 1000) + 100;
    const timer = window.setTimeout(() => onComplete(transition.id), delay);
    return () => window.clearTimeout(timer);
  }, [onComplete, state]);

  return null;
};

export default NightTransitionAcknowledger;
