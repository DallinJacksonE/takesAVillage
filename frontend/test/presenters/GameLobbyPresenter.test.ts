// A hypothetical service (Model)
const mockGameService = {
  startGame: jest.fn(),
};

// A hypothetical view interface
interface IGameLobbyView {
  setLoading(isLoading: boolean): void;
  showError(message: string): void;
  navigateToGame(): void;
}

// A hypothetical presenter
class GameLobbyPresenter {
  constructor(
    private view: IGameLobbyView,
    private service: typeof mockGameService,
  ) {}

  async handleStartGame() {
    this.view.setLoading(true);
    try {
      await this.service.startGame();
      this.view.navigateToGame();
    } catch (error) {
      this.view.showError("Failed to start the game.");
    } finally {
      this.view.setLoading(false);
    }
  }
}

describe("GameLobbyPresenter", () => {
  it("should call the service and navigate on successful start", async () => {
    // 1. Arrange
    const mockView: IGameLobbyView = {
      setLoading: jest.fn(),
      showError: jest.fn(),
      navigateToGame: jest.fn(),
    };
    const presenter = new GameLobbyPresenter(mockView, mockGameService);

    // 2. Act
    await presenter.handleStartGame();

    // 3. Assert
    expect(mockView.setLoading).toHaveBeenCalledWith(true);
    expect(mockGameService.startGame).toHaveBeenCalled();
    expect(mockView.navigateToGame).toHaveBeenCalled();
    expect(mockView.setLoading).toHaveBeenCalledWith(false);
    expect(mockView.showError).not.toHaveBeenCalled();
  });
});
