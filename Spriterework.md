# Sprite rework plan

## End Goal

To have a frontend that is more intuitive for the user to use and to have animated sprites to show village information.

Our current frontend is hard for new users to intuit what is going on, there are lots of component containers with different functionalities that change often, and the game state is not expressed to the human players as cleanly as it should be. We want to change the client to:

- Be more like playing a game than interacting with menues
- update the client so it reflects the recent gameplay changes of intent and being able to unlock that intent.
- harden the packages of state that the backend is sending to the players (they shouldn't be getting data about how many days the game is, and the time left packet isn't updating correctly where it sends 59 seconds left for the whole minute)

## Making it feel more like a game
We have the first steps for having animated character sprites in the game, we will expand on this to have the following functionality.
- the game will be a village map primarily that shows the village tiles/developments, and animates each player as a goblin sprite walking around and doing the work/trading/sleeping/dying/sick animations. We will want to make a shader or some script that outlines the gobnlins with the player color. This map is the main focus of the screen, and will have the other menus and interactive components drawn on top of the map to the sides. These will be expandable side panels, with one on the left for showing the gamephase and phase specific actions like working/contesting/maintaining/upgrading the village developments for WORK, trading for TRADE, and campfires for NIGHT. During each phase the animated village will have a different colored sky, and the side panel will have a red dot that shows the player if there are updates to their choices that need attention. On the right will be the village chat, which has the group village chat and the ability for the player to make new group chats with other village members. 

- the player's goblin will be positioned around the village depending on what is happening in the game. During work, once they have a work intent, the goblin will walk over to that development and start doing the work animation on the tile (dig/water for farm, mine for mine, and axe for woods), if the player chooses to start a CONTEST they will walk over and start animating a jump or attack. As other players work in different places or take part in the contests, the frontend will animate the players walking over to where they are at and this will help players to better see what is going on. If a player is sick, they stay at one of their developments and do a sleeping animation.

- during trading, the map will change from the goblins walking on the village map tiles to the goblins in a forest clearing, once a trade has been agreed the two goblins will walk towards eachother doing the carry animation and stop, once they have finalized their shippment, the two goblins will walk back to their starting location. Eventually we should have the players able to have unhappy emojis appear once they walk back if they were cheated in their trade.

- during the night, the clearing will be darker, and goblins will wither walk and start a campfire, or walk to a campfire they are a guest at, goblins who have no fire will stand in the dark alone. Then at the end of the day an animation will play where the players that got sick will do the damge animation and the players who die will do the death animation. For each sickness and death we want to send a toast notification.

## Better game awareness

We currently have the timer and the player name on the top of the webpage, but the player's don't see it if they are scrolled down. We want to overhaul this with a sticky bar at the top of the player's gameplay page that shows the Time left in the round in the center in a big mono font that turns orange at 30sec and red for <15sec. on the left of this bar is the player's name, and their goblin animation, so the animation will be happening in two places, one on the map, but also as a smaller icon in the player's bar so they can see what color they are and what they are doing to help with identifying themselves on the map.

## Intent and changing intent
Now players can change their intent so long as the game time has not run out and other players have not committed their intent yet. If a player hasn't done and immediate action, then they can undo their intent and choose something else. This applies to working, supporting a contest, or being a guest at a fire. Starting a contest or fire is immediate and a player can't undo that once its been done.

## Better sprite functionality
We want the sprites to work well, and some of the png strips have different amounts of frames. in the stip names, the last number at the end of the name is the frame count, with the strip going ten frames across before starting a new row of frames underneath the strip. This isn't yet a part of the code, so sprites with more than 10 frames do not work correctly.

## Other questions or suggestions:

### Scope and rollout

1. Is the first implementation expected to deliver every behavior described above in one release, or should it be split into milestones (for example: shell/map and timer, then WORK animations, then TRADE, then NIGHT and end-of-day effects)? Is the unhappy trade emoji explicitly out of scope for this rework because it is described as eventual?

We can work in milestones, and I think we should include the emojis as a functionality the player has when right clicking their own sprite on the map, they can select some emojis that will appear over their sprite's head for others to see for a few seconds.

2. Is this rework desktop-first, or is there a minimum mobile/tablet viewport that the map and two side panels must support? On narrow screens, should panels become drawers, stack below the map, or remain overlaid?

Desktop first, but we do need to considre laptops and mobile as well, having the chat overlaid but toggled to the side and the actions as drawers underneath is good for smaller screens for now.

3. Should the existing gameplay cards be restyled and moved into the new panels while preserving their current workflows, or is their interaction design also intended to change?

We can keep the existing workflow for many of them, but they need to be restyled.

### Map, scenes, and assets

4. Should the main WORK scene remain the current axial hex map driven by `MapTileDTO.q/r`, but rendered with the Sunnyside tileset, or should it become a separately authored village scene? If it is authored, where should tile/development and player anchor coordinates be defined?

The work scence should remain the axial hex map with the tileset, players can start on one of their developments then walk around. We want an isometric view if possible. When the player's mouse is over a tile with a player, they can see the player name and health. If they click the tile, they will see the tile map information.

5. Which existing art should represent undeveloped Farm/Woods/Mine tiles, each development type and level, campfires, the trade clearing, and phase-specific skies? Are placeholder tiles acceptable until final assets are selected?

