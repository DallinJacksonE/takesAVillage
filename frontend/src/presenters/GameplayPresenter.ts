import {
  GameStateDTO,
  GameActionPayload,
  ResourceBundle,
  Resource,
  BuildDevPayload,
  TargetDevPayload,
  ContestDevPayload,
  DraftTradePayload,
  CounterTradePayload,
  FinalizeTradePayload,
  DraftEmploymentPayload,
  DraftCampfirePayload,
  ContractActionPayload,
  CommitWorkPayload,
  ChatMessageDTO
} from "../dtos";
import { Presenter } from "./Presenter";
import { View } from "./View";
import { GameplayService, ConnectionState } from "../service/GameplayService";

export interface GameplayView extends View {
  setGameState(gameState: GameStateDTO | null): void;
  setPlayerCount(playerCount: number): void;
  setTimeLeft(timeLeft: number): void;
  setUserId(userId: string): void;
  showAlert(message: string): void;
  setConnectionState(state: ConnectionState): void;
  setChatHistory(messages: ChatMessageDTO[]): void;
  addChatMessage(message: ChatMessageDTO): void;
}

export class GameplayPresenter extends Presenter<GameplayView> {
  private gameId: string;
  private userId: string | null = null;
  private timeLeft: number = 0;
  private timer: NodeJS.Timeout | null = null;
  private service: GameplayService; // The injected model/service

  constructor(view: GameplayView, gameId: string) {
    super(view);
    this.gameId = gameId;

    this.service = new GameplayService();

    // 1. Initialize all React state listeners FIRST
    this.init();

    // 2. Connect, and ONLY join the room when the socket confirms it is open
    this.service.connect(() => {
      if (this.userId) {
        this.service.joinRoom(this.gameId, this.userId);
      }
    });
  }

  private init() {
    this.userId = this.getCookie("user_session") || "anon";
    this._view.setUserId(this.userId);

    // --------------------------------------------------------
    // Presenter defines the Callbacks and plugs them into Service
    // --------------------------------------------------------
    this.service.setOnConnectionStateChange((state: ConnectionState) => {
      this._view.setConnectionState(state);

      // Optional safety: If the socket drops, clear the local timer to prevent drift
      if (state === "DISCONNECTED" || state === "RECONNECTING") {
        this.timeLeft = 0;
      }
    });
    this.service.setOnPlayerCount((count: number) => {
      this._view.setPlayerCount(count);
    });

    this.service.setOnGameState((state: GameStateDTO) => {
      this.timeLeft = state.time_remaining;
      this._view.setGameState(state);
      this._view.setTimeLeft(state.time_remaining);
    });

    this.service.setOnChatHistory((msgs) => {
      this._view.setChatHistory(msgs);
    });

    this.service.setOnNewChatMessage((msg) => {
      this._view.addChatMessage(msg);
    });

    this.service.setOnGameStarted(() => {
      this.service.requestUpdate(this.gameId, this.userId!);
    });

    this.service.setOnError((message: string) => {
      this._view.showAlert(message);
    });


    // Manage the local countdown timer
    const timer = setInterval(() => {
      this.timeLeft = this.timeLeft > 0 ? this.timeLeft - 1 : 0;
      this._view.setTimeLeft(this.timeLeft);
    }, 1000);
    this.timer = timer;
  }

  public destroy() {
    if (this.timer) {
      clearInterval(this.timer);
    }
    this.service.destroy(); // Sever the connection cleanly
  }

  private getCookie(name: string): string | undefined {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(";").shift();
  }

  // --------------------------------------------------------
  // Lobby & Social Actions
  // --------------------------------------------------------

  public handleStartGame = () => {
    if (!this.userId) return;
    this.service.startGame(this.gameId, this.userId);
  }

  public sendChat = (content: string, toId: string = "GLOBAL") => {
    if (!this.userId) return;
    this.service.sendChat(this.gameId, this.userId, content, toId);
  }

  // --------------------------------------------------------
  // Core Helper for wrapping payloads
  // --------------------------------------------------------

