# TabbedCommunicator Refactor Implementation Plan

**Goal:** Break `TabbedCommunicator` into smaller chat UI components, move chat navigation to a right-side rail, sort created chats by most recent message, and stop rendering automatic per-player chat tabs.

**Architecture:** Keep `TabbedCommunicator` as the stateful coordinator for active chat selection, unread state, create-chat modal state, and send orchestration. Extract stateless/render-focused subcomponents for the active chat panel, the right-side tab rail, and the create-chat modal. Treat global chat and user-created chats as the only selectable conversations.

**Tech Stack:** React 19, TypeScript, existing DTOs and websocket presenter/service flow.

---

## Current context

- Existing file: `frontend/src/components/gameplay/communication/TabbedCommunicator.tsx`
- Existing call site: `frontend/src/views/Gameplay.tsx`
- Chat DTOs live in `frontend/src/dtos/index.ts`.
- Backend-created chat messages serialize a numeric `timestamp`, while `ChatMessageDTO` currently declares `created_at`; the refactor should tolerate both to sort by recency without requiring a backend change.
- Backend `game.create_chat()` already ensures the creator is included in `member_ids`, so the create modal should pass only selected other players.

## Implementation checklist

1. Add shared component-local types/helpers.
   - Create `frontend/src/components/gameplay/communication/chatViewTypes.ts`.
   - Define `ChatTabViewModel`, `ActiveChatViewModel`, `getMessageTime()`, and `getChatLastMessageTime()`.

2. Extract active chat rendering.
   - Create `frontend/src/components/gameplay/communication/ActiveChat.tsx`.
   - Props: active chat metadata, filtered display messages, current player id, input value/change/send callbacks, `getPlayerName`.
   - Own only scroll-to-bottom ref/effect and chat body/input rendering.

3. Extract right-side chat tab rail.
   - Create `frontend/src/components/gameplay/communication/ChatTabsRail.tsx`.
   - Render `+ New Chat` above the list.
   - Render `Village Square` first, then created chat tabs sorted by most recent message timestamp descending.
   - Show unread badges and active styles vertically.

4. Extract create chat modal.
   - Create `frontend/src/components/gameplay/communication/CreateChatModal.tsx`.
   - Keep name and selected-player draft state inside the modal.
   - Clear draft state on successful create/cancel.
   - Disable create unless name is non-empty and at least one other player is selected.

5. Rewrite `TabbedCommunicator.tsx` as the coordinator.
   - Import `ChatDTO` from `frontend/src/dtos` instead of declaring a local duplicate.
   - Remove automatic per-player tabs and private-chat filtering.
   - Keep only `global` and backend-created chat ids as valid active ids.
   - If the active chat disappears, fall back to `global`.
   - Mark visible messages read when active chat/messages change.
   - Build tab view models with unread counts and last-message timestamps.
   - Pass selected active chat to `ActiveChat`.

6. Update DTO compatibility.
   - Update `ChatMessageDTO` to allow `timestamp?: number` and `created_at?: string` so current backend messages and older timestamped records can both type-check.

7. Validate.
   - Run `npm run build` from `frontend/`.
   - If unrelated repo errors remain, capture a targeted grep showing no `TabbedCommunicator`/new communication component errors.

## Acceptance criteria

- `TabbedCommunicator` is small and delegates UI to subcomponents.
- `ActiveChat` renders based on selected global/chat tab.
- Tabs are vertical on the right side.
- `+ New Chat` is above the chat list on the right side.
- Created chat tabs sort by most recent message, not alphabetically.
- No automatic one-tab-per-player/direct-message list is rendered.
- TypeScript diagnostics for the touched communication components are clean, aside from unrelated existing build blockers.