Placeholder tiles are acceptable for now

6. The curated goblin folder currently has idle, axe, death, dig, hammering, mining, and watering strips, but no curated walk, carry, sleep, hurt, jump/attack, or campfire sprites. Should those be copied/derived from the bundled Sunnyside source assets, supplied separately, or represented by temporary fallbacks? Which animation should be used for each development level/action?

Yes, look through the Sunnyside assets for useful sprites/tiles/assets and move those to where we can use them.

7. Should player-color outlines be implemented with a browser/CSS filter, an SVG/canvas mask, or a WebGL shader? What browsers must it support, and should the existing client-assigned palette remain authoritative and consistent for every player?

We want to support chrome and firefox for now. A css filter or a canvas mask would be great if we can git a 3px outline around the goblin easily enough, if not we can use a shader or something.

8. How should multiple goblins at the same development/fire/trade endpoint be arranged, and what movement rules are expected (straight-line tween vs pathfinding, speed, collision/overlap handling, and whether phase changes teleport or animate players into the new scene)?

As sprites on a tile increase, have their location points update. One sprite is in the center, two is a line one on each end, three has a triangle, four is a square etc. we can form a geometric shape based on the points of the shape matching the sprites on the shape.

### Authoritative state and privacy

9. Which animation/activity facts should the backend expose for every visible player? The current public `player_list` contains each player's full resources, actions, timeline, available work, and committed action. Should it instead use a deliberately limited public-player DTO plus a private `me` DTO, and exactly which fields are public?

The we should have an ENUM state in the player object that calculated whenever the player is updated which animation it should have.

10. The plan says players “shouldn't be getting data about how many days the game is.” Does that mean remove only `game_length` (which the backend currently sends but the frontend DTO omits), or also hide the current `day`? The sticky bar description still calls for game/phase awareness, so should it display the current day?

The game length is variable so we don't see toxic strategy at the end of the game, we want collaboration to continue so that is datat the players shouldn't have.

11. Should animation state be a backend-authored enum/event stream (for example `WALKING_TO_WORK`, `WORKING`, `CARRYING`, `SICK`, `DYING`), or should the client derive it from phase, health, fire status, contracts, and public intent fields? How should the client distinguish a newly completed event that must play once from persistent state that loops?

Yes, the backend can track the animation state and locations on the map so that people see consistent animations/emojis of the players, we might need a way for the python map in the backend to transition to the hexmap on the frontend

12. At NIGHT resolution, should hurt/death animations delay the visual transition to the next WORK state, or play over the newly received state? How long should they play, and should sickness/death toasts be sent only to the affected player or to everyone in the village?

They should delay the next day until they complete, then the game should move on to the next work phase

### Intent and attention behavior

13. What should the new undo/unlock command be called, and which exact intents can it clear: work, maintenance, upgrade, contest support, and campfire guest acceptance? The backend currently has internal `clear_intent()` support but exposes no client command for it.

When a player is committed to an intent, they can still see their other opportunities as valid options that if they click on those after their first descision, will then change their intent. If a player is at a dev with working intent but the development is contested, they will see the contesting player come up to the dev and they will see their own goblin return to one of their devs and idle until they choose something else.

14. What precisely makes an intent no longer undoable? In particular, does “other players have not committed their intent yet” mean nobody else has submitted any intent, nobody has committed a dependent intent for the same development/fire, or something else? Does pressing End Phase create an additional lock beyond submitting an intent?

There are actions that take effect at the end of a round, and actions that take effect immediately. Buidling, starting a contest, and starting a fire are immediate, as well as trading, which happends as soon as both have finished a trade.

15. Starting a contest, building a development, and starting a fire currently have immediate effects. Please confirm the complete list of irreversible immediate actions and whether accepting employment, trade, or campfire contracts remains reversible/cancelable under the new rules.

See above. Trades are communications that can be revoked as well.

16. What should trigger and clear the red attention dot on the left panel: any newly received state, an invalidated intent, an incoming contract/chat-like request, an available action, or a phase-specific curated list? Should unread attention survive panel close/reopen, page reload, or reconnect?

If a side panel recieves a state update and has not been expanded, then the player has not seen that information yet, once opened the dot can clear.

### Timer and acceptance criteria

17. What is the intended timer protocol and display format? Should the backend send an absolute phase deadline for a client countdown, broadcast remaining seconds periodically, or keep sending snapshots that the presenter reconciles? Should `60` display for the first second of a minute, and should the thresholds be orange at `<= 30` and red at `< 15` exactly?
18. Are there target FPS, maximum player count, supported browsers, keyboard/accessibility requirements, and reduced-motion behavior that should be treated as acceptance criteria for the animated map and overlay panels?

Target fps is 30, but if we can have easy way to change that number and the relation to the animation frames that would be great.

19. Should sprite metadata always trust the frame count encoded in the filename, and how should malformed/incomplete strips be handled? For example, `spr_death_strip13.png` is currently only 864×64 (nine 96×64 frames), so it cannot contain 13 frames under the stated ten-frames-per-row convention.

Let's try to make the code robust to the file metadata then, we know for sure that the frames go from left to right and we can use that fact to get the frames.