  private dispatchAction<T>(actionCommand: string, payload: T) {
    if (!this.userId) return;

    const envelopedPayload: GameActionPayload<T> = {
      gameId: this.gameId,
      userId: this.userId,
      action_command: actionCommand,
      payload: payload
    };

    this.service.submitAction(envelopedPayload);
  }

  // --------------------------------------------------------
  // Economy Actions
  // --------------------------------------------------------

  public buildDevelopment = (tileId: string) => {
    this.dispatchAction<BuildDevPayload>("BUILD_DEV", { tile_id: tileId });
  }

  public maintainDevelopment = (devId: string) => {
    this.dispatchAction<TargetDevPayload>("MAINTAIN_DEV", { dev_id: devId });
  }

  public upgradeDevelopment = (devId: string) => {
    this.dispatchAction<TargetDevPayload>("UPGRADE_DEV", { dev_id: devId });
  }

  // --------------------------------------------------------
  // Conflict Actions
  // --------------------------------------------------------

  public contestDevelopment = (devId: string, side?: "INITIATOR" | "CONTESTER" | "OWNER") => {
    this.dispatchAction<ContestDevPayload>("CONTEST_DEV", {
      dev_id: devId,
      side: side
    });
  }

  // --------------------------------------------------------
  // Trade Drafting & Negotiation
  // --------------------------------------------------------

  public draftTrade = (targetId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => {
    this.dispatchAction<DraftTradePayload>("TRADE", {
      target_id: targetId,
      offer_items: offerItems,
      request_items: requestItems,
      type: "TRADE"
    });
  }

  public counterTrade = (actionId: string, offerItems: Partial<ResourceBundle>, requestItems: Partial<ResourceBundle>) => {
    this.dispatchAction<CounterTradePayload>("BARTER", {
      action_id: actionId,
      offer_items: offerItems,
      request_items: requestItems
    });
  }

  public finalizeTrade = (actionId: string, actualItems: Partial<ResourceBundle>) => {
    this.dispatchAction<FinalizeTradePayload>("FINALIZE", {
      action_id: actionId,
      actual_items: actualItems
    });
  }

  // --------------------------------------------------------
  // Employment & Campfire Drafting
  // --------------------------------------------------------

  public draftEmployment = (targetId: string, devId: string, wage: number, wageType: Resource, isApplication: boolean) => {
    this.dispatchAction<DraftEmploymentPayload>("EMPLOYMENT", {
      target_id: targetId,
      dev_id: devId,
      wage: wage,
      wage_type: wageType,
      is_application: isApplication,
      type: "EMPLOYMENT"
    });
  }

  public startFire = () => {
    this.dispatchAction<{}>("START_FIRE", {});
  }

  public draftCampfire = (targetId: string, isRequest: boolean) => {
    this.dispatchAction<DraftCampfirePayload>("CAMPFIRE", {
      target_id: targetId,
      is_request: isRequest,
      type: "CAMPFIRE"
    });
  }

  public createChat = (
    name: string,
    memberIds: string[]
  ) => {
    if (!this.userId) return;

    this.service.createChat(
      this.gameId,
      this.userId,
      name,
      memberIds
    );
  }

  // --------------------------------------------------------
  // Universal Contract Responses (Accept/Deny/Cancel)
  // --------------------------------------------------------

  public acceptContract = (actionId: string, type?: string) => {
    this.dispatchAction<ContractActionPayload>("ACCEPT", { action_id: actionId, type: type });
  }

  public denyContract = (actionId: string, type?: string) => {
    this.dispatchAction<ContractActionPayload>("DENY", { action_id: actionId, type: type });
  }

  public cancelContract = (actionId: string, type?: string) => {
    this.dispatchAction<ContractActionPayload>("CANCEL", { action_id: actionId, type: type });
  }

  // --------------------------------------------------------
  // Phase Management
  // --------------------------------------------------------

  public commitWork = (payload: CommitWorkPayload) => {
    this.dispatchAction<CommitWorkPayload>("COMMIT_WORK", payload);
  }

  public finishPhase = () => {
    this.dispatchAction<{}>("FINISH_PHASE", {});
  }
}
